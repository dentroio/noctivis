"""Deterministic format triage; not a decompiler."""
from pathlib import Path

def classify(path: Path) -> dict:
    with path.open("rb") as stream:
        header = stream.read(8)
    if header.startswith(b"\x7fELF"):
        kind = "ELF"
    elif header.startswith(b"MZ"):
        kind = "PE candidate"
    elif header[:4] in (b"\xfe\xed\xfa\xce", b"\xce\xfa\xed\xfe", b"\xfe\xed\xfa\xcf", b"\xcf\xfa\xed\xfe"):
        kind = "Mach-O"
    else:
        kind = "unknown"
    return {"format": kind, "size_bytes": path.stat().st_size}
