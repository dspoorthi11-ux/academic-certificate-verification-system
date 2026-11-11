# Independent Academic Credential Verification Network

An independent service for checking academic credentials against approved issuer records, comparing uploaded document hashes, and publishing cryptographically signed verification attestations. Universities remain the original credential issuers; this platform does not award qualifications.

## Implemented trust workflow

- University accounts submit institution applications and upload supporting evidence.
- Institution approval is restricted to administrators and requires uploaded evidence plus reviewed evidence IDs.
- Only approved institutions can add issuer records. Uploaded documents are content-addressed with server-calculated SHA-256 hashes and stored outside the database.
- Public users and authenticated employers can verify by certificate ID or upload PDF/JPEG/PNG files. An ID-only lookup never asserts document integrity.
- A successful approved-issuer and hash match produces a versioned Ed25519 attestation with a public verification page, QR code, and separate PDF report.
- Public verification checks the stored signature. Student and employer views show records from authenticated APIs.
- AI analysis uses baseline document heuristics and optional OCR. It is supporting evidence, never the authenticity decision.

## Repository

- `frontend/`: React, TypeScript, Vite, React Router, Axios, Framer Motion, and Lucide.
- `backend/`: FastAPI, SQLAlchemy, JWT auth, institution trust review, certificate verification, attestation, archival evidence, and API routes.
- `blockchain/`: Solidity registry, Hardhat configuration, and contract tests.
- `backend/ai_service/`: file signature, PDF text, optional image OCR, basic metadata/layout, and issuer-name heuristics.
- `docs/`: architecture, security, database, API, blockchain, and deployment notes.

## Local development

Backend (PowerShell):

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Frontend (separate terminal):

```powershell
cd frontend
npm install
npm run dev
```

The API uses local SQLite by default for development and initializes/seeds only in development mode. Open `http://localhost:5173`; API docs are at `http://localhost:8000/docs`.

Contract checks:

```powershell
cd blockchain
npm install
npm test
```

## Production setup

1. Copy `.env.example` to `.env`; set a unique `JWT_SECRET`, `APP_ENV=production`, `BOOTSTRAP_ADMIN_EMAIL`, and `BOOTSTRAP_ADMIN_PASSWORD`.
2. Provision PostgreSQL and persistent private storage. Set `ATTESTATION_PRIVATE_KEY_PATH` to a protected Ed25519 PKCS#8 private key supplied by a secret manager; production refuses to generate a missing key.
3. Run `cd backend; alembic upgrade head` before starting the API.
4. Build and start services with `docker compose up --build`.
5. Configure HTTPS, backups, restore drills, rate limiting, monitoring, and access controls before public launch.

## Important integration limits

- Blockchain RPC health and transaction lookup are real JSON-RPC reads. Contract writes and on-chain verification are not wired to a deployed contract ABI/signer and therefore report not configured; no transaction IDs are fabricated.
- IPFS remains an adapter/mock and is not the document store for this trust workflow.
- PDF parsing is available. Image OCR needs the Tesseract executable installed and configured through `TESSERACT_PATH`; otherwise the analysis clearly reports OCR unavailable.
- The Ed25519 signature is a platform cryptographic seal, not a CCA-licensed DSC, PAdES signature, or third-party trusted timestamp. Those require an authorized provider integration and credentials.
- Local volume persistence is not an archival guarantee. Production needs encrypted backups, retention policies, key rotation procedures, and archival integrity monitoring.
- Rate limiting, provider-side e-signature integration, blockchain writes, institution external registry confirmation, QR camera scanning, and automated OCR model training remain production work.

## Environment

See `.env.example`. Never commit signing keys, bootstrap passwords, blockchain keys, or uploaded documents.
