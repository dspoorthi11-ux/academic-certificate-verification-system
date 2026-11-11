from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from app.api.routes.auth import router as auth_router
from app.api.routes.audit import router as audit_router
from app.api.routes.blockchain import router as blockchain_router
from app.api.routes.certificates import router as certificate_router
from app.api.routes.institutions import router as institution_router
from app.api.routes.signatures import router as signature_router
from app.api.routes.verification import (
    attestation_router,
    public_router,
    router as verification_router,
)
from app.core.config import get_settings
from app.core.database import SessionLocal, init_db
from app.core.seed import seed_demo_data
from app.models import trust as trust_models

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    if settings.app_env.lower() == "development":
        init_db()
    db: Session = SessionLocal()
    try:
        seed_demo_data(db)
    finally:
        db.close()
    yield


app = FastAPI(title="Certificate Verification Platform", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in settings.cors_origins.split(",") if origin.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/api")
app.include_router(audit_router, prefix="/api")
app.include_router(blockchain_router, prefix="/api")
app.include_router(certificate_router, prefix="/api")
app.include_router(institution_router, prefix="/api")
app.include_router(signature_router, prefix="/api")
app.include_router(verification_router, prefix="/api")
app.include_router(attestation_router, prefix="/api")
app.include_router(public_router)


@app.get("/health")
async def health_check():
    return {"status": "ok"}


@app.get("/")
async def root():
    return {"message": "Certificate Verification Platform API"}
