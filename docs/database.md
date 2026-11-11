# Database design

The system uses SQLAlchemy with Alembic migrations for users, roles, universities, students, certificates, documents, blockchain records, verification history, AI analysis outputs, audit logs, institution trust review, signed attestations, and archival evidence.

## Core entities
- User
- Role
- University
- Student
- Certificate
- CertificateDocument
- BlockchainRecord
- Verification
- AuditLog
- FraudAnalysis
- InstitutionRegistry
- InstitutionVerification
- VerificationAttestation
- DigitalSignature
- VerificationArchive
- BlockchainTransaction
- VerificationRequestRecord

The `20261029_core` baseline creates missing core tables idempotently for pre-Alembic installations. `20261030_trust` adds the trust and attestation tables. Run `alembic upgrade head` before production startup. Existing records are preserved; the baseline migration is intentionally irreversible.

Document bytes are stored in the private storage volume, not in PostgreSQL. Attestation payloads and public keys are persisted to support signature revalidation and archival evidence checks. Public blockchain records must only contain hashes and minimal references.
