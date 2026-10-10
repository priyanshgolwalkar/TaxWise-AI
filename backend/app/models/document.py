from datetime import datetime
from sqlalchemy import DateTime, ForeignKey, Integer, JSON, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.session import Base

class Document(Base):
    __tablename__ = 'documents'
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'), index=True)
    filename: Mapped[str] = mapped_column(String(255))
    content_type: Mapped[str] = mapped_column(String(100))
    size_bytes: Mapped[int] = mapped_column(Integer)
    storage_key: Mapped[str] = mapped_column(String(500), unique=True)
    status: Mapped[str] = mapped_column(String(40), default='uploaded')
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    user = relationship('User', back_populates='documents')
    extracted_data = relationship('ExtractedFinancialData', back_populates='document', uselist=False, cascade='all, delete-orphan')

class ExtractedFinancialData(Base):
    __tablename__ = 'extracted_financial_data'
    id: Mapped[int] = mapped_column(primary_key=True)
    document_id: Mapped[int] = mapped_column(ForeignKey('documents.id'), unique=True, index=True)
    normalized_data: Mapped[dict] = mapped_column(JSON)
    raw_text: Mapped[str] = mapped_column(Text, default='')
    missing_fields: Mapped[list] = mapped_column(JSON, default=list)
    validation_errors: Mapped[list] = mapped_column(JSON, default=list)
    requires_user_verification: Mapped[bool] = mapped_column(default=True)
    document = relationship('Document', back_populates='extracted_data')
