from typing import Any

import httpx

from app.core.config import get_settings

settings = get_settings()


class BlockchainService:
    def __init__(self, rpc_url: str | None = None) -> None:
        self.rpc_url = rpc_url or settings.blockchain_rpc_url

    def _rpc(self, method: str, params: list[Any] | None = None) -> Any:
        response = httpx.post(
            self.rpc_url,
            json={"jsonrpc": "2.0", "method": method, "params": params or [], "id": 1},
            timeout=8,
        )
        response.raise_for_status()
        body = response.json()
        if "error" in body:
            raise RuntimeError(body["error"].get("message", "JSON-RPC request failed"))
        return body.get("result")

    def network_status(self) -> dict[str, Any]:
        try:
            chain_id = self._rpc("eth_chainId")
            block_number = self._rpc("eth_blockNumber")
            return {
                "rpc_status": "available",
                "chain_id": int(chain_id, 16),
                "latest_block": int(block_number, 16),
                "contract_configured": settings.contract_address.lower() != "0x0000000000000000000000000000000000000000",
                "transaction_signing": "not_configured",
            }
        except Exception as exc:
            return {
                "rpc_status": "unavailable",
                "chain_id": None,
                "latest_block": None,
                "contract_configured": False,
                "transaction_signing": "not_configured",
                "error": str(exc),
            }

    def register_certificate(self, certificate_id: str, document_hash: str, issuer: str) -> dict[str, Any]:
        return {
            "success": False,
            "status": "not_configured",
            "transaction_hash": None,
            "network": None,
            "reason": "Contract ABI, deployed address, and authorized transaction signer are required.",
        }

    def verify_certificate(self, certificate_id: str, document_hash: str) -> dict[str, Any]:
        return {
            "certificate_id": certificate_id,
            "status": "not_checked",
            "exists": None,
            "hash_match": None,
            "reason": "No deployed contract verification adapter is configured; no blockchain confirmation is claimed.",
        }

    def revoke_certificate(self, certificate_id: str) -> dict[str, Any]:
        return {
            "success": False,
            "certificate_id": certificate_id,
            "status": "not_configured",
            "transaction_hash": None,
            "reason": "No deployed contract transaction signer is configured.",
        }

    def get_transaction(self, transaction_hash: str) -> dict[str, Any]:
        try:
            transaction = self._rpc("eth_getTransactionByHash", [transaction_hash])
            receipt = self._rpc("eth_getTransactionReceipt", [transaction_hash])
            return {"status": "found" if transaction else "not_found", "transaction": transaction, "receipt": receipt}
        except Exception as exc:
            return {"status": "unavailable", "transaction": None, "receipt": None, "error": str(exc)}

    def get_certificate_record(self, certificate_id: str) -> dict[str, Any]:
        return {
            "certificate_id": certificate_id,
            "status": "not_checked",
            "reason": "No deployed contract verification adapter is configured.",
        }


def get_blockchain_service() -> BlockchainService:
    return BlockchainService()
