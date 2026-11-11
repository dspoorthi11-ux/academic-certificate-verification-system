# API

FastAPI interactive docs: `/docs`. Authenticated requests use `Authorization: Bearer <access_token>`.

## Authentication
- POST /api/auth/register
- POST /api/auth/login
- GET /api/auth/me

## Certificates
- POST /api/certificates
- GET /api/certificates
- GET /api/certificates/{id}
- POST /api/certificates/{id}/revoke
- POST /api/certificates/{id}/verify
- POST /api/certificates/upload

## Verification
- POST `/api/verification/verify` (ID lookup; never authenticates without uploaded bytes)
- POST `/api/verification/verify-upload` (multipart `certificate_id` and `file`; server computes SHA-256)
- GET `/api/verification/{certificate_id}` (ID lookup)
- GET `/api/verification/history` (authenticated verifier/admin history)
- GET `/api/attestations/{verification_id}`
- GET `/api/attestations/{verification_id}/report.pdf`
- GET `/public/verify/{verification_id}`
- GET `/public/verify/{verification_id}/qr.png`

## Institutions and admin
- POST `/api/institutions/register`
- GET `/api/institutions/mine`
- POST `/api/institutions/{id}/documents` (multipart `file`)
- GET `/api/institutions/registry` (approved issuers only)
- GET `/api/institutions/applications` (admin only)
- POST `/api/institutions/{id}/review` (admin only; approval requires stored evidence IDs)
- GET `/api/institutions/{id}/documents/{document_id}` (admin only)
- GET `/api/audit` (admin only)

## Integration status
- GET `/api/blockchain/status`
- GET `/api/blockchain/transactions/{transaction_hash}`
- GET `/api/blockchain/certificates/{certificate_id}`
- GET `/api/signatures/esign/status`

## Health
- GET /health

Public verification does not return student names/emails. Platform attestations expose only certificate and issuer references needed for independent checking. File uploads are limited to PDF/JPEG/PNG, 10 MB for certificate checks and 20 MB for institution evidence.
