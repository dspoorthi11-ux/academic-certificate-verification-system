from typing import Literal

from pydantic import BaseModel, EmailStr, Field, HttpUrl


class InstitutionRegistration(BaseModel):
    institution_name: str = Field(min_length=3, max_length=255)
    institution_type: str = Field(min_length=2, max_length=100)
    official_email: EmailStr
    website: HttpUrl
    country: str = Field(min_length=2, max_length=120)
    state: str | None = Field(default=None, max_length=120)
    address: str = Field(min_length=8, max_length=2000)
    accreditation: str = Field(min_length=3, max_length=2000)
    representative_name: str = Field(min_length=2, max_length=255)
    representative_designation: str = Field(min_length=2, max_length=255)
    contact_number: str = Field(min_length=6, max_length=80)
    supporting_documents: list[str] = Field(default_factory=list, max_length=20)
    institution_public_key: str | None = None


class InstitutionReview(BaseModel):
    status: Literal["UNDER_REVIEW", "APPROVED", "REJECTED", "SUSPENDED"]
    evidence_reviewed: list[str] = Field(default_factory=list, max_length=20)
    notes: str | None = Field(default=None, max_length=2000)


class PublicVerificationRequest(BaseModel):
    certificate_id: str = Field(min_length=3, max_length=100)
