from fastapi import APIRouter

from app.services.esign_provider import get_esign_provider

router = APIRouter(prefix="/signatures", tags=["signatures"])


@router.get("/esign/status")
async def esign_provider_status():
    provider = get_esign_provider()
    validation = await provider.validate_signed_pdf(b"")
    return {
        "provider": provider.provider_name,
        "configured": validation["configured"],
        "legal_signature_available": validation["configured"],
        "message": validation["reason"],
    }