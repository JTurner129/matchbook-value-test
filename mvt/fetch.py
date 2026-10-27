"""Polite downloader for football-data.co.uk season files, with a verified manifest.

Every download is recorded in data/MANIFEST.csv: URL, UTC fetch time, size, SHA-256,
row count, expected row count and a verification status (CLAUDE.md s7).
"""
from __future__ import annotations

import csv
import hashlib
import io
import os
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
MANIFEST = ROOT / "data" / "MANIFEST.csv"
BASE = "https://www.football-data.co.uk/mmz4281/{season}/{code}.csv"

# Candidate second-tier and lower leagues (main-league files that carry the full odds set).
# The final list used for analysis is fixed in PREREGISTRATION.md after the coverage table.
CANDIDATE_LEAGUES = {
    "E1": "England Championship",
    "E2": "England League One",
    "E3": "England League Two",
    "EC": "England National League",
    "SC1": "Scotland Championship",
    "SC2": "Scotland League One",
    "SC3": "Scotland League Two",
    "D2": "Germany 2. Bundesliga",
    "I2": "Italy Serie B",
    "SP2": "Spain Segunda",
    "F2": "France Ligue 2",
}
# Scottish leagues play each opponent four times, others twice.
ROUNDS = {"SC1": 2, "SC2": 2, "SC3": 2}

SEASONS = [f"{y % 100:02d}{(y + 1) % 100:02d}" for y in range(2012, 2026)]  # 1213 .. 2526
USER_AGENT = "matchbook-value-test research script (personal, non-commercial)"
MANIFEST_FIELDS = [
    "file", "url", "fetched_utc", "bytes", "sha256", "rows", "teams",
    "expected_rows", "status",
]


def season_label(season: str) -> str:
    return f"20{season[:2]}-{season[2:]}"


def http_get(url: str, tries: int = 5) -> bytes:
    delay = 2.0
    last = None
    for _ in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(req, timeout=60) as r:
                data = r.read()
                declared = r.headers.get("Content-Length")
                if declared is not None and int(declared) != len(data):
                    raise IOError(f"truncated: {len(data)} of {declared} bytes")
                return data
        except Exception as e:  # network or truncation: back off and retry
            last = e
            time.sleep(delay)
            delay *= 2
    raise RuntimeError(f"failed to fetch {url}: {last}")


def read_fd_csv(data: bytes) -> pd.DataFrame:
    """Parse a football-data CSV fully; drop the blank trailing rows some files carry."""
    text = data.decode("latin-1")
    df = pd.read_csv(io.StringIO(text), on_bad_lines="error", low_memory=False)
    df = df.dropna(how="all")
    df = df[df["HomeTeam"].notna() & df["AwayTeam"].notna()]
    return df


def verify(code: str, data: bytes) -> dict:
    df = read_fd_csv(data)
    teams = len(set(df["HomeTeam"]) | set(df["AwayTeam"]))
    expected = teams * (teams - 1) * ROUNDS.get(code, 1)
    rows = len(df)
    lines = [ln for ln in data.splitlines() if ln.strip(b" ,")]
    # A cut-off file shows up as a last line with fewer fields than the header.
    if lines[-1].count(b",") < lines[0].count(b","):
        status = "TRUNCATED"
    elif rows == expected:
        status = "OK"
    else:
        status = f"ROWS_DIFFER({rows - expected:+d})"
    return {"rows": rows, "teams": teams, "expected_rows": expected, "status": status}


def load_manifest() -> dict[str, dict]:
    if not MANIFEST.exists():
        return {}
    with open(MANIFEST, newline="") as f:
        return {r["file"]: r for r in csv.DictReader(f)}


def write_manifest(entries: dict[str, dict]) -> None:
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    with open(MANIFEST, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=MANIFEST_FIELDS)
        w.writeheader()
        for k in sorted(entries):
            w.writerow({f: entries[k].get(f, "") for f in MANIFEST_FIELDS})


def fetch_all(leagues=None, seasons=None, pause: float = 3.0) -> None:
    leagues = leagues or list(CANDIDATE_LEAGUES)
    seasons = seasons or SEASONS
    RAW.mkdir(parents=True, exist_ok=True)
    entries = load_manifest()
    for season in seasons:
        for code in leagues:
            rel = f"raw/{season}_{code}.csv"
            path = ROOT / "data" / rel
            if rel in entries and path.exists() and entries[rel]["status"].startswith(("OK", "ROWS_DIFFER")):
                if hashlib.sha256(path.read_bytes()).hexdigest() == entries[rel]["sha256"]:
                    continue  # already fetched and verified: resume
            url = BASE.format(season=season, code=code)
            try:
                data = http_get(url)
            except RuntimeError as e:
                entries[rel] = {"file": rel, "url": url, "status": f"FETCH_FAILED: {e}"[:200],
                                "fetched_utc": datetime.now(timezone.utc).isoformat(timespec="seconds")}
                write_manifest(entries)
                continue
            path.write_bytes(data)
            info = verify(code, data)
            entries[rel] = {
                "file": rel, "url": url,
                "fetched_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest(), **info,
            }
            write_manifest(entries)
            print(rel, info, flush=True)
            time.sleep(pause)


if __name__ == "__main__":
    fetch_all()
