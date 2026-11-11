import hashlib
import re
import uuid
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_role
from app.core.database import get_db
from app.models.certificate import AuditLog, Certificate, CertificateDocument, Verification
from app.models.trust import InstitutionRegistry
from app.models.user import Student, University, User
from app.schemas.certificate import CertificateCreate, CertificateOut, VerificationRequest

router = APIRouter(prefix="/certificates", tags=["certificates"])
MAX_DOCUMENT_BYTES = 10 * 1024 * 1024
DOCUMENT_MIME_TYPES = {"application/pdf", "image/png", "image/jpeg"}


def _document_path(document_hash: str) -> Path:
    return Path(__file__).resolve().parents[3] / "storage" / "documents" / f"{document_hash}.bin"


def _can_access_certificate(db: Session, certificate: Certificate, user: User) -> bool:
    if user.role.name == "admin":
        return True
    if user.role.name == "university":
        issuer = db.query(University).filter(University.user_id == user.id).first()
        return bool(issuer and certificate.issuer_id == issuer.id)
    if user.role.name == "student":
        student = db.query(Student).filter(Student.user_id == user.id).first()
        return bool(student and certificate.student_id == student.id)
    return db.query(Verification).filter(
        Verification.certificate_id == certificate.id,
        Verification.verifier_id == user.id,
    ).first() is not None


@router.post("", response_model=CertificateOut, status_code=status.HTTP_201_CREATED)
async def create_certificate(
    payload: CertificateCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("university")),
):
    university = db.query(University).filter(University.user_id == current_user.id).first()
    if not university:
        raise HTTPException(status_code=400, detail="University profile not found")
    institution = db.query(InstitutionRegistry).filter(
        InstitutionRegistry.university_id == university.id,
        InstitutionRegistry.status == "APPROVED",
    ).first()
    if not institution or institution.institution_name.casefold() != payload.institution_name.casefold():
        raise HTTPException(status_code=403, detail="Only an approved institution may add issuer records")

    student_user = db.query(User).filter(User.email == (payload.student_email or "").lower()).first()
    student = db.query(Student).filter(Student.user_id == student_user.id).first() if student_user else None
    if not student:
        raise HTTPException(status_code=400, detail="Student must have an account before a certificate record can be added")
    if student_user.role.name != "student":
        raise HTTPException(status_code=400, detail="The supplied account is not a student account")
    if not re.fullmatch(r"[a-fA-F0-9]{64}", payload.document_hash):
        raise HTTPException(status_code=400, detail="A SHA-256 hash from a previous document upload is required")
    stored_document = _document_path(payload.document_hash.lower())
    if not stored_document.is_file():
        raise HTTPException(status_code=400, detail="Upload the certificate document before creating its issuer record")

    cert_id = f"CERT-{uuid.uuid4().hex[:8].upper()}"
    cert = Certificate(
        certificate_id=cert_id,
        student_id=student.id,
        issuer_id=university.id,
        certificate_type=payload.certificate_type,
        course_name=payload.course_name,
        specialization=payload.specialization,
        institution_name=payload.institution_name,
        issue_date=payload.issue_date or datetime.utcnow(),
        graduation_year=payload.graduation_year,
        document_hash=payload.document_hash,
        ipfs_hash=None,
        blockchain_transaction_hash=None,
        blockchain_network=None,
        status="ACTIVE",
        verification_url=f"/verify/{cert_id}",
        qr_data=cert_id,
    )
    db.add(cert)
    db.flush()
    db.add(CertificateDocument(
        certificate_id=cert.id,
        file_name=f"{cert_id}.bin",
        file_path=str(stored_document),
        mime_type="application/octet-stream",
        size_bytes=stored_document.stat().st_size,
        original_hash=payload.document_hash.lower(),
        is_active=True,
    ))

    db.add(AuditLog(user_id=current_user.id, action="certificate_creation", resource=cert_id, result="SUCCESS", details="Certificate created"))
    db.commit()
    db.refresh(cert)
    return cert


@router.get("", response_model=list[CertificateOut])
async def list_certificates(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.role.name == "admin":
        return db.query(Certificate).all()
    if current_user.role.name == "university":
        issuer = db.query(University).filter(University.user_id == current_user.id).first()
        return db.query(Certificate).filter(Certificate.issuer_id == issuer.id).all() if issuer else []
    if current_user.role.name == "student":
        student = db.query(Student).filter(Student.user_id == current_user.id).first()
        return db.query(Certificate).filter(Certificate.student_id == student.id).all() if student else []
    return (
        db.query(Certificate)
        .join(Verification, Verification.certificate_id == Certificate.id)
        .filter(Verification.verifier_id == current_user.id)
        .distinct()
        .all()
    )


@router.get("/{certificate_id}", response_model=CertificateOut)
async def get_certificate(certificate_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    cert = db.query(Certificate).filter(Certificate.certificate_id == certificate_id).first()
    if not cert:
        raise HTTPException(status_code=404, detail="Certificate not found")
    if not _can_access_certificate(db, cert, current_user):
        raise HTTPException(status_code=403, detail="You cannot access this certificate record")
    return cert


@router.post("/{certificate_id}/revoke")
async def revoke_certificate(certificate_id: str, db: Session = Depends(get_db), current_user: User = Depends(require_role("university"))):
    cert = db.query(Certificate).filter(Certificate.certificate_id == certificate_id).first()
    if not cert:
        raise HTTPException(status_code=404, detail="Certificate not found")
    issuer = db.query(University).filter(University.user_id == current_user.id).first()
    if issuer is None or issuer.id != cert.issuer_id:
        raise HTTPException(status_code=403, detail="Only the issuing institution can revoke this record")
    approved = db.query(InstitutionRegistry).filter(
        InstitutionRegistry.university_id == issuer.id,
        InstitutionRegistry.status == "APPROVED",
    ).first()
    if approved is None:
        raise HTTPException(status_code=403, detail="Institution is not currently approved")
    if cert.status == "REVOKED":
        raise HTTPException(status_code=409, detail="Certificate is already revoked")
    cert.status = "REVOKED"
    db.add(AuditLog(user_id=current_user.id, action="certificate_revocation", resource=certificate_id, result="SUCCESS", details="Certificate revoked"))
    db.commit()
    return {"status": "revoked", "certificate_id": certificate_id}


@router.post("/{certificate_id}/verify")
async def verify_certificate(certificate_id: str, payload: VerificationRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    from app.api.routes.verification import _run_verification
    from app.schemas.trust import PublicVerificationRequest

    # A caller-supplied hash is not evidence; only the multipart upload endpoint computes it server-side.
    return _run_verification(db, PublicVerificationRequest(certificate_id=certificate_id))


@router.post("/upload")
async def upload_certificate_document(file: UploadFile = File(...), db: Session = Depends(get_db), current_user: User = Depends(require_role("university"))):
    issuer = db.query(University).filter(University.user_id == current_user.id).first()
    institution = db.query(InstitutionRegistry).filter(
        InstitutionRegistry.university_id == issuer.id if issuer else False,
        InstitutionRegistry.status == "APPROVED",
    ).first()
    if institution is None:
        raise HTTPException(status_code=403, detail="Only approved institutions can upload issuer documents")
    if file.content_type not in DOCUMENT_MIME_TYPES:
        raise HTTPException(status_code=415, detail="Unsupported file type; upload a PDF, PNG, or JPEG")
    content = await file.read(MAX_DOCUMENT_BYTES + 1)
    if len(content) > MAX_DOCUMENT_BYTES:
        raise HTTPException(status_code=413, detail="Document exceeds the 10 MB limit")
    if not content:
        raise HTTPException(status_code=400, detail="Uploaded document is empty")
    digest = hashlib.sha256(content).hexdigest()
    path = _document_path(digest)
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_bytes(content)
    db.add(AuditLog(user_id=current_user.id, action="certificate_upload", resource=file.filename, result="SUCCESS", details=digest))
    db.commit()
    return {"status": "uploaded", "hash": digest, "filename": file.filename}
