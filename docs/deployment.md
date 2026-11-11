# Deployment

The repository includes Dockerfiles for the API, frontend, and local Hardhat node. Production must use PostgreSQL, a protected Ed25519 key, HTTPS, persistent document storage, and a configured secret manager.

## Docker

```bash
cp .env.example .env
# Set JWT_SECRET, BOOTSTRAP_ADMIN_EMAIL, BOOTSTRAP_ADMIN_PASSWORD, and production settings.
cd backend
alembic upgrade head
cd ..
docker compose up --build
```

The API container does not auto-create schema in production mode. Run migrations before starting it. The Docker named volume `backend_storage` holds local signing key material and document/archive files; configure encrypted backups and restore testing separately. A mounted named volume is not itself a long-term archival policy.

## Manual

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

cd frontend
npm install
npm run dev -- --host 0.0.0.0
```

For image OCR, install the Tesseract executable in the runtime image and set `TESSERACT_PATH`. It is optional; the API reports when OCR was unavailable.

## Production prerequisites

- Set a unique `JWT_SECRET`; bootstrap the administrator only through protected environment variables.
- Provision the signing key externally and point `ATTESTATION_PRIVATE_KEY_PATH` to it. Never bake private signing material into an image.
- Configure institutional validation sources, rate limiting, monitoring, data retention and access controls.
- Blockchain writes require a deployed contract, ABI, authorized signer, and chain monitoring. Electronic signatures require a CCA-authorized provider. Neither is simulated by this repository.
