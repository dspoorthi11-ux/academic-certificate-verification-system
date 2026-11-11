import hashlib
import json
import uuid
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_role
from app.core.database import get_db
from app.models.certificate import AuditLog
from app.models.trust import InstitutionRegistry, InstitutionVerification
from app.models.user import University, User
from app.schemas.trust import InstitutionRegistration, InstitutionReview

router = APIRouter(prefix="/institutions", tags=["institutions"])
MAX_EVIDENCE_BYTES = 20 * 1024 * 1024
EVIDENCE_MIME_TYPES = {"application/pdf", "image/jpeg", "image/png"}


def _institution_view(institution: InstitutionRegistry, public: bool = False) -> dict:
    result = {
        "id": institution.id,
        "institution_name": institution.institution_name,
        "institution_type": institution.institution_type,
        "website": institution.website,
        "country": institution.country,
        "domain_candidate": institution.domain_candidate,
        "status": institution.status,
        "approved_at": institution.approved_at,
        "created_at": institution.created_at,
    }
    if not public:
        result.update({
            "user_id": institution.user_id,
            "university_id": institution.university_id,
            "official_email": institution.official_email,
            "state": institution.state,
            "address": institution.address,
            "accreditation": institution.accreditation,
            "representative_name": institution.representative_name,
            "representative_designation": institution.representative_designation,
            "contact_number": institution.contact_number,
            "supporting_documents": json.loads(institution.supporting_documents),
            "institution_public_key": institution.institution_public_key,
            "decision_notes": institution.decision_notes,
        })
    return result


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register_institution(
    payload: InstitutionRegistration,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role.name != "university":
        raise HTTPException(status_code=403, detail="Only university accounts can submit institution applications")
    if db.query(InstitutionRegistry).filter(
        InstitutionRegistry.official_email == payload.official_email.lower(),
    ).first():
        raise HTTPException(status_code=409, detail="An application already exists for this official email")

    website_domain = (urlparse(str(payload.website)).hostname or "").lower().removeprefix("www.")
    email_domain = payload.official_email.split("@", 1)[-1].lower()
    university = db.query(University).filter(University.user_id == current_user.id).first()
    if university is None:
        university = University(
            user_id=current_user.id,
            name=payload.institution_name,
            country=payload.country,
            website=str(payload.website),
        )
        db.add(university)
        db.flush()

    institution = InstitutionRegistry(
        user_id=current_user.id,
        university_id=university.id,
        institution_name=payload.institution_name,
        institution_type=payload.institution_type,
        official_email=payload.official_email.lower(),
        website=str(payload.website),
        country=payload.country,
        state=payload.state,
        address=payload.address,
        accreditation=payload.accreditation,
        representative_name=payload.representative_name,
        representative_designation=payload.representative_designation,
        contact_number=payload.contact_number,
        supporting_documents="[]",
        domain_candidate=website_domain if email_domain == website_domain or email_domain.endswith(f".{website_domain}") else "DOMAIN_MISMATCH",
        institution_public_key=payload.institution_public_key,
        status="PENDING",
    )
    db.add(institution)
    db.flush()
    db.add(AuditLog(
        user_id=current_user.id,
        action="institution_registration",
        resource=institution.id,
        result="PENDING_REVIEW",
        details="Institution application submitted; no issuer trust granted.",
    ))
    db.commit()
    db.refresh(institution)
    return _institution_view(institution)


@router.get("/mine")
def get_my_institution_application(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    institution = (
        db.query(InstitutionRegistry)
        .filter(InstitutionRegistry.user_id == current_user.id)
        .order_by(InstitutionRegistry.created_at.desc())
        .first()
    )
    if institution is None:
        raise HTTPException(status_code=404, detail="No institution application found")
    return _institution_view(institution)


@router.get("/registry")
def list_public_registry(db: Session = Depends(get_db)):
    institutions = (
        db.query(InstitutionRegistry)
        .filter(InstitutionRegistry.status == "APPROVED")
        .order_by(InstitutionRegistry.institution_name.asc())
        .all()
    )
    return [_institution_view(item, public=True) for item in institutions]


@router.get("/applications")
def list_institution_applications(
    db: Session = Depends(get_db),
    _admin: User = Depends(require_role("admin")),
):
    institutions = db.query(InstitutionRegistry).order_by(InstitutionRegistry.created_at.desc()).all()
    return [_institution_view(item) for item in institutions]


@router.post("/{institution_id}/documents", status_code=status.HTTP_201_CREATED)
async def upload_institution_evidence(
    institution_id: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    institution = db.query(InstitutionRegistry).filter(InstitutionRegistry.id == institution_id).first()
    if institution is None:
        raise HTTPException(status_code=404, detail="Institution application not found")
    if institution.user_id != current_user.id and current_user.role.name != "admin":
        raise HTTPException(status_code=403, detail="You cannot upload evidence for this institution")
    if institution.status != "PENDING" and current_user.role.name != "admin":
        raise HTTPException(status_code=409, detail="Evidence can only be added to a pending application")
    if file.content_type not in EVIDENCE_MIME_TYPES:
        raise HTTPException(status_code=415, detail="Evidence must be a PDF, JPEG, or PNG")

    content = await file.read(MAX_EVIDENCE_BYTES + 1)
    if not content:
        raise HTTPException(status_code=400, detail="Evidence file is empty")
    if len(content) > MAX_EVIDENCE_BYTES:
        raise HTTPException(status_code=413, detail="Evidence file exceeds the 20 MB limit")

    document_id = uuid.uuid4().hex
    digest = hashlib.sha256(content).hexdigest()
    storage_dir = Path(__file__).resolve().parents[3] / "storage" / "institution-documents"
    storage_dir.mkdir(parents=True, exist_ok=True)
    (storage_dir / f"{document_id}.bin").write_bytes(content)
    records = json.loads(institution.supporting_documents)
    records.append({
        "id": document_id,
        "name": Path(file.filename or "evidence").name,
        "sha256": digest,
        "mime_type": file.content_type,
    })
    institution.supporting_documents = json.dumps(records)
    db.add(AuditLog(
        user_id=current_user.id,
        action="institution_evidence_upload",
        resource=institution.id,
        result="SUCCESS",
        details=f"Evidence SHA-256: {digest}",
    ))
    db.commit()
    return {"document_id": document_id, "file_name": Path(file.filename or "evidence").name, "sha256": digest}


@router.get("/{institution_id}/documents/{document_id}")
def download_institution_evidence(
    institution_id: str,
    document_id: str,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_role("admin")),
):
    institution = db.query(InstitutionRegistry).filter(InstitutionRegistry.id == institution_id).first()
    if institution is None:
        raise HTTPException(status_code=404, detail="Institution application not found")
    records = json.loads(institution.supporting_documents)
    evidence = next((item for item in records if item.get("id") == document_id), None)
    if evidence is None:
        raise HTTPException(status_code=404, detail="Evidence document not found")
    path = Path(__file__).resolve().parents[3] / "storage" / "institution-documents" / f"{document_id}.bin"
    if not path.is_file():
        raise HTTPException(status_code=404, detail="Evidence document is unavailable")
    return FileResponse(path, media_type=evidence["mime_type"], filename=evidence["name"])


@router.post("/{institution_id}/review")
def review_institution(
    institution_id: str,
    payload: InstitutionReview,
    db: Session = Depends(get_db),
    admin: User = Depends(require_role("admin")),
):
    institution = db.query(InstitutionRegistry).filter(InstitutionRegistry.id == institution_id).first()
    if institution is None:
        raise HTTPException(status_code=404, detail="Institution application not found")
    if payload.status == "APPROVED" and institution.domain_candidate == "DOMAIN_MISMATCH":
        raise HTTPException(status_code=400, detail="Official email domain must match the institution website before approval")
    if payload.status == "APPROVED" and not json.loads(institution.supporting_documents):
        raise HTTPException(status_code=400, detail="At least one uploaded supporting document must be reviewed before approval")
    stored_evidence_ids = {
        evidence.get("id")
        for evidence in json.loads(institution.supporting_documents)
        if isinstance(evidence, dict)
    }
    if payload.status == "APPROVED" and (
        not payload.evidence_reviewed
        or not set(payload.evidence_reviewed).issubset(stored_evidence_ids)
    ):
        raise HTTPException(status_code=400, detail="Approval must reference uploaded evidence document IDs")

    previous_status = institution.status
    institution.status = payload.status
    institution.approved_by = admin.id if payload.status == "APPROVED" else None
    institution.approved_at = datetime.utcnow() if payload.status == "APPROVED" else None
    institution.decision_notes = payload.notes
    db.add(InstitutionVerification(
        institution_id=institution.id,
        admin_user_id=admin.id,
        previous_status=previous_status,
        new_status=payload.status,
        evidence_reviewed=json.dumps(payload.evidence_reviewed),
        notes=payload.notes,
    ))
    db.add(AuditLog(
        user_id=admin.id,
        action="institution_status_change",
        resource=institution.id,
        result=payload.status,
        details=payload.notes or "Institution status updated by administrator.",
    ))
    db.commit()
    db.refresh(institution)
    return _institution_view(institution)