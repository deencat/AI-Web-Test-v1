"""Knowledge Base document models."""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from app.db.base import Base, utc_now


class FileType(str, enum.Enum):
    """File type enumeration."""
    PDF = "pdf"
    DOCX = "docx"
    TXT = "txt"
    MD = "md"


class KBCategory(Base):
    """Knowledge Base category model."""
    
    __tablename__ = "kb_categories"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True, index=True)
    description = Column(Text, nullable=True)
    color = Column(String(20), nullable=False, default="#3B82F6")  # Hex color
    icon = Column(String(50), nullable=True)  # Icon name
    
    # Relationships
    documents = relationship("KBDocument", back_populates="category", cascade="all, delete-orphan")
    test_templates = relationship("TestTemplate", back_populates="category")
    
    def __repr__(self):
        return f"<KBCategory(id={self.id}, name='{self.name}')>"


class KBDocument(Base):
    """Knowledge Base document model."""
    
    __tablename__ = "kb_documents"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    
    # File information
    filename = Column(String(255), nullable=False)  # Original filename
    file_path = Column(String(500), nullable=False)  # Storage path
    file_type = Column(SQLEnum(FileType), nullable=False, index=True)
    file_size = Column(Integer, nullable=False)  # Size in bytes
    
    # Content
    content = Column(Text, nullable=True)  # Extracted text content
    
    # Metadata
    referenced_count = Column(Integer, default=0)  # How many times referenced
    created_at = Column(DateTime, nullable=False, default=utc_now)
    updated_at = Column(DateTime, nullable=False, default=utc_now, onupdate=utc_now)
    
    # Relationships
    category_id = Column(Integer, ForeignKey("kb_categories.id"), nullable=False, index=True)
    category = relationship("KBCategory", back_populates="documents")
    
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    user = relationship("User", back_populates="kb_documents")
    
    def __repr__(self):
        return f"<KBDocument(id={self.id}, title='{self.title}', type={self.file_type})>"

