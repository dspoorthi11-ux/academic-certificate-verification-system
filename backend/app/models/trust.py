import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class InstitutionRegistry(Base):
    __tablename__ = "institution_registry"
    __table_args__ = (
        UniqueConstraint("official_email", name="uq_institution_registry_email"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), index=True)
    university_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("universities.id"), nullable=True)
    institution_name: Mapped[str] = mapped_column(String(255))
    institution_type: Mapped[str] = mapped_column(String(100))
    official_email: Mapped[str] = mapped_column(String(255))
    website: Mapped[str] = mapped_column(String(255))
    country: Mapped[str] = mapped_column(String(120))
    state: Mapped[str | None] = mapped_column(String(120), nullable=True)
    address: Mapped[str] = mapped_column(Text)
    accreditation: Mapped[str] = mapped_column(Text)
    representative_name: Mapped[str] = mapped_column(String(255))
    representative_designation: Mapped[str] = mapped_column(String(255))
    contact_number: Mapped[str] = mapped_column(String(80))
    supporting_documents: Mapped[str] = mapped_column(Text, default="[]")
    domain_candidate: Mapped[str] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(32), default="PENDING", index=True)
    institution_public_key: Mapped[str | None] = mapped_column(Text, nullable=True)
    approved_by: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    decision_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class InstitutionVerification(Base):
    __tablename__ = "institution_verifications"
    __table_args__ = (Index("ix_institution_verifications_institution_created", "institution_id", "created_at"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    institution_id: Mapped[str] = mapped_column(String(36), ForeignKey("institution_registry.id"), index=True)
    admin_user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"))
    previous_status: Mapped[str] = mapped_column(String(32))
    new_status: Mapped[str] = mapped_column(String(32))
    evidence_reviewed: Mapped[str | None] = mapped_column(Text, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class VerificationAttestation(Base):
    __tablename__ = "verification_attestations"
    __table_args__ = (UniqueConstraint("verification_id", "version", name="uq_attestation_verification_version"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    public_id: Mapped[str] = mapped_column(String(40), unique=True, index=True)
    verification_id: Mapped[str] = mapped_column(String(36), ForeignKey("verifications.id"), index=True)
    certificate_id: Mapped[str] = mapped_column(String(100), index=True)
    document_hash: Mapped[str] = mapped_column(String(128))
    institution_name: Mapped[str] = mapped_column(String(255))
    result: Mapped[str] = mapped_column(String(32))
    verified_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    methodology: Mapped[str] = mapped_column(Text)
    issuer_confirmation_reference: Mapped[str] = mapped_column(String(255))
    blockchain_reference: Mapped[str | None] = mapped_column(String(255), nullable=True)
    platform_identity: Mapped[str] = mapped_column(String(255))
    version: Mapped[int] = mapped_column(Integer, default=1)
    key_id: Mapped[str] = mapped_column(String(128))
    public_key: Mapped[str] = mapped_column(Text)
    signature: Mapped[str] = mapped_column(Text)
    payload: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class DigitalSignature(Base):
    __tablename__ = "digital_signatures"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    attestation_id: Mapped[str] = mapped_column(String(36), ForeignKey("verification_attestations.id"), index=True)
    algorithm: Mapped[str] = mapped_column(String(50), default="Ed25519")
    key_id: Mapped[str] = mapped_column(String(128))
    public_key: Mapped[str] = mapped_column(Text)
    signature: Mapped[str] = mapped_column(Text)
    signed_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class VerificationArchive(Base):
    __tablename__ = "verification_archives"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    attestation_id: Mapped[str] = mapped_column(String(36), ForeignKey("verification_attestations.id"), unique=True)
    document_hash: Mapped[str] = mapped_column(String(128), index=True)
    original_document_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    evidence_json: Mapped[str] = mapped_column(Text)
    archived_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class BlockchainTransaction(Base):
    __tablename__ = "blockchain_transactions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    certificate_id: Mapped[str] = mapped_column(String(100), index=True)
    transaction_hash: Mapped[str | None] = mapped_column(String(128), unique=True, nullable=True)
    network: Mapped[str] = mapped_column(String(100))
    operation: Mapped[str] = mapped_column(String(50))
    status: Mapped[str] = mapped_column(String(32))
    details: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class VerificationRequestRecord(Base):
    __tablename__ = "verification_requests"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    certificate_id: Mapped[str] = mapped_column(String(100), index=True)
    requester_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    institution_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("institution_registry.id"), nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="PENDING")
    request_reference: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)