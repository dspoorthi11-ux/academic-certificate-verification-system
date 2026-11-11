import base64
import hashlib
import json
import os
from pathlib import Path
from typing import Any

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey


class AttestationSigner:
    algorithm = "Ed25519"

    def __init__(self, key_path: str | None = None) -> None:
        configured_path = key_path or os.getenv("ATTESTATION_PRIVATE_KEY_PATH")
        self.key_path = Path(configured_path) if configured_path else Path(__file__).resolve().parents[2] / "storage" / "attestation-ed25519.pem"
        self.key_path.parent.mkdir(parents=True, exist_ok=True)
        self._private_key = self._load_or_create_key()
        public_bytes = self._private_key.public_key().public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw,
        )
        self.public_key = base64.b64encode(public_bytes).decode("ascii")
        self.key_id = hashlib.sha256(public_bytes).hexdigest()[:32]

    def sign(self, payload: dict[str, Any]) -> tuple[str, str, str]:
        message = self.canonicalize(payload)
        signature = self._private_key.sign(message)
        return base64.b64encode(signature).decode("ascii"), self.public_key, self.key_id

    @staticmethod
    def canonicalize(payload: dict[str, Any]) -> bytes:
        return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")

    @staticmethod
    def verify(payload: dict[str, Any], signature: str, public_key: str) -> bool:
        try:
            key_bytes = base64.b64decode(public_key, validate=True)
            signature_bytes = base64.b64decode(signature, validate=True)
            Ed25519PublicKey.from_public_bytes(key_bytes).verify(
                signature_bytes,
                AttestationSigner.canonicalize(payload),
            )
            return True
        except (ValueError, TypeError, Exception):
            return False

    def _load_or_create_key(self) -> Ed25519PrivateKey:
        if self.key_path.exists():
            key = serialization.load_pem_private_key(self.key_path.read_bytes(), password=None)
            if not isinstance(key, Ed25519PrivateKey):
                raise ValueError("Attestation key must be an Ed25519 private key")
            return key

        if os.getenv("APP_ENV", "development").lower() == "production":
            raise RuntimeError("ATTESTATION_PRIVATE_KEY_PATH must reference a provisioned production key")

        key = Ed25519PrivateKey.generate()
        pem = key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        )
        descriptor = os.open(self.key_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(descriptor, "wb") as key_file:
            key_file.write(pem)
        return key


def get_attestation_signer() -> AttestationSigner:
    return AttestationSigner()