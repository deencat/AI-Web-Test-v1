"""
Persist Playwright-oriented flow recordings to disk after ObservationAgent completes.

Writes under ``backend/artifacts/flow_recordings/{YYYYMMDDTHHMMSSZ}_{short_workflow}/`` (gitignored via ``backend/artifacts/``):
  - ``playwright_flow_recording.json`` — schema v1 wrapper (steps + locators)
  - ``flow_steps.json`` — same steps array alone (easy diff / tooling)
  - ``playwright_step_ir.json`` — deterministic step IR (suggestions/xpath/attrs) for non-LLM codegen
  - ``requirements/requirements_result.json`` — full RequirementsAgent output (scenarios, coverage, etc.) after POST ``/requirements`` or generate-tests stage 2, when the run has on-disk flow artifacts
  - ``by_test_case/test_case_{id}.json`` — per generated DB test case manifest pointing at the files above

Paths are attached to ``obs_data["flow_recording_artifacts"]`` for API / workflow results.
"""
from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


def _backend_root() -> Path:
    """Directory containing ``app/`` (e.g. .../backend)."""
    return Path(__file__).resolve().parent.parent.parent


def flow_recording_directory_name(workflow_id: str, *, at: Optional[datetime] = None) -> str:
    """
    Build a folder name that sorts chronologically by name (oldest → newest in A→Z sort).

    Pattern: ``{UTC timestamp}Z_{short_token}`` e.g. ``20260326T113015Z_613bbc29``.
    For standard UUID ``workflow_id`` values, ``short_token`` is the first 8 hex chars (before the first hyphen).
    Otherwise: alphanumeric slug of ``workflow_id``, capped at 12 characters.
    """
    if at is None:
        at = datetime.now(timezone.utc)
    elif at.tzinfo is None:
        at = at.replace(tzinfo=timezone.utc)
    else:
        at = at.astimezone(timezone.utc)
    ts = at.strftime("%Y%m%dT%H%M%SZ")
    wid = workflow_id.strip()
    head = wid.split("-", 1)[0] if wid else ""
    if len(head) == 8 and head.isalnum():
        token = head.lower()
    else:
        slug = "".join(c for c in workflow_id if c.isalnum())
        token = (slug or "wf")[:12].lower()
    return f"{ts}_{token}"


def resolve_flow_recording_directory(user_path: str) -> Path:
    """
    Resolve ``user_path`` to an existing directory under ``flow_recordings_base_dir()``.

    Accepts a folder name (e.g. ``613bbc29-4bde-493d-bbcc-fa874fcaf69c`` or
    ``20260326T032703Z_613bbc29``) or a relative path under the base, or an absolute path
    that still lies under the base (symlink-safe compare).

    Raises ``ValueError`` if the path escapes the recordings root or is not a directory.
    """
    base = flow_recordings_base_dir().resolve()
    raw = (user_path or "").strip()
    if not raw:
        raise ValueError("flow_recording_path is empty")
    candidate = Path(raw).expanduser()
    if not candidate.is_absolute():
        target = (base / candidate).resolve()
    else:
        target = candidate.resolve()
    try:
        target.relative_to(base)
    except ValueError as e:
        raise ValueError(
            f"flow_recording_path must be under the flow recordings root ({base}); got {target}"
        ) from e
    if not target.is_dir():
        raise ValueError(f"flow_recording_path is not a directory: {target}")
    return target


def observation_result_from_flow_recording_dir(rec_dir: Path) -> Dict[str, Any]:
    """
    Build a minimal ``observation_result`` dict from saved ``playwright_flow_recording.json``
    and/or ``flow_steps.json`` so RequirementsAgent and downstream agents can run without
    re-executing ObservationAgent.

    Preserves ``flow_steps``, ``playwright_flow_recording``, ``page_context.goal_reached``,
    synthesized ``ui_elements`` from steps for RequirementsAgent grouping, and ``pages`` /
    ``navigation_flow`` derived from step URLs.
    """
    main = rec_dir / "playwright_flow_recording.json"
    steps_only = rec_dir / "flow_steps.json"
    recording: Dict[str, Any]
    steps: List[Dict[str, Any]]

    if main.is_file():
        recording = json.loads(main.read_text(encoding="utf-8"))
        steps = list(recording.get("steps") or [])
        start_url = str(recording.get("start_url") or "").strip()
        goal_reached = bool(recording.get("goal_reached", False))
    elif steps_only.is_file():
        raw = json.loads(steps_only.read_text(encoding="utf-8"))
        if not isinstance(raw, list):
            raise ValueError(f"{steps_only} must contain a JSON array of steps")
        steps = raw
        recording = {
            "schema_version": 1,
            "source": "browser-use-observation",
            "start_url": "",
            "goal_reached": False,
            "steps": steps,
        }
        start_url = ""
        for s in steps:
            if (s.get("action") or "").lower() == "navigate" and s.get("target"):
                start_url = str(s.get("target", "")).strip()
                break
        if not start_url and steps:
            start_url = str(steps[0].get("page_url") or "").strip()
        recording["start_url"] = start_url
        goal_reached = False
    else:
        raise ValueError(
            f"Folder has neither playwright_flow_recording.json nor flow_steps.json: {rec_dir}"
        )

    if not steps:
        raise ValueError(f"No flow steps found under {rec_dir}")

    page_urls: List[str] = []
    seen: set[str] = set()
    for s in steps:
        u = str(s.get("page_url") or "").strip()
        if u and u not in seen:
            seen.add(u)
            page_urls.append(u)

    pages: List[Dict[str, Any]] = []
    for u in page_urls:
        pages.append({"url": u, "title": "", "elements": [], "forms": [], "load_time_ms": 0, "status_code": 200})

    navigation_flow = {
        "start_url": start_url or (page_urls[0] if page_urls else ""),
        "goal_reached": goal_reached,
        "pages_visited": list(page_urls),
        "flow_path": [],
    }

    page_context: Dict[str, Any] = {
        "url": start_url or (page_urls[0] if page_urls else ""),
        "goal_reached": goal_reached,
        "flow_recording_artifacts": {
            "workflow_id": f"replay:{rec_dir.name}",
            "directory_name": rec_dir.name,
            "directory": str(rec_dir.resolve()),
            "playwright_flow_recording_file": str(main.resolve()) if main.is_file() else "",
            "flow_steps_file": str(steps_only.resolve()) if steps_only.is_file() else "",
            "playwright_step_ir_file": str((rec_dir / "playwright_step_ir.json").resolve())
            if (rec_dir / "playwright_step_ir.json").is_file()
            else "",
            "replayed_from_disk": True,
        },
    }

    ui_elements: List[Dict[str, Any]] = []
    for s in steps:
        action = (s.get("action") or "").lower()
        target = str(s.get("target") or "")[:200]
        page_url = str(s.get("page_url") or "")
        node = (s.get("element_type") or "custom").lower()
        if action == "click":
            el_type = "button" if node in ("button", "a", "submit") else "custom"
        elif action == "input":
            el_type = "input"
        else:
            el_type = "custom"
        loc = s.get("locator")
        xpath = ""
        if isinstance(loc, dict):
            xpath = str(loc.get("xpath") or "")
        ui_elements.append(
            {
                "type": el_type,
                "text": target,
                "selector": xpath or f"//{node}",
                "page_url": page_url,
                "attributes": {},
                "semantic_purpose": action or el_type,
                "confidence": 0.85,
                "source": "flow-recording-replay",
            }
        )

    observation_result: Dict[str, Any] = {
        "ui_elements": ui_elements,
        "page_structure": {"url": page_context["url"]},
        "page_context": page_context,
        "pages": pages,
        "navigation_flow": navigation_flow,
        "flow_steps": steps,
        "playwright_flow_recording": recording,
        "start_url": start_url,
    }
    return observation_result


def flow_recordings_base_dir() -> Path:
    """
    Root directory for all flow recording folders.

    Override with env ``FLOW_RECORDINGS_DIR`` or settings ``FLOW_RECORDINGS_DIR``.
    """
    from app.core.config import settings

    env = os.environ.get("FLOW_RECORDINGS_DIR", "").strip()
    if env:
        return Path(env).expanduser().resolve()
    cfg = getattr(settings, "FLOW_RECORDINGS_DIR", None)
    if cfg:
        p = Path(str(cfg)).expanduser()
        if not p.is_absolute():
            p = _backend_root() / p
        return p.resolve()
    return (_backend_root() / "artifacts" / "flow_recordings").resolve()


def build_recording_document(obs_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Return the canonical ``playwright_flow_recording`` dict, building it if missing."""
    rec = obs_data.get("playwright_flow_recording")
    if isinstance(rec, dict) and rec.get("steps"):
        return rec

    steps: List[Dict[str, Any]] = obs_data.get("flow_steps") or []
    if not steps:
        return None

    from app.utils.playwright_flow_recording import wrap_playwright_flow_recording

    start_url = (obs_data.get("start_url") or "").strip()
    if not start_url:
        pc = obs_data.get("page_context") or {}
        start_url = str(pc.get("url") or "").strip()
    goal = bool((obs_data.get("page_context") or {}).get("goal_reached", False))
    if "goal_reached" in (obs_data.get("navigation_flow") or {}):
        goal = bool((obs_data.get("navigation_flow") or {}).get("goal_reached", goal))

    return wrap_playwright_flow_recording(
        start_url=start_url,
        steps=steps,
        goal_reached=goal,
    )


def _atomic_write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    text = json.dumps(payload, indent=2, ensure_ascii=False, default=str)
    tmp.write_text(text, encoding="utf-8")
    tmp.replace(path)


def _flow_recording_artifacts_from_observation(observation_like: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Return the artifacts dict that has a usable ``directory``, or None."""
    for art in (
        observation_like.get("flow_recording_artifacts"),
        (observation_like.get("page_context") or {}).get("flow_recording_artifacts"),
    ):
        if isinstance(art, dict) and not art.get("error") and (art.get("directory") or "").strip():
            return art
    return None


def _merge_requirements_paths_into_observation(
    observation_like: Dict[str, Any],
    paths: Dict[str, str],
) -> None:
    """Attach ``requirements_result_file`` / ``requirements_directory`` to every artifacts dict on the observation."""
    seen: set[int] = set()
    for art in (
        observation_like.get("flow_recording_artifacts"),
        (observation_like.get("page_context") or {}).get("flow_recording_artifacts"),
    ):
        if not isinstance(art, dict) or art.get("error"):
            continue
        aid = id(art)
        if aid in seen:
            continue
        seen.add(aid)
        art.update(paths)


def persist_requirements_result_to_flow_recording(
    observation_like: Dict[str, Any],
    requirements_result: Dict[str, Any],
    *,
    workflow_id: str,
) -> Optional[Dict[str, str]]:
    """
    If this observation is tied to a flow-recordings directory, write RequirementsAgent output under
    ``{directory}/requirements/requirements_result.json`` and extend ``flow_recording_artifacts`` with paths.

    No-op when recordings are disabled, when there is no artifacts directory, or when the directory is missing on disk.
    """
    from app.core.config import settings

    if not getattr(settings, "FLOW_RECORDINGS_ENABLED", True):
        return None
    art = _flow_recording_artifacts_from_observation(observation_like)
    if not art:
        return None
    rec_dir = Path(str(art.get("directory")).strip())
    if not rec_dir.is_dir():
        logger.warning(
            "Cannot persist requirements_result: flow recording directory missing: %s",
            rec_dir,
        )
        return None
    req_dir = rec_dir / "requirements"
    dest = req_dir / "requirements_result.json"
    envelope = {
        "schema_version": 1,
        "source": "requirements-agent",
        "workflow_id": workflow_id,
        "written_at": datetime.now(timezone.utc).isoformat(),
        "requirements_result": requirements_result,
    }
    try:
        _atomic_write_json(dest, envelope)
    except OSError as e:
        logger.exception("Failed to write requirements_result for workflow %s: %s", workflow_id, e)
        return None
    paths = {
        "requirements_result_file": str(dest.resolve()),
        "requirements_directory": str(req_dir.resolve()),
    }
    _merge_requirements_paths_into_observation(observation_like, paths)
    logger.info(
        "Saved requirements_result for workflow %s → %s",
        workflow_id,
        dest,
    )
    return paths


def build_playwright_step_ir(steps: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Deterministic intermediate representation for tooling / codegen without LLM.

    Mirrors each flow_step's action metadata plus locator strategies from ObservationAgent.
    """
    ordered = sorted(steps, key=lambda s: s.get("order", 0))
    ir_steps: List[Dict[str, Any]] = []
    for s in ordered:
        loc = s.get("locator")
        if not isinstance(loc, dict):
            loc = {}
        ir_step: Dict[str, Any] = {
            "order": s.get("order"),
            "action": s.get("action"),
            "target": s.get("target"),
            "page_url": s.get("page_url"),
            "page_title": s.get("page_title"),
            "element_type": s.get("element_type"),
            "input_type": s.get("input_type"),
            "playwright_suggestions": loc.get("playwright_suggestions") or [],
            "xpath": loc.get("xpath"),
            "backend_node_id": loc.get("backend_node_id"),
            "frame_id": loc.get("frame_id"),
            "attributes": loc.get("attributes") or {},
        }
        ct = loc.get("class_tokens")
        if isinstance(ct, list) and ct:
            ir_step["class_tokens"] = ct
        ir_steps.append(ir_step)
    return {
        "schema_version": 1,
        "source": "observation-step-ir",
        "steps": ir_steps,
        "notes": (
            "Use stable suggestions first (testId, role, css_id); try xpath for positional replay; "
            "kind=css compound-class selectors are fallbacks when class was captured. "
            "Not a Playwright trace; map IR to TS with a small emitter."
        ),
    }


def persist_observation_flow_artifacts(
    workflow_id: str,
    obs_data: Dict[str, Any],
    *,
    enabled: bool = True,
) -> Optional[Dict[str, Any]]:
    """
    Write flow recording JSON files for this workflow and attach metadata to ``obs_data``.

    Returns the ``flow_recording_artifacts`` dict, or None if skipped (disabled / no steps).
    """
    from app.core.config import settings

    if not enabled:
        return None
    if not getattr(settings, "FLOW_RECORDINGS_ENABLED", True):
        return None

    recording = build_recording_document(obs_data)
    if not recording:
        logger.debug("No flow_steps / recording to persist for workflow %s", workflow_id)
        return None

    steps = recording.get("steps") or obs_data.get("flow_steps") or []
    if not steps:
        return None

    dir_name = flow_recording_directory_name(workflow_id)
    out_dir = flow_recordings_base_dir() / dir_name
    main_file = out_dir / "playwright_flow_recording.json"
    steps_file = out_dir / "flow_steps.json"
    ir_file = out_dir / "playwright_step_ir.json"
    step_ir = build_playwright_step_ir(steps)

    try:
        _atomic_write_json(main_file, recording)
        _atomic_write_json(steps_file, steps)
        _atomic_write_json(ir_file, step_ir)
    except OSError as e:
        logger.exception("Failed to write flow recording for workflow %s: %s", workflow_id, e)
        obs_data["flow_recording_artifacts"] = {
            "error": str(e),
            "workflow_id": workflow_id,
        }
        return obs_data["flow_recording_artifacts"]

    artifacts: Dict[str, Any] = {
        "workflow_id": workflow_id,
        "directory_name": dir_name,
        "directory": str(out_dir.resolve()),
        "playwright_flow_recording_file": str(main_file.resolve()),
        "flow_steps_file": str(steps_file.resolve()),
        "playwright_step_ir_file": str(ir_file.resolve()),
        "schema_version": recording.get("schema_version"),
    }
    obs_data["flow_recording_artifacts"] = artifacts
    # Mirror in page_context for consumers that only read page_context
    pc = obs_data.setdefault("page_context", {})
    if isinstance(pc, dict):
        pc["flow_recording_artifacts"] = dict(artifacts)
    logger.info(
        "Saved flow recording for workflow %s → %s",
        workflow_id,
        main_file,
    )
    return artifacts


def persist_test_case_flow_manifests(
    workflow_id: str,
    test_case_ids: Optional[List[Any]],
    obs_data: Dict[str, Any],
    *,
    enabled: bool = True,
) -> Optional[List[str]]:
    """
    After Evolution stores test cases, write one small JSON manifest per test_case_id under
    ``{flow_recordings}/{timestamp}_{short_workflow}/by_test_case/`` linking to the shared recording files.

    Updates ``flow_recording_artifacts["test_case_manifest_files"]`` on ``obs_data`` (and page_context).
    """
    from app.core.config import settings

    if not enabled or not test_case_ids:
        return None
    if not getattr(settings, "FLOW_RECORDINGS_ENABLED", True):
        return None

    artifacts = obs_data.get("flow_recording_artifacts")
    if not isinstance(artifacts, dict) or artifacts.get("error"):
        logger.debug("No flow_recording_artifacts to attach test manifests for workflow %s", workflow_id)
        return None
    out_dir_str = artifacts.get("directory")
    if not out_dir_str:
        return None

    base = Path(out_dir_str) / "by_test_case"
    manifest_paths: List[str] = []
    try:
        base.mkdir(parents=True, exist_ok=True)
        for tid in test_case_ids:
            tid_str = str(tid).strip()
            safe_tid = "".join(c if c.isalnum() or c in "-_" else "_" for c in tid_str)[:120]
            manifest = {
                "schema_version": 1,
                "workflow_id": workflow_id,
                "test_case_id": tid,
                "playwright_flow_recording_file": artifacts.get("playwright_flow_recording_file"),
                "flow_steps_file": artifacts.get("flow_steps_file"),
                "playwright_step_ir_file": artifacts.get("playwright_step_ir_file"),
                "shared_recording_directory": out_dir_str,
            }
            dest = base / f"test_case_{safe_tid}.json"
            _atomic_write_json(dest, manifest)
            manifest_paths.append(str(dest.resolve()))
    except OSError as e:
        logger.exception("Failed test-case flow manifests for workflow %s: %s", workflow_id, e)
        artifacts["test_case_manifest_error"] = str(e)
        return None

    artifacts["test_case_manifest_files"] = manifest_paths
    artifacts["test_case_manifest_count"] = len(manifest_paths)
    pc = obs_data.get("page_context")
    if isinstance(pc, dict):
        # Keep page_context in sync with obs_data (shallow copy from first persist would be stale).
        pc["flow_recording_artifacts"] = dict(obs_data["flow_recording_artifacts"])
    logger.info(
        "Wrote %d test-case flow manifest(s) under %s",
        len(manifest_paths),
        base,
    )
    return manifest_paths
