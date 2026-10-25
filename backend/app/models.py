import uuid
from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey, text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, nullable=False)
    full_name = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=text("now()"), nullable=False)

    documents = relationship("Document", back_populates="user", cascade="all, delete-orphan")


class Document(Base):
    __tablename__ = "documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    filename = Column(String, nullable=False)
    storage_path = Column(String, nullable=False)
    original_size_bytes = Column(Integer, nullable=False)
    compressed_size_bytes = Column(Integer, nullable=False)
    fingerprints = Column(JSONB, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=text("now()"), nullable=False)

    user = relationship("User", back_populates="documents")
    
    # Linked back_populates relationships to fix SQLAlchemy warnings
    source_reports = relationship(
        "PlagiarismReport", 
        foreign_keys="PlagiarismReport.source_doc_id", 
        back_populates="source_document",
        cascade="all, delete-orphan"
    )
    matched_reports = relationship(
        "PlagiarismReport", 
        foreign_keys="PlagiarismReport.matched_doc_id", 
        back_populates="matched_document",
        cascade="all, delete-orphan"
    )


class PlagiarismReport(Base):
    __tablename__ = "plagiarism_reports"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_doc_id = Column(UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    matched_doc_id = Column(UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    similarity_score = Column(Float, nullable=False)
    matched_segments = Column(JSONB, default=[], nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=text("now()"), nullable=False)

    source_document = relationship("Document", foreign_keys=[source_doc_id], back_populates="source_reports")
    matched_document = relationship("Document", foreign_keys=[matched_doc_id], back_populates="matched_reports")