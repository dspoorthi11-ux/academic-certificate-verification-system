import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class CertificateDocument(Base):
    __tablename__ = "certificate_documents"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    certificate_id: Mapped[str] = mapped_column(String(36), ForeignKey("certificates.id"), unique=True)
    file_name: Mapped[str] = mapped_column(String(255))
    file_path: Mapped[str] = mapped_column(String(500))
    mime_type: Mapped[str] = mapped_column(String(100))
    size_bytes: Mapped[int] = mapped_column(Integer)
    original_hash: Mapped[str] = mapped_column(String(128))
    ipfs_hash: Mapped[str | None] = mapped_column(String(128), nullable=True)
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    certificate: Mapped["Certificate"] = relationship(back_populates="document", foreign_keys=[certificate_id])


class BlockchainRecord(Base):
    __tablename__ = "blockchain_records"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    certificate_id: Mapped[str] = mapped_column(String(36), ForeignKey("certificates.id"), unique=True)
    tx_hash: Mapped[str] = mapped_column(String(128), unique=True)
    contract_address: Mapped[str | None] = mapped_column(String(255), nullable=True)
    network: Mapped[str] = mapped_column(String(100), default="hardhat")
    status: Mapped[str] = mapped_column(String(50), default="pending")
    registered_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    certificate: Mapped["Certificate"] = relationship(back_populates="blockchain_record", foreign_keys=[certificate_id])


class Verification(Base):
    __tablename__ = "verifications"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    certificate_id: Mapped[str] = mapped_column(String(36), ForeignKey("certificates.id"), index=True)
    verifier_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="PENDING")
    result: Mapped[str] = mapped_column(String(50), default="UNKNOWN")
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    ai_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    verification_timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    certificate: Mapped["Certificate"] = relationship(back_populates="verifications", foreign_keys=[certificate_id])


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    action: Mapped[str] = mapped_column(String(255))
    resource: Mapped[str | None] = mapped_column(String(255), nullable=True)
    result: Mapped[str] = mapped_column(String(100), default="SUCCESS")
    ip_address: Mapped[str | None] = mapped_column(String(100), nullable=True)
    details: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class FraudAnalysis(Base):
    __tablename__ = "fraud_analyses"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    certificate_id: Mapped[str] = mapped_column(String(36), ForeignKey("certificates.id"), index=True)
    authenticity_score: Mapped[float] = mapped_column(Float, default=0.0)
    fraud_probability: Mapped[float] = mapped_column(Float, default=0.0)
    risk_level: Mapped[str] = mapped_column(String(50), default="LOW")
    detected_anomalies: Mapped[str | None] = mapped_column(Text, nullable=True)
    extracted_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    explanation: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    certificate: Mapped["Certificate"] = relationship(back_populates="fraud_analysis", foreign_keys=[certificate_id])


class Certificate(Base):
    __tablename__ = "certificates"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    certificate_id: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    student_id: Mapped[str] = mapped_column(String(36), ForeignKey("students.id"), index=True)
    issuer_id: Mapped[str] = mapped_column(String(36), ForeignKey("universities.id"), index=True)
    certificate_type: Mapped[str] = mapped_column(String(100))
    course_name: Mapped[str] = mapped_column(String(255))
    specialization: Mapped[str | None] = mapped_column(String(255), nullable=True)
    institution_name: Mapped[str] = mapped_column(String(255))
    issue_date: Mapped[datetime] = mapped_column(DateTime)
    graduation_year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    document_hash: Mapped[str] = mapped_column(String(128), index=True)
    ipfs_hash: Mapped[str | None] = mapped_column(String(128), nullable=True)
    blockchain_transaction_hash: Mapped[str | None] = mapped_column(String(128), nullable=True)
    blockchain_network: Mapped[str | None] = mapped_column(String(100), nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="ACTIVE")
    verification_url: Mapped[str | None] = mapped_column(String(255), nullable=True)
    qr_data: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    document: Mapped[CertificateDocument | None] = relationship(back_populates="certificate", uselist=False)
    blockchain_record: Mapped[BlockchainRecord | None] = relationship(back_populates="certificate", uselist=False)
    verifications: Mapped[list[Verification]] = relationship(back_populates="certificate")
    fraud_analysis: Mapped[list[FraudAnalysis]] = relationship(back_populates="certificate")
