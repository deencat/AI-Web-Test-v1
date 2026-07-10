"""App State Graph (ASG) ORM models — Feature 3 deterministic test generation."""
from __future__ import annotations

import enum

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    JSON,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from app.db.base import Base, utc_now


class ASGGraphStatus(str, enum.Enum):
    BUILDING = "building"
    READY = "ready"
    FAILED = "failed"


class ASGGraph(Base):
    __tablename__ = "asg_graphs"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, nullable=True, index=True)
    created_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    status = Column(String(32), nullable=False, default=ASGGraphStatus.BUILDING.value, index=True)
    policy_json = Column(JSON, nullable=False, default=dict)
    seed_hash = Column(String(64), nullable=False, index=True)
    confidence_score = Column(Float, nullable=False, default=0.0)
    created_at = Column(DateTime, nullable=False, default=utc_now)
    updated_at = Column(DateTime, nullable=False, default=utc_now, onupdate=utc_now)

    nodes = relationship("ASGNode", back_populates="graph", cascade="all, delete-orphan")
    edges = relationship("ASGEdge", back_populates="graph", cascade="all, delete-orphan")
    paths = relationship("ASGPath", back_populates="graph", cascade="all, delete-orphan")
    synthesized_tests = relationship(
        "ASGSynthesizedTest", back_populates="graph", cascade="all, delete-orphan"
    )


class ASGNode(Base):
    __tablename__ = "asg_nodes"
    __table_args__ = (
        Index("ix_asg_nodes_graph_fingerprint", "graph_id", "state_fingerprint"),
    )

    id = Column(Integer, primary_key=True, index=True)
    graph_id = Column(Integer, ForeignKey("asg_graphs.id", ondelete="CASCADE"), nullable=False, index=True)
    state_fingerprint = Column(String(64), nullable=False)
    url = Column(Text, nullable=False, default="")
    title = Column(String(512), nullable=False, default="")
    state_payload_json = Column(JSON, nullable=False, default=dict)
    confidence = Column(Float, nullable=False, default=0.0)
    is_terminal = Column(Boolean, nullable=False, default=False)

    graph = relationship("ASGGraph", back_populates="nodes")
    outgoing_edges = relationship(
        "ASGEdge",
        foreign_keys="ASGEdge.from_node_id",
        back_populates="from_node",
        cascade="all, delete-orphan",
    )
    incoming_edges = relationship(
        "ASGEdge",
        foreign_keys="ASGEdge.to_node_id",
        back_populates="to_node",
        cascade="all, delete-orphan",
    )


class ASGEdge(Base):
    __tablename__ = "asg_edges"
    __table_args__ = (
        Index("ix_asg_edges_graph_deterministic_key", "graph_id", "deterministic_key"),
    )

    id = Column(Integer, primary_key=True, index=True)
    graph_id = Column(Integer, ForeignKey("asg_graphs.id", ondelete="CASCADE"), nullable=False, index=True)
    from_node_id = Column(Integer, ForeignKey("asg_nodes.id", ondelete="CASCADE"), nullable=False, index=True)
    to_node_id = Column(Integer, ForeignKey("asg_nodes.id", ondelete="CASCADE"), nullable=False, index=True)
    action_type = Column(String(64), nullable=False, default="click")
    action_payload_json = Column(JSON, nullable=False, default=dict)
    readiness_snapshot_json = Column(JSON, nullable=True)
    confidence = Column(Float, nullable=False, default=0.0)
    deterministic_key = Column(String(128), nullable=False)

    graph = relationship("ASGGraph", back_populates="edges")
    from_node = relationship("ASGNode", foreign_keys=[from_node_id], back_populates="outgoing_edges")
    to_node = relationship("ASGNode", foreign_keys=[to_node_id], back_populates="incoming_edges")


class ASGPath(Base):
    __tablename__ = "asg_paths"
    __table_args__ = (
        Index("ix_asg_paths_graph_score", "graph_id", "score"),
    )

    id = Column(Integer, primary_key=True, index=True)
    graph_id = Column(Integer, ForeignKey("asg_graphs.id", ondelete="CASCADE"), nullable=False, index=True)
    goal_type = Column(String(64), nullable=False, default="shortest_path")
    path_nodes_json = Column(JSON, nullable=False, default=list)
    path_edges_json = Column(JSON, nullable=False, default=list)
    score = Column(Float, nullable=False, default=0.0)
    risk_score = Column(Float, nullable=False, default=0.0)
    selected = Column(Boolean, nullable=False, default=False)

    graph = relationship("ASGGraph", back_populates="paths")
    synthesized_tests = relationship("ASGSynthesizedTest", back_populates="path")


class ASGSynthesizedTest(Base):
    __tablename__ = "asg_synthesized_tests"

    id = Column(Integer, primary_key=True, index=True)
    graph_id = Column(Integer, ForeignKey("asg_graphs.id", ondelete="CASCADE"), nullable=False, index=True)
    path_id = Column(Integer, ForeignKey("asg_paths.id", ondelete="SET NULL"), nullable=True, index=True)
    test_case_id = Column(Integer, ForeignKey("test_cases.id", ondelete="SET NULL"), nullable=True, index=True)
    steps_json = Column(JSON, nullable=False, default=list)
    synthesis_manifest_json = Column(JSON, nullable=False, default=dict)
    validation_score = Column(Float, nullable=True)

    graph = relationship("ASGGraph", back_populates="synthesized_tests")
    path = relationship("ASGPath", back_populates="synthesized_tests")
