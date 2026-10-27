"""Guard for the sealed holdout (CLAUDE.md s8).

Nothing may read data/sealed/ until the single explicit `python -m mvt.unseal` step has
run. That step runs once: it needs the development result to be final and committed,
checks the sealed files against the SHA-256 values in PREREGISTRATION.md, and writes
results/UNSEALED.json. A second unseal is refused.
"""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SEALED = ROOT / "data" / "sealed"
MARKER = ROOT / "results" / "UNSEALED.json"
DEV_FINAL = ROOT / "results" / "phase1_dev.json"
PREREG = ROOT / "PREREGISTRATION.md"


class SealedError(PermissionError):
    pass


def is_sealed_path(path: Path) -> bool:
    p = Path(path).resolve()
    return p == SEALED.resolve() or SEALED.resolve() in p.parents


def check_read(path: Path, marker: Path = MARKER) -> None:
    if is_sealed_path(path) and not marker.exists():
        raise SealedError(f"{path} is in the sealed holdout; run `python -m mvt.unseal` once, "
                          "after the development result is final")


def read_bytes(path: Path) -> bytes:
    """The only way analysis code reads a data file."""
    check_read(Path(path))
    return Path(path).read_bytes()


def preregistered_hashes(prereg: Path = PREREG) -> dict[str, str]:
    """Lines like `| sealed/2425_E1.csv | <sha256> |` in PREREGISTRATION.md."""
    text = prereg.read_text()
    return dict(re.findall(r"\|\s*(sealed/[\w.]+)\s*\|\s*([0-9a-f]{64})\s*\|", text))


def _committed(path: Path) -> bool:
    r = subprocess.run(["git", "ls-files", "--error-unmatch", str(path)], cwd=ROOT,
                       capture_output=True)
    clean = subprocess.run(["git", "diff", "--quiet", "HEAD", "--", str(path)], cwd=ROOT)
    return r.returncode == 0 and clean.returncode == 0


def unseal() -> None:
    if MARKER.exists():
        raise SealedError(f"already unsealed at {json.loads(MARKER.read_text())['unsealed_utc']}; "
                          "the holdout can be opened only once")
    if not DEV_FINAL.exists() or not _committed(DEV_FINAL):
        raise SealedError("the development result must be final and committed before unsealing")
    expected = preregistered_hashes()
    if not expected:
        raise SealedError("no sealed hashes found in PREREGISTRATION.md")
    present = sorted(p.relative_to(SEALED.parent).as_posix() for p in SEALED.glob("*.csv"))
    if sorted(expected) != present:
        raise SealedError(f"sealed files differ from the pre-registered list: {set(expected) ^ set(present)}")
    for rel, sha in expected.items():
        got = hashlib.sha256((SEALED.parent / rel).read_bytes()).hexdigest()
        if got != sha:
            raise SealedError(f"{rel}: SHA-256 {got} != pre-registered {sha}")
    MARKER.parent.mkdir(exist_ok=True)
    MARKER.write_text(json.dumps({
        "unsealed_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "files_verified": len(expected),
        "dev_result_commit": subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT,
                                            capture_output=True, text=True).stdout.strip(),
    }, indent=2))
    print(f"unsealed {len(expected)} files; marker written to {MARKER.relative_to(ROOT)}")
