import asyncio
import hashlib
import io
from datetime import datetime
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool
from pypdf import PdfReader
from reportlab.pdfgen import canvas as pdf_canvas

from app.api.routes.verification import _run_verification, download_attestation_report, public_verify_attestation
from app.models.base import Base
from app.models.certificate import Certificate
from app.models.trust import InstitutionRegistry, VerificationAttestation
from app.models.user import Role, Student, University, User
from app.schemas.trust import PublicVerificationRequest
from app.services.attestation_signing import AttestationSigner
from app.services.blockchain_service import BlockchainService
from ai_service.fraud_detection import get_fraud_service

def make_test_pdf() -> bytes:
    buffer = io.BytesIO()
    page = pdf_canvas.Canvas(buffer)
    page.drawString(72, 720, "Northbridge University Original Certificate")
    page.drawString(72, 680, "Computer Science degree record")
    page.save()
    return buffer.getvalue()


DOCUMENT_BYTES = make_test_pdf()
DOCUMENT_HASH = hashlib.sha256(DOCUMENT_BYTES).hexdigest()


@pytest.fixture
def db_session():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    session = factory()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(engine)
        engine.dispose()


def add_certificate_records(session: Session, issuer_status: str = "APPROVED") -> Certificate:
    university_role = Role(name="university")
    student_role = Role(name="student")
    session.add_all([university_role, student_role])
    session.flush()

    issuer_user = User(
        email="records@northbridge.edu",
        full_name="Northbridge Records",
        password_hash="unused",
        role_id=university_role.id,
    )
    student_user = User(
        email="student@example.edu",
        full_name="Example Student",
        password_hash="unused",
        role_id=student_role.id,
    )
    session.add_all([issuer_user, student_user])
    session.flush()

    university = University(
        user_id=issuer_user.id,
        name="Northbridge University",
        country="Example Country",
        website="https://northbridge.edu",
    )
    student = Student(user_id=student_user.id, university_name="Northbridge University")
    session.add_all([university, student])
    session.flush()

    certificate = Certificate(
        certificate_id="CERT-TRUST-001",
        student_id=student.id,
        issuer_id=university.id,
        certificate_type="Degree",
        course_name="Computer Science",
        institution_name="Northbridge University",
        issue_date=datetime(2025, 6, 1),
        document_hash=DOCUMENT_HASH,
        status="ACTIVE",
    )
    institution = InstitutionRegistry(
        user_id=issuer_user.id,
        university_id=university.id,
        institution_name="Northbridge University",
        institution_type="University",
        official_email="records@northbridge.edu",
        website="https://northbridge.edu",
        country="Example Country",
        address="1 University Road",
        accreditation="Example Accreditation Authority reference 1",
        representative_name="Records Officer",
        representative_designation="Registrar",
        contact_number="+10000000000",
        supporting_documents="[{\"id\":\"evidence-1\"}]",
        domain_candidate="northbridge.edu",
        status=issuer_status,
    )
    session.add_all([certificate, institution])
    session.commit()
    return certificate


def test_unapproved_institution_cannot_authenticate_certificate(db_session: Session):
    add_certificate_records(db_session, issuer_status="PENDING")

    result = _run_verification(
        db_session,
        PublicVerificationRequest(certificate_id="CERT-TRUST-001"),
        original_document=DOCUMENT_BYTES,
        mime_type="application/pdf",
    )

    assert result["result"] == "UNABLE_TO_AUTHENTICATE"
    assert result["issuer_authentication"] == "UNCONFIRMED"
    assert result["attestation"] is None
    assert db_session.query(VerificationAttestation).count() == 0


def test_matching_hash_creates_verifiable_signed_attestation(db_session: Session, monkeypatch, tmp_path):
    add_certificate_records(db_session)
    monkeypatch.setenv("ATTESTATION_PRIVATE_KEY_PATH", str(tmp_path / "attestation.pem"))

    result = _run_verification(
        db_session,
        PublicVerificationRequest(certificate_id="CERT-TRUST-001"),
        original_document=DOCUMENT_BYTES,
        mime_type="application/pdf",
    )

    assert result["result"] == "AUTHENTIC"
    assert result["attestation"] is not None
    public_id = result["attestation"]["verification_id"]
    public_result = public_verify_attestation(public_id, db_session)
    assert public_result["signature"]["valid"] is True
    assert public_result["document_sha256"] == DOCUMENT_HASH

    report_response = download_attestation_report(public_id, db_session)

    async def consume_report() -> bytes:
        return b"".join([part async for part in report_response.body_iterator])

    report_bytes = asyncio.run(consume_report())
    report_pdf = PdfReader(io.BytesIO(report_bytes))
    assert len(report_pdf.pages) >= 2
    assert "Northbridge University Original Certificate" in report_pdf.pages[0].extract_text()
    archive_path = Path(__file__).resolve().parents[1] / "storage" / "documents" / f"{DOCUMENT_HASH}.bin"
    if archive_path.exists():
        archive_path.unlink()

    changed_payload = {"document_sha256": "0" * 64}
    assert AttestationSigner.verify(
        changed_payload,
        db_session.query(VerificationAttestation).filter_by(public_id=public_id).one().signature,
        public_result["signature"]["public_key"],
    ) is False


def test_hash_mismatch_is_not_overridden_by_ai_risk(db_session: Session):
    add_certificate_records(db_session)

    result = _run_verification(
        db_session,
        PublicVerificationRequest(certificate_id="CERT-TRUST-001"),
        original_document=b"tampered document bytes",
        mime_type="application/pdf",
    )

    assert result["result"] == "TAMPERED"
    assert result["attestation"] is None
    assert result["ai_analysis"]["role"] == "SUPPORTING_RISK_ASSESSMENT_ONLY"


def test_id_lookup_does_not_claim_document_integrity(db_session: Session):
    add_certificate_records(db_session)

    result = _run_verification(db_session, PublicVerificationRequest(certificate_id="CERT-TRUST-001"))

    assert result["result"] == "DOCUMENT_REQUIRED"
    assert result["document_integrity"] == "NOT_MATCHED_OR_NOT_CHECKED"
    assert result["attestation"] is None


def test_unknown_certificate_returns_unable_to_authenticate_with_ai_summary(db_session: Session):
    result = _run_verification(
        db_session,
        PublicVerificationRequest(certificate_id="10619788"),
        original_document=DOCUMENT_BYTES,
        mime_type="application/pdf",
    )

    assert result["result"] == "UNABLE_TO_AUTHENTICATE"
    assert "no trusted issuer record" in result["message"]
    assert result["issuer_authentication"] == "UNCONFIRMED"
    assert result["attestation"] is None
    assert result["ai_analysis"]["analysis_status"] == "COMPLETED"
    assert not any("Document hash is missing" in anomaly for anomaly in result["ai_analysis"]["detected_anomalies"])


def test_blockchain_adapter_never_fabricates_confirmation():
    service = BlockchainService("http://127.0.0.1:1")

    registered = service.register_certificate("CERT-TRUST-001", "a" * 64, "issuer")
    verified = service.verify_certificate("CERT-TRUST-001", "a" * 64)

    assert registered["success"] is False
    assert registered["transaction_hash"] is None
    assert verified["status"] == "not_checked"
    assert verified["exists"] is None


def test_document_analysis_extracts_uploaded_pdf_text():
    analysis = get_fraud_service().analyze_document(
        DOCUMENT_HASH,
        metadata={"expected_issuer": "Northbridge University"},
        document_bytes=DOCUMENT_BYTES,
        mime_type="application/pdf",
    )

    assert analysis["analysis_status"] == "COMPLETED"
    assert "Northbridge University" in analysis["extracted_text"]
    assert analysis["risk_level"] in {"LOW", "MEDIUM", "HIGH", "CRITICAL"}


def test_document_analysis_is_not_assessed_without_uploaded_file():
    analysis = get_fraud_service().analyze_document(DOCUMENT_HASH)

    assert analysis["analysis_status"] == "NOT_ASSESSED"
    assert analysis["authenticity_score"] is None
    assert analysis["fraud_probability"] is None
