"""Content-addressed sample bytes. Callers store and read them. Nothing here executes a sample."""

import hashlib
import os
import tempfile
from pathlib import Path

_HEX = set("0123456789abcdef")


class ArtifactStore:
    def __init__(self, root: Path):
        self.root = root.resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    def path_for(self, sha256: str) -> Path:
        if len(sha256) != 64 or any(character not in _HEX for character in sha256):
            raise ValueError("artifact id is not a sha256")
        candidate = (self.root / sha256[:2] / sha256).resolve()
        try:
            candidate.relative_to(self.root)
        except ValueError as exc:
            raise ValueError("artifact path escapes the store") from exc
        return candidate

    def put(self, source: Path, sha256: str) -> None:
        destination = self.path_for(sha256)
        if destination.is_file():
            self._verify(destination, sha256)
            return
        destination.parent.mkdir(parents=True, exist_ok=True)
        descriptor, temporary_name = tempfile.mkstemp(prefix="artifact-", dir=destination.parent)
        temporary = Path(temporary_name)
        try:
            with os.fdopen(descriptor, "wb") as out:
                digest = hashlib.sha256()
                with source.open("rb") as incoming:
                    while chunk := incoming.read(1024 * 1024):
                        digest.update(chunk)
                        out.write(chunk)
                out.flush()
                os.fsync(out.fileno())
            if digest.hexdigest() != sha256:
                raise ValueError("sample hash does not match the stored id")
            os.replace(temporary, destination)
        except Exception:
            temporary.unlink(missing_ok=True)
            raise

    def read(self, sha256: str) -> bytes:
        destination = self.path_for(sha256)
        if not destination.is_file():
            raise FileNotFoundError(sha256)
        data = destination.read_bytes()
        if hashlib.sha256(data).hexdigest() != sha256:
            raise ValueError("stored sample failed hash verification")
        return data

    def _verify(self, destination: Path, sha256: str) -> None:
        digest = hashlib.sha256()
        with destination.open("rb") as stream:
            while chunk := stream.read(1024 * 1024):
                digest.update(chunk)
        if digest.hexdigest() != sha256:
            raise ValueError("stored sample failed hash verification")
