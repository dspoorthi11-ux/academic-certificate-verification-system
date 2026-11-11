from datetime import datetime, timedelta

from sqlalchemy.orm import Session

import os

from app.models.certificate import AuditLog, Certificate, CertificateDocument, FraudAnalysis, Verification
from app.core.security import hash_password
from app.models.user import Role, Student, University, User, Verifier


def seed_demo_data(db: Session) -> None:
    roles = {
        role.name: role
        for role in db.query(Role).filter(Role.name.in_(["university", "student", "verifier", "admin"])).all()
    }
    for role_name, description in [
        ("university", "Institution account; subject to independent approval"),
        ("student", "Student user"),
        ("verifier", "Employer or verifier user"),
        ("admin", "Platform administrator"),
    ]:
        if role_name not in roles:
            role = Role(name=role_name, description=description)
            db.add(role)
            roles[role_name] = role
    db.commit()

    admin_email = os.getenv("BOOTSTRAP_ADMIN_EMAIL", "").strip().lower()
    admin_password = os.getenv("BOOTSTRAP_ADMIN_PASSWORD", "")
    if admin_email and admin_password and not db.query(User).filter(User.email == admin_email).first():
        db.add(User(
            email=admin_email,
            full_name="Platform Administrator",
            password_hash=hash_password(admin_password),
            role_id=roles["admin"].id,
            is_active=True,
        ))
        db.commit()

    if os.getenv("APP_ENV", "development").lower() != "development":
        return

    if db.query(User).count() > 0:
        return

    university_role = roles["university"]
    student_role = roles["student"]
    verifier_role = roles["verifier"]

    user_map = {}
    for email, name, role in [
        ("university@example.com", "Northbridge University", university_role),
        ("student@example.com", "Alice Johnson", student_role),
        ("verifier@example.com", "Mark Taylor", verifier_role),
    ]:
        user = User(email=email, full_name=name, password_hash="$2b$12$3I0U7G7hCwc1D4y1/CC8pOo2Bbs0l7u19kqe/3xkOp2uyuSXl2XlS", role_id=role.id)
        db.add(user)
        db.flush()
        user_map[email] = user

    university = University(user_id=user_map["university@example.com"].id, name="Northbridge University", country="USA", website="https://northbridge.edu")
    student = Student(user_id=user_map["student@example.com"].id, student_number="STU-1001", program="Computer Science", university_name="Northbridge University")
    verifier = Verifier(user_id=user_map["verifier@example.com"].id, company_name="Apex HR", department="Talent Acquisition")
    db.add_all([university, student, verifier])
    db.commit()

    certificate_1 = Certificate(
        certificate_id="CERT-1001",
        student_id=student.id,
        issuer_id=university.id,
        certificate_type="Bachelor of Science",
        course_name="Computer Science",
        specialization="Software Engineering",
        institution_name="Northbridge University",
        issue_date=datetime.utcnow() - timedelta(days=220),
        graduation_year=2024,
        document_hash="abc123hash",
        ipfs_hash="QmSampleHash1",
        blockchain_transaction_hash="0xabc1",
        blockchain_network="hardhat",
        status="ACTIVE",
        verification_url="/verify/CERT-1001",
        qr_data="CERT-1001",
    )
    db.add(certificate_1)
    db.flush()

    db.add(CertificateDocument(
        certificate_id=certificate_1.id,
        file_name="grad_certificate.pdf",
        file_path="/tmp/grad_certificate.pdf",
        mime_type="application/pdf",
        size_bytes=120000,
        original_hash="abc123hash",
        ipfs_hash="QmSampleHash1",
        is_active=True,
    ))
    db.add(FraudAnalysis(
        certificate_id=certificate_1.id,
        authenticity_score=97.8,
        fraud_probability=0.04,
        risk_level="LOW",
        detected_anomalies="No critical anomalies detected",
        extracted_text="Northbridge University Computer Science",
        explanation="Document structure and hash match expected baseline.",
    ))
    db.add(Verification(
        certificate_id=certificate_1.id,
        verifier_id=verifier.user_id,
        status="COMPLETED",
        result="AUTHENTIC",
        notes="Verified successfully",
        ai_score=97.8,
    ))
    db.add(AuditLog(user_id=user_map["university@example.com"].id, action="certificate_creation", resource="CERT-1001", result="SUCCESS", details="Demo certificate issued"))
    db.commit()
