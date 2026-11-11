import hashlib
import io
import json
import uuid
from datetime import datetime
from pathlib import Path
from urllib.parse import quote
from xml.sax.saxutils import escape

import qrcode
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import Response, StreamingResponse
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Image, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from reportlab.lib.pagesizes import letter
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas
from pypdf import PdfReader, PdfWriter
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import get_db
from app.api.deps import get_optional_current_user
from app.models.certificate import AuditLog, Certificate, FraudAnalysis, Verification
from app.models.trust import (
    DigitalSignature,
    InstitutionRegistry,
    VerificationArchive,
    VerificationAttestation,
)
from app.models.user import University, User
from app.schemas.trust import PublicVerificationRequest
from app.services.attestation_signing import AttestationSigner, get_attestation_signer
from ai_service.fraud_detection import get_fraud_service

router = APIRouter(prefix="/verification", tags=["verification"])
attestation_router = APIRouter(prefix="/attestations", tags=["attestations"])
public_router = APIRouter(tags=["public verification"])
settings = get_settings()
MAX_UPLOAD_BYTES = 10 * 1024 * 1024
ALLOWED_MIME_TYPES = {"application/pdf", "image/jpeg", "image/png"}


def _approved_issuer(db: Session, certificate: Certificate) -> InstitutionRegistry | None:
    university = db.query(University).filter(University.id == certificate.issuer_id).first()
    if university is None:
        return None
    institution = (
        db.query(InstitutionRegistry)
        .filter(
            InstitutionRegistry.university_id == university.id,
            InstitutionRegistry.status == "APPROVED",
        )
        .first()
    )
    if institution is None or institution.institution_name.casefold() != certificate.institution_name.casefold():
        return None
    return institution


def _new_attestation(
    db: Session,
    verification: Verification,
    certificate: Certificate,
    institution: InstitutionRegistry,
) -> VerificationAttestation:
    verified_at = datetime.utcnow()
    public_id = f"VER-{verified_at.year}-{uuid.uuid4().hex[:12].upper()}"
    blockchain_status = "REFERENCE_STORED" if certificate.blockchain_transaction_hash else "NOT_CONFIRMED"
    payload = {
        "verification_id": public_id,
        "certificate_id": certificate.certificate_id,
        "document_sha256": certificate.document_hash.lower(),
        "institution": institution.institution_name,
        "institution_registry_id": institution.id,
        "result": "AUTHENTIC",
        "document_integrity": "MATCHED",
        "issuer_authentication": "CONFIRMED_BY_APPROVED_REGISTRY",
        "blockchain_status": blockchain_status,
        "blockchain_reference": certificate.blockchain_transaction_hash,
        "verified_at": verified_at.isoformat(timespec="seconds") + "Z",
        "timestamp_type": "PLATFORM_SERVER_TIME",
        "methodology": "Approved issuer registry lookup, certificate record lookup, and uploaded SHA-256 comparison.",
        "platform": "Independent Academic Credential Verification Network",
        "attestation_version": 1,
        "signature_algorithm": "Ed25519",
    }
    signer = get_attestation_signer()
    signature, public_key, key_id = signer.sign(payload)
    attestation = VerificationAttestation(
        public_id=public_id,
        verification_id=verification.id,
        certificate_id=certificate.certificate_id,
        document_hash=certificate.document_hash.lower(),
        institution_name=institution.institution_name,
        result="AUTHENTIC",
        verified_at=verified_at,
        methodology=payload["methodology"],
        issuer_confirmation_reference=f"registry:{institution.id};certificate:{certificate.id}",
        blockchain_reference=certificate.blockchain_transaction_hash,
        platform_identity=payload["platform"],
        version=1,
        key_id=key_id,
        public_key=public_key,
        signature=signature,
        payload=json.dumps(payload, sort_keys=True, separators=(",", ":")),
    )
    db.add(attestation)
    db.flush()
    db.add(DigitalSignature(
        attestation_id=attestation.id,
        algorithm="Ed25519",
        key_id=key_id,
        public_key=public_key,
        signature=signature,
        signed_at=verified_at,
    ))
    db.add(VerificationArchive(
        attestation_id=attestation.id,
        document_hash=certificate.document_hash.lower(),
        evidence_json=json.dumps({
            "payload": payload,
            "public_key": public_key,
            "signature": signature,
            "key_id": key_id,
            "algorithm": "Ed25519",
        }, sort_keys=True),
    ))
    return attestation


def _ai_summary(fraud: dict) -> dict:
    authenticity_score = fraud.get("authenticity_score")
    return {
        "analysis_status": fraud.get("analysis_status", "NOT_ASSESSED"),
        "role": "SUPPORTING_RISK_ASSESSMENT_ONLY",
        "risk_score": round(100 - float(authenticity_score), 2) if authenticity_score is not None else None,
        "fraud_probability": fraud.get("fraud_probability"),
        "risk_category": fraud.get("risk_level"),
        "detected_anomalies": fraud.get("detected_anomalies", []),
        "explanation": fraud.get("explanation"),
        "recommended_action": fraud.get("recommended_action"),
    }


def _run_verification(
    db: Session,
    payload: PublicVerificationRequest,
    original_document: bytes | None = None,
    mime_type: str | None = None,
    verifier: User | None = None,
) -> dict:
    certificate = db.query(Certificate).filter(Certificate.certificate_id == payload.certificate_id).first()
    if certificate is None:
        uploaded_document_hash = hashlib.sha256(original_document).hexdigest() if original_document else ""
        fraud = get_fraud_service().analyze_document(
            uploaded_document_hash,
            metadata={},
            document_bytes=original_document,
            mime_type=mime_type,
        )
        message = "Unable to independently authenticate this certificate: no trusted issuer record was found."
        db.add(AuditLog(
            user_id=verifier.id if verifier else None,
            action="public_certificate_verification",
            resource=payload.certificate_id,
            result="UNABLE_TO_AUTHENTICATE",
            details=message,
        ))
        db.commit()
        return {
            "certificate_id": payload.certificate_id,
            "result": "UNABLE_TO_AUTHENTICATE",
            "message": message,
            "institution": None,
            "issuer_authentication": "UNCONFIRMED",
            "document_integrity": "NOT_CHECKED",
            "blockchain_status": "NOT_CONFIRMED",
            "blockchain_reference": None,
            "ai_analysis": _ai_summary(fraud),
            "attestation": None,
        }

    institution = _approved_issuer(db, certificate)
    uploaded_hash = hashlib.sha256(original_document).hexdigest() if original_document else None
    fraud = get_fraud_service().analyze_document(
        certificate.document_hash,
        metadata={"expected_issuer": institution.institution_name if institution else None},
        document_bytes=original_document,
        mime_type=mime_type,
    )

    result = "UNABLE_TO_AUTHENTICATE"
    message = "Unable to independently authenticate this certificate."
    attestation = None
    if institution is None:
        message = "Unable to independently authenticate this certificate: issuer is not in the approved registry."
    elif certificate.status == "REVOKED":
        result = "REVOKED"
        message = "The approved issuer record shows that this certificate has been revoked."
    elif certificate.status != "ACTIVE":
        result = "UNABLE_TO_AUTHENTICATE"
        message = "The issuer record is not active and cannot be independently authenticated."
    elif uploaded_hash is None:
        result = "DOCUMENT_REQUIRED"
        message = "An approved issuer record exists. Upload the document to compare its SHA-256 hash."
    elif uploaded_hash != certificate.document_hash.lower():
        result = "TAMPERED"
        message = "The uploaded document hash does not match the approved issuer record."
    else:
        result = "AUTHENTIC"
        message = "The approved issuer record and uploaded document hash match. AI analysis is supporting evidence only."

    verification = Verification(
        certificate_id=certificate.id,
        verifier_id=verifier.id if verifier else None,
        status="COMPLETED",
        result=result,
        notes=message,
        ai_score=fraud.get("authenticity_score"),
    )
    db.add(verification)
    db.add(FraudAnalysis(
        certificate_id=certificate.id,
        authenticity_score=float(fraud["authenticity_score"] or 0),
        fraud_probability=float(fraud["fraud_probability"] or 0),
        risk_level=str(fraud.get("risk_level", "NOT_ASSESSED")),
        detected_anomalies=json.dumps(fraud.get("detected_anomalies", [])),
        explanation=fraud.get("explanation"),
    ))
    db.flush()

    if result == "AUTHENTIC" and institution is not None:
        attestation = _new_attestation(db, verification, certificate, institution)
        db.add(AuditLog(
            user_id=verifier.id if verifier else None,
            action="attestation_signature",
            resource=attestation.public_id,
            result="SIGNED",
            details=f"Ed25519 platform seal; key id {attestation.key_id}",
        ))
        if original_document is not None:
            archive_dir = Path(__file__).resolve().parents[3] / "storage" / "documents"
            archive_dir.mkdir(parents=True, exist_ok=True)
            archived_path = archive_dir / f"{certificate.document_hash.lower()}.bin"
            if not archived_path.exists():
                archived_path.write_bytes(original_document)
            db.flush()
            db.query(VerificationArchive).filter(
                VerificationArchive.attestation_id == attestation.id,
            ).update({"original_document_path": str(archived_path)})

    db.add(AuditLog(
        user_id=verifier.id if verifier else None,
        action="public_certificate_verification",
        resource=certificate.certificate_id,
        result=result,
        details=message,
    ))
    db.commit()

    response = {
        "certificate_id": certificate.certificate_id,
        "result": result,
        "message": message,
        "institution": institution.institution_name if institution else None,
        "issuer_authentication": "CONFIRMED" if institution else "UNCONFIRMED",
        "document_integrity": "MATCHED" if uploaded_hash and uploaded_hash == certificate.document_hash.lower() else "NOT_MATCHED_OR_NOT_CHECKED",
        "blockchain_status": "REFERENCE_STORED_NOT_INDEPENDENTLY_CHECKED" if certificate.blockchain_transaction_hash else "NOT_CONFIRMED",
        "blockchain_reference": certificate.blockchain_transaction_hash,
        "ai_analysis": _ai_summary(fraud),
        "attestation": None,
    }
    if attestation:
        response["attestation"] = {
            "verification_id": attestation.public_id,
            "public_url": f"{settings.frontend_url}/public/verify/{quote(attestation.public_id)}",
            "signature_algorithm": "Ed25519",
            "key_id": attestation.key_id,
        }
    return response


@router.post("/verify")
def verify_by_id(
    payload: PublicVerificationRequest,
    db: Session = Depends(get_db),
    verifier: User | None = Depends(get_optional_current_user),
):
    return _run_verification(db, payload, verifier=verifier)


@router.post("/verify-upload")
async def verify_uploaded_document(
    certificate_id: str = Form(..., min_length=3, max_length=100),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    verifier: User | None = Depends(get_optional_current_user),
):
    if file.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(status_code=415, detail="Only PDF, JPEG, and PNG documents are accepted")
    content = await file.read(MAX_UPLOAD_BYTES + 1)
    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="Document exceeds the 10 MB limit")
    if not content:
        raise HTTPException(status_code=400, detail="Uploaded document is empty")
    return _run_verification(
        db,
        PublicVerificationRequest(certificate_id=certificate_id),
        original_document=content,
        mime_type=file.content_type,
        verifier=verifier,
    )


@router.get("/history")
def verification_history(
    db: Session = Depends(get_db),
    verifier: User = Depends(get_optional_current_user),
):
    if verifier is None:
        raise HTTPException(status_code=401, detail="Authentication required")
    if verifier.role.name not in {"verifier", "admin"}:
        raise HTTPException(status_code=403, detail="Verifier access required")
    records = (
        db.query(Verification, Certificate)
        .join(Certificate, Verification.certificate_id == Certificate.id)
        .filter(Verification.verifier_id == verifier.id)
        .order_by(Verification.verification_timestamp.desc())
        .all()
    )
    return [{
        "verification_id": record.id,
        "certificate_id": certificate.certificate_id,
        "result": record.result,
        "status": record.status,
        "checked_at": record.verification_timestamp,
        "ai_score": record.ai_score,
    } for record, certificate in records]


@router.get("/{certificate_id}")
def get_verification_record(certificate_id: str, db: Session = Depends(get_db)):
    return _run_verification(db, PublicVerificationRequest(certificate_id=certificate_id))


@public_router.get("/public/verify/{public_id}")
def public_verify_attestation(public_id: str, db: Session = Depends(get_db)):
    attestation = db.query(VerificationAttestation).filter(
        VerificationAttestation.public_id == public_id,
    ).first()
    if attestation is None:
        raise HTTPException(status_code=404, detail="Verification attestation not found")
    payload = json.loads(attestation.payload)
    signature_valid = AttestationSigner.verify(payload, attestation.signature, attestation.public_key)
    return {
        "verification_id": attestation.public_id,
        "certificate_id": attestation.certificate_id,
        "institution": attestation.institution_name,
        "result": attestation.result if signature_valid else "SIGNATURE_INVALID",
        "document_sha256": attestation.document_hash,
        "verified_at": attestation.verified_at,
        "document_integrity": payload.get("document_integrity"),
        "issuer_authentication": payload.get("issuer_authentication"),
        "blockchain_status": payload.get("blockchain_status"),
        "blockchain_reference": attestation.blockchain_reference,
        "signature": {
            "algorithm": "Ed25519",
            "key_id": attestation.key_id,
            "valid": signature_valid,
            "public_key": attestation.public_key,
        },
        "methodology": attestation.methodology,
        "platform": attestation.platform_identity,
    }


@public_router.get("/public/verify/{public_id}/qr.png")
def attestation_qr(public_id: str, db: Session = Depends(get_db)):
    attestation = db.query(VerificationAttestation).filter(
        VerificationAttestation.public_id == public_id,
    ).first()
    if attestation is None:
        raise HTTPException(status_code=404, detail="Verification attestation not found")
    image = qrcode.make(f"{settings.frontend_url}/public/verify/{public_id}")
    image_buffer = io.BytesIO()
    image.save(image_buffer, format="PNG")
    return Response(content=image_buffer.getvalue(), media_type="image/png")


@attestation_router.get("/{public_id}")
def get_attestation(public_id: str, db: Session = Depends(get_db)):
    return public_verify_attestation(public_id, db)


@attestation_router.get("/{public_id}/report.pdf")
def download_attestation_report(public_id: str, db: Session = Depends(get_db)):
    public_data = public_verify_attestation(public_id, db)
    buffer = io.BytesIO()
    document = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=20 * mm, leftMargin=20 * mm, topMargin=18 * mm, bottomMargin=18 * mm)
    styles = getSampleStyleSheet()
    story = [
        Paragraph("Independent Academic Credential Verification Report", styles["Title"]),
        Spacer(1, 8 * mm),
        Paragraph("This report is an independent platform attestation. It is not the university-issued academic certificate and is not a legally recognized electronic signature.", styles["BodyText"]),
        Spacer(1, 6 * mm),
    ]
    rows = [
        ["Verification ID", public_data["verification_id"]],
        ["Result", public_data["result"]],
        ["Institution", public_data["institution"]],
        ["Certificate ID", public_data["certificate_id"]],
        ["Original document SHA-256", public_data["document_sha256"]],
        ["Verified at (platform time)", str(public_data["verified_at"])],
        ["Document integrity", public_data["document_integrity"]],
        ["Issuer authentication", public_data["issuer_authentication"]],
        ["Blockchain", public_data["blockchain_status"]],
        ["Blockchain reference", public_data["blockchain_reference"] or "Not confirmed"],
        ["Signature", f"Ed25519 / {public_data['signature']['key_id']} / {'VALID' if public_data['signature']['valid'] else 'INVALID'}"],
    ]
    table = Table([[escape(str(left)), escape(str(right or ""))] for left, right in rows], colWidths=[48 * mm, 115 * mm])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#e8f4fa")),
        ("TEXTCOLOR", (0, 0), (-1, -1), colors.HexColor("#102b3c")),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#b9d1dc")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
    ]))
    story.extend([table, Spacer(1, 8 * mm), Paragraph("Methodology", styles["Heading2"]), Paragraph(escape(public_data["methodology"]), styles["BodyText"]), Spacer(1, 5 * mm)])
    qr_buffer = io.BytesIO()
    qrcode.make(f"{settings.frontend_url}/public/verify/{public_id}").save(qr_buffer, format="PNG")
    qr_buffer.seek(0)
    story.append(Image(qr_buffer, width=35 * mm, height=35 * mm))
    story.append(Spacer(1, 4 * mm))
    story.append(Paragraph("The original file is preserved unchanged and included before these report pages in this generated copy. Platform server time is not a third-party trusted timestamp. Blockchain status is reported only as stored evidence unless independently confirmed.", styles["BodyText"]))
    document.build(story)

    attestation_record = db.query(VerificationAttestation).filter(
        VerificationAttestation.public_id == public_id,
    ).first()
    archive = db.query(VerificationArchive).filter(
        VerificationArchive.attestation_id == attestation_record.id,
    ).first() if attestation_record else None
    if archive and archive.original_document_path and Path(archive.original_document_path).is_file():
        original_bytes = Path(archive.original_document_path).read_bytes()
        original_reader = None
        if original_bytes.startswith(b"%PDF-"):
            original_reader = PdfReader(io.BytesIO(original_bytes), strict=False)
        else:
            image_pdf = io.BytesIO()
            page = canvas.Canvas(image_pdf, pagesize=letter)
            image = ImageReader(io.BytesIO(original_bytes))
            image_width, image_height = image.getSize()
            scale = min((letter[0] - 48) / image_width, (letter[1] - 48) / image_height)
            drawn_width, drawn_height = image_width * scale, image_height * scale
            page.drawImage(image, (letter[0] - drawn_width) / 2, (letter[1] - drawn_height) / 2, drawn_width, drawn_height, preserveAspectRatio=True)
            page.save()
            original_reader = PdfReader(image_pdf)

        report_reader = PdfReader(buffer)
        writer = PdfWriter()
        for source_page in original_reader.pages:
            writer.add_page(source_page)
        for report_page in report_reader.pages:
            writer.add_page(report_page)
        combined = io.BytesIO()
        writer.write(combined)
        buffer = combined

    buffer.seek(0)
    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{public_id}-verification-report.pdf"'},
    )
