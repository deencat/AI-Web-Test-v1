"""
StepLibraryModule ORM model — Sprint 10.11 Step Library.

Stores reusable named step sequences that can be referenced from test cases
using the @module:name(param=value) inline syntax.
"""
from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import relationship

from app.db.base import Base, utc_now


class StepLibraryModule(Base):
    """
    A named, parameterized, reusable step sequence.

    Referenced in test case steps using: @module:name(param=value)
    The resolver expands these references to concrete steps before execution.
    """

    __tablename__ = "step_library_modules"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Slug identifier, e.g. "login_three_hk" — unique per user
    name = Column(String(100), nullable=False, unique=True, index=True)

    # Human-readable display name, e.g. "Three HK Login Flow"
    display_name = Column(String(255), nullable=False)

    # Optional description of what the module does
    description = Column(Text, nullable=True)

    # List of step strings or step dicts — same format as TestCase.steps
    steps = Column(JSON, nullable=False)

    # Declared parameter names, e.g. ["username", "password"]
    parameters = Column(JSON, nullable=True)

    # Searchable tags, e.g. ["e2e", "checkout"]
    tags = Column(JSON, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    # Relationships
    user = relationship("User", back_populates="step_library_modules")
