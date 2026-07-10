"""
ASGService — App State Graph builder, planner, synthesizer, and confidence gates.

Feature 3: Deterministic test generation from crawl artifacts and flow_steps.
"""
from __future__ import annotations

import hashlib
import json
import logging
import time
import uuid
from collections import defaultdict, deque
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse

from sqlalchemy.orm import Session

from app.core.config import settings
from app.crud import asg as asg_crud
from app.models.asg import ASGGraph, ASGGraphStatus, ASGNode, ASGEdge, ASGPath
from app.schemas.asg import (
    ASGBuildRequest,
    ASGBuildResponse,
    ASGBuildStats,
    ASGConfidenceSummary,
    ASGGraphDetailResponse,
    ASGPlanGoal,
    ASGPlanResponse,
    ASGPlannedPath,
    ASGSynthesizeRequest,
    ASGSynthesizeResponse,
    ASGSynthesizedDraftTest,
    ASGValidateResponse,
)

logger = logging.getLogger(__name__)

_ARTIFACTS_ROOT = Path(__file__).resolve().parent.parent.parent / "artifacts" / "asg"


def _stable_hash(payload: Dict[str, Any]) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def compute_state_fingerprint(
    *,
    url: str,
    title: str,
    landmarks: List[str],
    ui_traits: Dict[str, Any],
) -> str:
    """Deterministic state fingerprint from DOM landmarks, URL, and UI traits."""
    normalized_url = (url or "").split("#")[0].rstrip("/")
    payload = {
        "url": normalized_url,
        "title": (title or "").strip().lower()[:200],
        "landmarks": sorted({lm.strip().lower() for lm in landmarks if lm}),
        "ui_traits": {
            k: ui_traits[k]
            for k in sorted(ui_traits.keys())
            if ui_traits[k] is not None
        },
    }
    return _stable_hash(payload)


def extract_landmarks_from_flow_step(step: Dict[str, Any]) -> List[str]:
    landmarks: List[str] = []
    target = (step.get("target") or "").strip()
    if target:
        landmarks.append(target)
    locator = step.get("locator") or {}
    if isinstance(locator, dict):
        for key in ("css", "xpath", "role", "text"):
            val = locator.get(key)
            if val:
                landmarks.append(str(val))
    page_title = (step.get("page_title") or "").strip()
    if page_title:
        landmarks.append(f"title:{page_title}")
    return landmarks


def normalize_transition(flow_step: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize a crawl action into a deterministic transition payload."""
    action = (flow_step.get("action") or "unknown").lower()
    target = (flow_step.get("target") or "").strip()
    return {
        "action_type": action,
        "target": target,
        "page_url": flow_step.get("page_url") or "",
        "element_type": flow_step.get("element_type") or "",
        "input_type": flow_step.get("input_type") or "",
        "locator": flow_step.get("locator") or {},
        "order": flow_step.get("order"),
        "extracted_content": flow_step.get("extracted_content") or "",
    }


def compute_edge_deterministic_key(
    from_fingerprint: str,
    to_fingerprint: str,
    transition: Dict[str, Any],
    seed_hash: str,
) -> str:
    payload = {
        "from": from_fingerprint,
        "to": to_fingerprint,
        "action_type": transition.get("action_type"),
        "target": transition.get("target"),
        "order": transition.get("order"),
        "seed_hash": seed_hash,
    }
    return _stable_hash(payload)[:32]


def score_selector_stability(transition: Dict[str, Any]) -> float:
    locator = transition.get("locator") or {}
    if not isinstance(locator, dict):
        return 0.4
    if locator.get("xpath"):
        return 0.55
    if locator.get("css"):
        return 0.75
    if locator.get("role") and locator.get("text"):
        return 0.85
    target = (transition.get("target") or "").strip()
    if target and target.lower() not in ("div", "span", "input", "button"):
        return 0.7
    return 0.45


def score_readiness_signal(readiness_snapshot: Optional[Dict[str, Any]]) -> float:
    if not readiness_snapshot:
        return 0.6
    if readiness_snapshot.get("settled") is True:
        return 0.9
    if readiness_snapshot.get("loading_cleared") is True:
        return 0.8
    if readiness_snapshot.get("modal_dismissed"):
        return 0.75
    return 0.55


def score_action_reproducibility(transition: Dict[str, Any]) -> float:
    action = (transition.get("action_type") or "").lower()
    if action == "navigate":
        return 0.95
    if action == "click" and transition.get("target"):
        return 0.8
    if action == "input":
        return 0.7
    return 0.5


def compute_transition_confidence(
    transition: Dict[str, Any],
    readiness_snapshot: Optional[Dict[str, Any]] = None,
) -> float:
    scores = [
        score_selector_stability(transition),
        score_readiness_signal(readiness_snapshot),
        score_action_reproducibility(transition),
    ]
    return round(sum(scores) / len(scores), 4)


def compute_node_confidence(landmarks: List[str], edge_confidences: List[float]) -> float:
    base = 0.65 if landmarks else 0.45
    if edge_confidences:
        return round(min(1.0, (base + sum(edge_confidences) / len(edge_confidences)) / 2), 4)
    return base


class ASGPolicyEngine:
    """Enforce exploration bounds during graph build."""

    def __init__(self, policy: Dict[str, Any]):
        self.max_nodes = int(policy.get("max_nodes", 150))
        self.max_depth = int(policy.get("max_depth", 20))
        self.max_branching = int(policy.get("max_branching", 8))
        self.domain_allowlist = [d.lower() for d in policy.get("domain_allowlist") or []]
        self.forbidden_actions = {
            a.lower() for a in policy.get("forbidden_actions") or []
        }
        self.hits: List[str] = []

    def is_url_allowed(self, url: str) -> bool:
        if not self.domain_allowlist:
            return True
        host = (urlparse(url).hostname or "").lower()
        allowed = any(host == d or host.endswith(f".{d}") for d in self.domain_allowlist)
        if not allowed:
            self.hits.append(f"domain_blocked:{host}")
        return allowed

    def is_action_allowed(self, action_type: str) -> bool:
        if action_type.lower() in self.forbidden_actions:
            self.hits.append(f"forbidden_action:{action_type}")
            return False
        return True

    def can_add_node(self, current_count: int) -> bool:
        if current_count >= self.max_nodes:
            self.hits.append("max_nodes_reached")
            return False
        return True

    def can_add_branch(self, from_node_id: int, branch_count: int) -> bool:
        if branch_count >= self.max_branching:
            self.hits.append(f"max_branching_reached:node_{from_node_id}")
            return False
        return True

    def can_go_deeper(self, depth: int) -> bool:
        if depth >= self.max_depth:
            self.hits.append("max_depth_reached")
            return False
        return True


class ASGService:
    """Domain service for ASG build, plan, synthesize, and validate."""

    def __init__(self, artifacts_root: Optional[Path] = None):
        self.artifacts_root = artifacts_root or _ARTIFACTS_ROOT

    @property
    def confidence_min(self) -> float:
        return float(getattr(settings, "ASG_CONFIDENCE_MIN", 0.75))

    def _graph_dir(self, graph_id: int) -> Path:
        return self.artifacts_root / str(graph_id)

    def _write_json(self, path: Path, payload: Dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")

    def build_seed_hash(
        self,
        target_url: str,
        seed_intents: List[str],
        flow_steps: List[Dict[str, Any]],
        policy: Dict[str, Any],
        explicit_seed: Optional[str] = None,
    ) -> str:
        if explicit_seed:
            return explicit_seed
        payload = {
            "url": str(target_url),
            "intents": sorted(seed_intents),
            "step_count": len(flow_steps),
            "policy": policy,
        }
        return _stable_hash(payload)[:16]

    def build_graph(
        self,
        db: Session,
        request: ASGBuildRequest,
        *,
        created_by: Optional[int] = None,
    ) -> ASGBuildResponse:
        started = time.perf_counter()
        policy_dict = request.policy.model_dump()
        seed_hash = self.build_seed_hash(
            str(request.target_url),
            request.seed_intents,
            request.flow_steps,
            policy_dict,
            request.seed_hash,
        )
        policy = ASGPolicyEngine(policy_dict)

        graph = asg_crud.create_graph(
            db,
            created_by=created_by,
            project_id=request.project_id,
            policy_json=policy_dict,
            seed_hash=seed_hash,
            status=ASGGraphStatus.BUILDING.value,
        )

        flow_steps = list(request.flow_steps or [])
        if not flow_steps:
            flow_steps = [{"action": "navigate", "target": str(request.target_url), "page_url": str(request.target_url)}]

        readiness_by_order: Dict[int, Dict[str, Any]] = {}
        for snap in request.readiness_snapshots or []:
            order = snap.get("order")
            if order is not None:
                readiness_by_order[int(order)] = snap

        node_by_fp: Dict[str, ASGNode] = {}
        branch_counts: Dict[int, int] = defaultdict(int)
        depth_by_fp: Dict[str, int] = {}
        edge_confidence_by_fp: Dict[str, List[float]] = defaultdict(list)

        initial_fp = compute_state_fingerprint(
            url=str(request.target_url),
            title=request.page_context.get("title", ""),
            landmarks=[str(request.target_url)],
            ui_traits={"entry": True},
        )
        if policy.can_add_node(len(node_by_fp)):
            root = asg_crud.create_node(
                db,
                graph_id=graph.id,
                state_fingerprint=initial_fp,
                url=str(request.target_url),
                title=request.page_context.get("title", ""),
                state_payload_json={"landmarks": [str(request.target_url)], "entry": True},
                confidence=0.9,
                is_terminal=len(flow_steps) == 0,
            )
            node_by_fp[initial_fp] = root
            depth_by_fp[initial_fp] = 0

        prev_fp = initial_fp
        prev_node = node_by_fp.get(initial_fp)

        for idx, raw_step in enumerate(flow_steps):
            transition = normalize_transition(raw_step)
            action_type = transition["action_type"]

            if not policy.is_action_allowed(action_type):
                continue

            page_url = transition.get("page_url") or str(request.target_url)
            if not policy.is_url_allowed(page_url):
                continue

            landmarks = extract_landmarks_from_flow_step(raw_step)
            page_title = raw_step.get("page_title") or request.page_context.get("title", "")
            ui_traits = {
                "element_type": transition.get("element_type"),
                "input_type": transition.get("input_type"),
            }
            state_fp = compute_state_fingerprint(
                url=page_url,
                title=page_title,
                landmarks=landmarks,
                ui_traits=ui_traits,
            )

            parent_depth = depth_by_fp.get(prev_fp, 0)
            if state_fp not in node_by_fp:
                if not policy.can_add_node(len(node_by_fp)):
                    break
                if not policy.can_go_deeper(parent_depth + 1):
                    break
                node = asg_crud.create_node(
                    db,
                    graph_id=graph.id,
                    state_fingerprint=state_fp,
                    url=page_url,
                    title=page_title,
                    state_payload_json={"landmarks": landmarks, "ui_traits": ui_traits},
                    confidence=0.0,
                    is_terminal=idx == len(flow_steps) - 1,
                )
                node_by_fp[state_fp] = node
                depth_by_fp[state_fp] = parent_depth + 1
            else:
                node = node_by_fp[state_fp]
                if idx == len(flow_steps) - 1:
                    node.is_terminal = True

            if prev_node is None:
                prev_fp = state_fp
                prev_node = node_by_fp[state_fp]
                continue

            if not policy.can_add_branch(prev_node.id, branch_counts[prev_node.id]):
                prev_fp = state_fp
                prev_node = node_by_fp[state_fp]
                continue

            order = raw_step.get("order", idx + 1)
            readiness = readiness_by_order.get(int(order))
            edge_conf = compute_transition_confidence(transition, readiness)
            det_key = compute_edge_deterministic_key(prev_fp, state_fp, transition, seed_hash)

            if not asg_crud.get_edge_by_key(db, graph.id, det_key):
                asg_crud.create_edge(
                    db,
                    graph_id=graph.id,
                    from_node_id=prev_node.id,
                    to_node_id=node_by_fp[state_fp].id,
                    action_type=action_type,
                    action_payload_json=transition,
                    readiness_snapshot_json=readiness,
                    confidence=edge_conf,
                    deterministic_key=det_key,
                )
                branch_counts[prev_node.id] += 1

            edge_confidence_by_fp[state_fp].append(edge_conf)
            prev_fp = state_fp
            prev_node = node_by_fp[state_fp]

        for fp, node in node_by_fp.items():
            node.confidence = compute_node_confidence(
                node.state_payload_json.get("landmarks", []),
                edge_confidence_by_fp.get(fp, []),
            )

        db.commit()

        nodes = asg_crud.list_nodes(db, graph.id)
        edges = asg_crud.list_edges(db, graph.id)
        confidences = [n.confidence for n in nodes] + [e.confidence for e in edges]
        mean_conf = sum(confidences) / len(confidences) if confidences else 0.0
        below = sum(1 for c in confidences if c < self.confidence_min)

        asg_crud.update_graph_status(
            db, graph, status=ASGGraphStatus.READY.value, confidence_score=mean_conf
        )

        duration_ms = int((time.perf_counter() - started) * 1000)
        stats = ASGBuildStats(
            node_count=len(nodes),
            edge_count=len(edges),
            terminal_nodes=sum(1 for n in nodes if n.is_terminal),
            policy_hits=list(dict.fromkeys(policy.hits)),
            build_duration_ms=duration_ms,
        )
        confidence = ASGConfidenceSummary(
            mean=round(mean_conf, 4),
            min=round(min(confidences), 4) if confidences else 0.0,
            max=round(max(confidences), 4) if confidences else 0.0,
            below_threshold_count=below,
            threshold=self.confidence_min,
        )

        graph_payload = {
            "graph_id": graph.id,
            "seed_hash": seed_hash,
            "policy": policy_dict,
            "nodes": [
                {
                    "id": n.id,
                    "state_fingerprint": n.state_fingerprint,
                    "url": n.url,
                    "title": n.title,
                    "confidence": n.confidence,
                    "is_terminal": n.is_terminal,
                }
                for n in nodes
            ],
            "edges": [
                {
                    "id": e.id,
                    "from_node_id": e.from_node_id,
                    "to_node_id": e.to_node_id,
                    "action_type": e.action_type,
                    "deterministic_key": e.deterministic_key,
                    "confidence": e.confidence,
                }
                for e in edges
            ],
        }
        gdir = self._graph_dir(graph.id)
        self._write_json(gdir / "build" / "graph.json", graph_payload)
        self._write_json(
            gdir / "build" / "confidence-report.json",
            {"confidence": confidence.model_dump(), "stats": stats.model_dump()},
        )

        return ASGBuildResponse(
            graph_id=graph.id,
            status=ASGGraphStatus.READY.value,
            seed_hash=seed_hash,
            stats=stats,
            confidence=confidence,
        )

    def get_graph_detail(self, db: Session, graph_id: int) -> ASGGraphDetailResponse:
        graph = asg_crud.get_graph(db, graph_id)
        if not graph:
            raise ValueError(f"Graph {graph_id} not found")

        nodes = asg_crud.list_nodes(db, graph_id)
        edges = asg_crud.list_edges(db, graph_id)
        all_conf = [n.confidence for n in nodes] + [e.confidence for e in edges]

        def _bucket(c: float) -> str:
            if c >= 0.9:
                return "high"
            if c >= 0.75:
                return "medium"
            return "low"

        dist: Dict[str, float] = {"high": 0.0, "medium": 0.0, "low": 0.0}
        for c in all_conf:
            dist[_bucket(c)] += 1
        total = len(all_conf) or 1
        dist = {k: round(v / total, 4) for k, v in dist.items()}

        return ASGGraphDetailResponse(
            graph_id=graph.id,
            project_id=graph.project_id,
            status=graph.status,
            seed_hash=graph.seed_hash,
            confidence_score=graph.confidence_score,
            node_count=len(nodes),
            edge_count=len(edges),
            confidence_distribution=dist,
            created_at=graph.created_at.isoformat() if graph.created_at else "",
            updated_at=graph.updated_at.isoformat() if graph.updated_at else "",
        )

    def plan_paths(self, db: Session, graph_id: int, goal: ASGPlanGoal) -> ASGPlanResponse:
        graph = asg_crud.get_graph(db, graph_id)
        if not graph:
            raise ValueError(f"Graph {graph_id} not found")

        nodes = asg_crud.list_nodes(db, graph_id)
        edges = asg_crud.list_edges(db, graph_id)
        if not nodes:
            raise ValueError("Graph has no nodes")

        fp_by_id = {n.id: n.state_fingerprint for n in nodes}
        id_by_fp = {n.state_fingerprint: n.id for n in nodes}
        adj: Dict[int, List[ASGEdge]] = defaultdict(list)
        for e in edges:
            adj[e.from_node_id].append(e)

        root = nodes[0]
        for n in nodes:
            if n.state_payload_json.get("entry"):
                root = n
                break

        planned: List[ASGPlannedPath] = []
        plan_id = str(uuid.uuid4())

        if goal.mode == "shortest_path":
            target_fp = goal.target_node_fingerprint
            target_id = id_by_fp.get(target_fp) if target_fp else None
            if target_id is None:
                terminals = [n for n in nodes if n.is_terminal]
                target_id = terminals[-1].id if terminals else nodes[-1].id

            path_node_ids = self._shortest_path(root.id, target_id, adj)
            if path_node_ids:
                path_edges = self._edges_along_path(path_node_ids, adj)
                score = self._path_score(path_edges)
                path = asg_crud.create_path(
                    db,
                    graph_id=graph_id,
                    goal_type=goal.mode,
                    path_nodes_json=[fp_by_id[nid] for nid in path_node_ids],
                    path_edges_json=[e.deterministic_key for e in path_edges],
                    score=score,
                    risk_score=1.0 - score,
                )
                planned.append(
                    ASGPlannedPath(
                        path_id=path.id,
                        goal_type=goal.mode,
                        node_fingerprints=path.path_nodes_json,
                        edge_keys=path.path_edges_json,
                        score=path.score,
                        risk_score=path.risk_score,
                        confidence=score,
                        rationale="Shortest confidence-weighted path to terminal state",
                    )
                )

        elif goal.mode == "requirement_coverage":
            req_targets = goal.requirement_ids or ["default"]
            seen_fps: set[str] = set()
            for req_id in req_targets[: goal.max_paths]:
                target = next(
                    (n for n in nodes if req_id.lower() in (n.title or "").lower() or req_id in n.state_fingerprint),
                    nodes[-1],
                )
                path_node_ids = self._shortest_path(root.id, target.id, adj)
                fps = tuple(fp_by_id[nid] for nid in path_node_ids)
                if fps in seen_fps or not path_node_ids:
                    continue
                seen_fps.add(fps)
                path_edges = self._edges_along_path(path_node_ids, adj)
                score = self._path_score(path_edges) * (1.0 if req_id in goal.requirement_ids else 0.85)
                path = asg_crud.create_path(
                    db,
                    graph_id=graph_id,
                    goal_type=goal.mode,
                    path_nodes_json=list(fps),
                    path_edges_json=[e.deterministic_key for e in path_edges],
                    score=score,
                    risk_score=1.0 - score,
                )
                planned.append(
                    ASGPlannedPath(
                        path_id=path.id,
                        goal_type=goal.mode,
                        node_fingerprints=path.path_nodes_json,
                        edge_keys=path.path_edges_json,
                        score=path.score,
                        risk_score=path.risk_score,
                        confidence=score,
                        rationale=f"Requirement coverage path for '{req_id}'",
                    )
                )

        else:  # risk_first
            ranked_edges = sorted(edges, key=lambda e: e.confidence)
            risky = ranked_edges[: min(goal.max_paths, len(ranked_edges))]
            for e in risky:
                path = asg_crud.create_path(
                    db,
                    graph_id=graph_id,
                    goal_type=goal.mode,
                    path_nodes_json=[fp_by_id[e.from_node_id], fp_by_id[e.to_node_id]],
                    path_edges_json=[e.deterministic_key],
                    score=e.confidence,
                    risk_score=1.0 - e.confidence,
                )
                planned.append(
                    ASGPlannedPath(
                        path_id=path.id,
                        goal_type=goal.mode,
                        node_fingerprints=path.path_nodes_json,
                        edge_keys=path.path_edges_json,
                        score=path.score,
                        risk_score=path.risk_score,
                        confidence=e.confidence,
                        rationale="Risk-first single-edge probe",
                    )
                )

        planned.sort(key=lambda p: p.score, reverse=True)
        planned = planned[: goal.max_paths]

        self._write_json(
            self._graph_dir(graph_id) / "plan" / f"{plan_id}.json",
            {"plan_id": plan_id, "goal": goal.model_dump(), "paths": [p.model_dump() for p in planned]},
        )

        return ASGPlanResponse(graph_id=graph_id, plan_id=plan_id, paths=planned)

    def _shortest_path(
        self, start_id: int, target_id: int, adj: Dict[int, List[ASGEdge]]
    ) -> List[int]:
        if start_id == target_id:
            return [start_id]
        queue: deque[List[int]] = deque([[start_id]])
        visited = {start_id}
        while queue:
            path = queue.popleft()
            node_id = path[-1]
            for edge in sorted(adj.get(node_id, []), key=lambda e: -e.confidence):
                nxt = edge.to_node_id
                if nxt in visited:
                    continue
                new_path = path + [nxt]
                if nxt == target_id:
                    return new_path
                visited.add(nxt)
                queue.append(new_path)
        return [start_id]

    def _edges_along_path(
        self, node_ids: List[int], adj: Dict[int, List[ASGEdge]]
    ) -> List[ASGEdge]:
        result: List[ASGEdge] = []
        for i in range(len(node_ids) - 1):
            frm, to = node_ids[i], node_ids[i + 1]
            candidates = [e for e in adj.get(frm, []) if e.to_node_id == to]
            if candidates:
                result.append(max(candidates, key=lambda e: e.confidence))
        return result

    def _path_score(self, edges: List[ASGEdge]) -> float:
        if not edges:
            return 0.5
        return round(sum(e.confidence for e in edges) / len(edges), 4)

    def synthesize_tests(
        self,
        db: Session,
        graph_id: int,
        request: ASGSynthesizeRequest,
        *,
        user_id: Optional[int] = None,
    ) -> ASGSynthesizeResponse:
        graph = asg_crud.get_graph(db, graph_id)
        if not graph:
            raise ValueError(f"Graph {graph_id} not found")

        asg_crud.mark_paths_selected(db, graph_id, request.path_ids)
        synthesis_id = str(uuid.uuid4())
        drafts: List[ASGSynthesizedDraftTest] = []

        from app.api.v2.endpoints.crawl_and_save import _flow_steps_to_test_steps
        from app.schemas.test_case import TestCaseCreate
        from app.crud.test_case import create_test_case
        from app.models.test_case import TestType, Priority, TestStatus

        edges = {e.deterministic_key: e for e in asg_crud.list_edges(db, graph_id)}

        for path_id in request.path_ids:
            path = asg_crud.get_path(db, graph_id, path_id)
            if not path:
                continue

            flow_steps: List[Dict[str, Any]] = []
            for edge_key in path.path_edges_json:
                edge = edges.get(edge_key)
                if not edge:
                    continue
                payload = dict(edge.action_payload_json or {})
                payload.setdefault("action", edge.action_type)
                flow_steps.append(payload)

            steps = _flow_steps_to_test_steps(flow_steps, request.login_credentials)
            if not steps and flow_steps:
                steps = [f"Step {i + 1}: {fs.get('action', 'action')} '{fs.get('target', '')}'" for i, fs in enumerate(flow_steps)]

            manifest = {
                "graph_id": graph_id,
                "path_id": path_id,
                "edge_keys": path.path_edges_json,
                "node_fingerprints": path.path_nodes_json,
                "synthesis_profile": request.synthesis_profile,
                "strategy": "asg",
            }
            validation_score = path.score

            test_case_id = None
            if request.save_test_cases and user_id is not None:
                tc = TestCaseCreate(
                    title=f"{request.test_title_prefix} — path {path_id}",
                    description=f"ASG synthesized test from graph {graph_id}",
                    test_type=TestType.E2E,
                    priority=Priority.MEDIUM,
                    status=TestStatus.PENDING,
                    steps=steps,
                    expected_result="Flow completes successfully",
                    test_metadata=manifest,
                )
                saved = create_test_case(db, tc, user_id)
                test_case_id = saved.id

            record = asg_crud.create_synthesized_test(
                db,
                graph_id=graph_id,
                path_id=path_id,
                steps_json=steps,
                synthesis_manifest_json=manifest,
                validation_score=validation_score,
                test_case_id=test_case_id,
            )

            drafts.append(
                ASGSynthesizedDraftTest(
                    synthesis_id=record.id,
                    path_id=path_id,
                    steps=steps,
                    provenance=manifest,
                    validation_score=validation_score,
                    test_case_id=test_case_id,
                )
            )

        self._write_json(
            self._graph_dir(graph_id) / "synthesis" / f"{synthesis_id}.json",
            {"synthesis_id": synthesis_id, "tests": [d.model_dump() for d in drafts]},
        )

        return ASGSynthesizeResponse(graph_id=graph_id, synthesis_id=synthesis_id, tests=drafts)

    def write_replay_artifact(
        self,
        *,
        graph_id: int,
        execution_id: int,
        plan_id: Optional[str] = None,
        synthesis_id: Optional[str] = None,
        extra: Optional[Dict[str, Any]] = None,
    ) -> Path:
        """Persist replay trace bundle linking graph, plan, synthesis, and execution IDs."""
        payload: Dict[str, Any] = {
            "graph_id": graph_id,
            "plan_id": plan_id,
            "synthesis_id": synthesis_id,
            "execution_id": execution_id,
        }
        if extra:
            payload.update(extra)
        artifact_path = self._graph_dir(graph_id) / "replay" / f"{execution_id}.json"
        self._write_json(artifact_path, payload)
        logger.info(
            "ASG replay artifact graph_id=%s plan_id=%s synthesis_id=%s execution_id=%s",
            graph_id,
            plan_id,
            synthesis_id,
            execution_id,
        )
        return artifact_path

    def validate_graph(self, db: Session, graph_id: int) -> ASGValidateResponse:
        graph = asg_crud.get_graph(db, graph_id)
        if not graph:
            raise ValueError(f"Graph {graph_id} not found")

        nodes = asg_crud.list_nodes(db, graph_id)
        edges = asg_crud.list_edges(db, graph_id)
        node_mean = sum(n.confidence for n in nodes) / len(nodes) if nodes else 0.0
        edge_mean = sum(e.confidence for e in edges) / len(edges) if edges else 0.0
        replay_conf = round((node_mean + edge_mean) / 2, 4) if (nodes or edges) else 0.0

        fallback = replay_conf < self.confidence_min
        reason = None
        if fallback:
            if node_mean < self.confidence_min:
                reason = "low_node_confidence"
            elif edge_mean < self.confidence_min:
                reason = "low_edge_confidence"
            else:
                reason = "low_replay_confidence"

        return ASGValidateResponse(
            graph_id=graph_id,
            replay_confidence=replay_conf,
            node_confidence_mean=round(node_mean, 4),
            edge_confidence_mean=round(edge_mean, 4),
            fallback_recommended=fallback,
            fallback_reason_code=reason,
            threshold=self.confidence_min,
        )

    def evaluate_confidence_gate(self, db: Session, graph_id: int) -> Tuple[bool, Optional[str]]:
        """Return (passes_gate, fallback_reason_code)."""
        result = self.validate_graph(db, graph_id)
        if result.fallback_recommended:
            return False, result.fallback_reason_code
        return True, None


def get_asg_service() -> ASGService:
    return ASGService()


def is_asg_enabled_for_project(project_id: Optional[int] = None) -> bool:
    if not getattr(settings, "ASG_ENABLED", False) and not getattr(settings, "ASG_SHADOW_MODE", True):
        return False
    allowlist = getattr(settings, "ASG_PROJECT_ALLOWLIST", None)
    if allowlist:
        allowed = {p.strip() for p in str(allowlist).split(",") if p.strip()}
        if project_id is not None and str(project_id) not in allowed:
            return False
    return True


def should_use_asg_primary(project_id: Optional[int] = None) -> bool:
    return bool(getattr(settings, "ASG_ENABLED", False)) and is_asg_enabled_for_project(project_id)


def trigger_shadow_build(
    db: Session,
    *,
    target_url: str,
    flow_steps: List[Dict[str, Any]],
    created_by: Optional[int] = None,
    project_id: Optional[int] = None,
    seed_intents: Optional[List[str]] = None,
    page_context: Optional[Dict[str, Any]] = None,
) -> Optional[int]:
    """Build ASG graph in shadow mode; returns graph_id or None on skip/failure."""
    if not is_asg_enabled_for_project(project_id):
        return None
    try:
        service = ASGService()
        req = ASGBuildRequest(
            target_url=target_url,
            seed_intents=seed_intents or [],
            flow_steps=flow_steps,
            project_id=project_id,
            page_context=page_context or {},
        )
        resp = service.build_graph(db, req, created_by=created_by)
        logger.info(
            "ASG shadow build complete graph_id=%s nodes=%s edges=%s confidence=%.3f",
            resp.graph_id,
            resp.stats.node_count,
            resp.stats.edge_count,
            resp.confidence.mean,
        )
        return resp.graph_id
    except Exception as exc:
        logger.warning("ASG shadow build failed: %s", exc)
        return None
