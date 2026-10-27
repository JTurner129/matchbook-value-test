"""Append-only variant log (CLAUDE.md s6, "the luck test").

Every analysis that computes CLV or P&L on real (non-placebo) data must run inside
`variant(...)`. Code that computes those numbers calls `require_variant()` first, so a
quick one-off check outside the wrapper fails loudly instead of going unrecorded.
"""
from __future__ import annotations

import contextlib
import contextvars
import csv
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VARIANTS = ROOT / "variants.csv"
FIELDS = ["variant_id", "started_utc", "git_commit", "git_dirty", "name", "scope",
          "params", "status", "n_flags", "mean_clv", "p_one_sided"]

_active: contextvars.ContextVar[dict | None] = contextvars.ContextVar("variant", default=None)


class NoVariantError(RuntimeError):
    pass


def _git(*args) -> str:
    try:
        return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True,
                              check=True).stdout.strip()
    except Exception:
        return ""


def _rows(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with open(path, newline="") as f:
        return list(csv.DictReader(f))


def _append(row: dict, path: Path) -> None:
    new = not path.exists()
    with open(path, "a", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        if new:
            w.writeheader()
        w.writerow({k: row.get(k, "") for k in FIELDS})


@contextlib.contextmanager
def variant(name: str, scope: str, params: dict, path: Path = VARIANTS):
    """Log a real-data run. A row is written at start (so crashed runs still count) and a
    second row with the outcome at the end; `n_variants()` counts distinct variant ids."""
    vid = f"V{len({r['variant_id'] for r in _rows(path)}) + 1:04d}"
    rec = {"variant_id": vid, "started_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
           "git_commit": _git("rev-parse", "HEAD"), "git_dirty": str(bool(_git("status", "--porcelain"))),
           "name": name, "scope": scope, "params": json.dumps(params, sort_keys=True), "status": "started"}
    _append(rec, path)
    result: dict = {}
    token = _active.set(result)
    try:
        yield result
        rec.update(status="finished", n_flags=result.get("n_flags", ""),
                   mean_clv=result.get("mean_clv", ""), p_one_sided=result.get("p_one_sided", ""))
    except BaseException:
        rec["status"] = "crashed"
        raise
    finally:
        _active.reset(token)
        _append(rec, path)


def n_variants(path: Path = VARIANTS) -> int:
    """N for the Bonferroni bar: every logged real-data run, finished, crashed or not."""
    return len({r["variant_id"] for r in _rows(path)})


def require_variant() -> dict:
    cur = _active.get()
    if cur is None:
        raise NoVariantError("CLV/P&L on real data must run inside mvt.variants.variant(...)")
    return cur
