from typing import Protocol


class ElectronicSignatureProvider(Protocol):
    """Adapter contract for a CCA-authorized eSign provider integration."""

    @property
    def provider_name(self) -> str: ...

    async def sign_pdf(self, pdf_bytes: bytes, signer_reference: str) -> bytes: ...

    async def validate_signed_pdf(self, pdf_bytes: bytes) -> dict[str, object]: ...


class UnconfiguredElectronicSignatureProvider:
    provider_name = "not_configured"

    async def sign_pdf(self, pdf_bytes: bytes, signer_reference: str) -> bytes:
        raise RuntimeError("No CCA-authorized electronic-signature provider is configured")

    async def validate_signed_pdf(self, pdf_bytes: bytes) -> dict[str, object]:
        return {
            "configured": False,
            "valid": False,
            "provider": self.provider_name,
            "reason": "A CCA-authorized provider, certificate-chain validation, and trusted timestamp configuration are required.",
        }


def get_esign_provider() -> ElectronicSignatureProvider:
    return UnconfiguredElectronicSignatureProvider()