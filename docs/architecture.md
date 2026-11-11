# Architecture

The platform is an independent verification service. Universities remain the original credential issuers. The application stores issuer records and verification evidence; it does not award or replace academic qualifications.

## Trust boundaries

- Public web app: landing, ID/file verification, and independently checkable attestation pages.
- FastAPI: authenticated institution, student, employer, and administrator workflows.
- PostgreSQL/SQLAlchemy: institution applications and decisions, issuer records, verification history, signatures, archival evidence, and audit records.
- Private document storage: uploaded original files keyed by server-computed SHA-256. Do not store private student data on a public chain.
- Ed25519 signer: platform-only signature key stored outside source and frontend. Each attestation retains its public key and key identifier.
- AI service: heuristic document risk cues. It cannot authenticate or reject a credential on its own.
- Blockchain adapter: real JSON-RPC health and transaction reads; contract writes and certificate lookups remain unavailable until a deployed ABI/address and protected signer are configured.

## Verification flow

1. Institution application and evidence are submitted.
2. Administrator reviews the real evidence files and approves, rejects, or suspends the issuer.
3. Approved institution adds a certificate issuer record after uploading its original document; the backend calculates SHA-256.
4. Public or employer user submits a certificate ID and optional document upload.
5. Backend compares the uploaded document SHA-256 with the stored issuer record and checks revocation.
6. File heuristics may add risk cues; they are not decisive evidence.
7. An exact issuer/hash match creates a canonical versioned attestation, signs it with Ed25519, and archives the payload/evidence.
8. QR links to the public SPA route, which fetches the attestation and independently validates its stored signature.

An ID-only lookup can find a record but cannot assert document integrity or create an attestation. No blockchain confirmation or trusted timestamp is claimed unless independently integrated.
