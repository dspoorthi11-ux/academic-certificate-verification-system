from fastapi import APIRouter

from app.services.blockchain_service import get_blockchain_service

router = APIRouter(prefix="/blockchain", tags=["blockchain"])


@router.get("/status")
def blockchain_status():
    return get_blockchain_service().network_status()


@router.get("/transactions/{transaction_hash}")
def get_transaction(transaction_hash: str):
    return get_blockchain_service().get_transaction(transaction_hash)


@router.get("/certificates/{certificate_id}")
def get_certificate_record(certificate_id: str):
    return get_blockchain_service().get_certificate_record(certificate_id)