import hashlib
import os
from pathlib import Path
from typing import Any


class IPFSAdapter:
    def __init__(self) -> None:
        self.mock_dir = Path(os.getenv("IPFS_MOCK_DIR", "/tmp/certificate_ipfs"))
        self.mock_dir.mkdir(parents=True, exist_ok=True)

    def upload_file(self, file_path: str) -> str:
        path = Path(file_path)
        content = path.read_bytes()
        digest = hashlib.sha256(content).hexdigest()
        target = self.mock_dir / f"{digest}.bin"
        if not target.exists():
            target.write_bytes(content)
        return f"QmMock{digest[:32]}"

    def get_file(self, cid: str) -> bytes | None:
        candidate = self.mock_dir / f"{cid.replace('QmMock', '')}.bin"
        if candidate.exists():
            return candidate.read_bytes()
        return None

    def remove(self, cid: str) -> bool:
        candidate = self.mock_dir / f"{cid.replace('QmMock', '')}.bin"
        if candidate.exists():
            candidate.unlink()
            return True
        return False


def get_ipfs_service() -> IPFSAdapter:
    return IPFSAdapter()
