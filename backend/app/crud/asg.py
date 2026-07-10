"""CRUD operations for App State Graph (ASG) entities."""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from sqlalchemy import desc, func
from sqlalchemy.orm import Session

from app.models.asg import (
    ASGEdge,
    ASGGraph,
    ASGGraphStatus,
    ASGNode,
    ASGPath,
    ASGSynthesizedTest,
)


def create_graph(
    db: Session,
    *,
    created_by: Optional[int],
    project_id: Optional[int],
    policy_json: Dict[str, Any],
    seed_hash: str,
    confidence_score: float = 0.0,
    status: str = ASGGraphStatus.BUILDING.value,
) -> ASGGraph:
    graph = ASGGraph(
        project_id=project_id,
        created_by=created_by,
        status=status,
        policy_json=policy_json,
        seed_hash=seed_hash,
        confidence_score=confidence_score,
    )
    db.add(graph)
    db.commit()
    db.refresh(graph)
    return graph


def get_graph(db: Session, graph_id: int) -> Optional[ASGGraph]:
    return db.query(ASGGraph).filter(ASGGraph.id == graph_id).first()


def update_graph_status(
    db: Session,
    graph: ASGGraph,
    *,
    status: str,
    confidence_score: Optional[float] = None,
) -> ASGGraph:
    graph.status = status
    if confidence_score is not None:
        graph.confidence_score = confidence_score
    db.add(graph)
    db.commit()
    db.refresh(graph)
    return graph


def create_node(
    db: Session,
    *,
    graph_id: int,
    state_fingerprint: str,
    url: str,
    title: str,
    state_payload_json: Dict[str, Any],
    confidence: float,
    is_terminal: bool = False,
) -> ASGNode:
    node = ASGNode(
        graph_id=graph_id,
        state_fingerprint=state_fingerprint,
        url=url,
        title=title,
        state_payload_json=state_payload_json,
        confidence=confidence,
        is_terminal=is_terminal,
    )
    db.add(node)
    db.flush()
    return node


def get_node_by_fingerprint(
    db: Session, graph_id: int, state_fingerprint: str
) -> Optional[ASGNode]:
    return (
        db.query(ASGNode)
        .filter(ASGNode.graph_id == graph_id, ASGNode.state_fingerprint == state_fingerprint)
        .first()
    )


def list_nodes(db: Session, graph_id: int) -> List[ASGNode]:
    return db.query(ASGNode).filter(ASGNode.graph_id == graph_id).all()


def create_edge(
    db: Session,
    *,
    graph_id: int,
    from_node_id: int,
    to_node_id: int,
    action_type: str,
    action_payload_json: Dict[str, Any],
    readiness_snapshot_json: Optional[Dict[str, Any]],
    confidence: float,
    deterministic_key: str,
) -> ASGEdge:
    edge = ASGEdge(
        graph_id=graph_id,
        from_node_id=from_node_id,
        to_node_id=to_node_id,
        action_type=action_type,
        action_payload_json=action_payload_json,
        readiness_snapshot_json=readiness_snapshot_json,
        confidence=confidence,
        deterministic_key=deterministic_key,
    )
    db.add(edge)
    db.flush()
    return edge


def get_edge_by_key(
    db: Session, graph_id: int, deterministic_key: str
) -> Optional[ASGEdge]:
    return (
        db.query(ASGEdge)
        .filter(ASGEdge.graph_id == graph_id, ASGEdge.deterministic_key == deterministic_key)
        .first()
    )


def list_edges(db: Session, graph_id: int) -> List[ASGEdge]:
    return db.query(ASGEdge).filter(ASGEdge.graph_id == graph_id).all()


def create_path(
    db: Session,
    *,
    graph_id: int,
    goal_type: str,
    path_nodes_json: List[Any],
    path_edges_json: List[Any],
    score: float,
    risk_score: float,
    selected: bool = False,
) -> ASGPath:
    path = ASGPath(
        graph_id=graph_id,
        goal_type=goal_type,
        path_nodes_json=path_nodes_json,
        path_edges_json=path_edges_json,
        score=score,
        risk_score=risk_score,
        selected=selected,
    )
    db.add(path)
    db.commit()
    db.refresh(path)
    return path


def list_paths(db: Session, graph_id: int, *, selected_only: bool = False) -> List[ASGPath]:
    q = db.query(ASGPath).filter(ASGPath.graph_id == graph_id)
    if selected_only:
        q = q.filter(ASGPath.selected.is_(True))
    return q.order_by(desc(ASGPath.score)).all()


def get_path(db: Session, graph_id: int, path_id: int) -> Optional[ASGPath]:
    return (
        db.query(ASGPath)
        .filter(ASGPath.graph_id == graph_id, ASGPath.id == path_id)
        .first()
    )


def mark_paths_selected(db: Session, graph_id: int, path_ids: List[int]) -> None:
    db.query(ASGPath).filter(ASGPath.graph_id == graph_id).update(
        {ASGPath.selected: False}, synchronize_session=False
    )
    if path_ids:
        db.query(ASGPath).filter(
            ASGPath.graph_id == graph_id, ASGPath.id.in_(path_ids)
        ).update({ASGPath.selected: True}, synchronize_session=False)
    db.commit()


def create_synthesized_test(
    db: Session,
    *,
    graph_id: int,
    path_id: Optional[int],
    steps_json: List[str],
    synthesis_manifest_json: Dict[str, Any],
    validation_score: Optional[float] = None,
    test_case_id: Optional[int] = None,
) -> ASGSynthesizedTest:
    record = ASGSynthesizedTest(
        graph_id=graph_id,
        path_id=path_id,
        test_case_id=test_case_id,
        steps_json=steps_json,
        synthesis_manifest_json=synthesis_manifest_json,
        validation_score=validation_score,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def count_nodes_edges(db: Session, graph_id: int) -> tuple[int, int]:
    node_count = db.query(func.count(ASGNode.id)).filter(ASGNode.graph_id == graph_id).scalar() or 0
    edge_count = db.query(func.count(ASGEdge.id)).filter(ASGEdge.graph_id == graph_id).scalar() or 0
    return int(node_count), int(edge_count)
