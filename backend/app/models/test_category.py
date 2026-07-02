"""TestCategory model for user-defined test organization categories."""
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import relationship

from app.db.base import Base, utc_now


class TestCategory(Base):
    """User-scoped category for organizing saved test cases."""

    __tablename__ = "test_categories"
    __table_args__ = (
        UniqueConstraint("user_id", "name", name="uq_test_categories_user_name"),
    )

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    color = Column(String(20), nullable=False, default="#3B82F6")
    sort_order = Column(Integer, nullable=False, default=0)
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    created_at = Column(DateTime, nullable=False, default=utc_now)
    updated_at = Column(DateTime, nullable=False, default=utc_now, onupdate=utc_now)

    user = relationship("User", back_populates="test_categories")
    test_cases = relationship("TestCase", back_populates="test_category")

    def __repr__(self) -> str:
        return f"<TestCategory(id={self.id}, name='{self.name}', user_id={self.user_id})>"
