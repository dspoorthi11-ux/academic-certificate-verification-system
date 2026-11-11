from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class CertificateCreate(BaseModel):
    student_name: str
    student_email: str | None = None
    student_number: str | None = None
    course_name: str
    certificate_type: str
    specialization: str | None = None
    institution_name: str
    issue_date: datetime | None = None
    graduation_year: int | None = None
    document_hash: str
    ipfs_hash: str | None = None
    blockchain_transaction_hash: str | None = None
    status: str = "ACTIVE"


class CertificateOut(BaseModel):
    id: str
    certificate_id: str
    student_id: str
    issuer_id: str
    certificate_type: str
    course_name: str
    specialization: str | None = None
    institution_name: str
    issue_date: datetime
    graduation_year: int | None = None
    document_hash: str
    ipfs_hash: str | None = None
    blockchain_transaction_hash: str | None = None
    blockchain_network: str | None = None
    status: str
    verification_url: str | None = None
    qr_data: str | None = None
    created_at: datetime
    updated_at: datetime


class VerificationRequest(BaseModel):
    certificate_id: str
    uploaded_document_hash: str | None = None
    notes: str | None = None


class VerificationResult(BaseModel):
    certificate_id: str
    result: str
    status: str
    ai_risk_level: str | None = None
    authenticity_score: float | None = None
    message: str
    details: dict[str, Any] = {}
