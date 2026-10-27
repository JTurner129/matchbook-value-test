"""football-data.co.uk loading, field coverage and the per-outcome Phase 1 table.

Column meanings (from https://www.football-data.co.uk/notes.txt, quoted in PROGRESS.md):
  PSH/PSD/PSA    Pinnacle pre-closing odds   PSCH/PSCD/PSCA    Pinnacle closing odds
  BFEH/BFED/BFEA Betfair Exchange pre-closing BFECH/BFECD/BFECA Betfair Exchange closing
Pre-closing odds are collected on Friday afternoons for weekend games and Tuesday
afternoons for midweek games; closing odds are the last available before kick-off.
"""
from __future__ import annotations

import io
from pathlib import Path

import numpy as np
import pandas as pd

from mvt import sealed

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"

SIDES = ("H", "D", "A")
PIN_EARLY = [f"PS{s}" for s in SIDES]
PIN_CLOSE = [f"PSC{s}" for s in SIDES]
BFE_EARLY = [f"BFE{s}" for s in SIDES]
BFE_CLOSE = [f"BFEC{s}" for s in SIDES]
COVERAGE_COLS = {
    "Pinnacle early": PIN_EARLY, "Pinnacle close": PIN_CLOSE,
    "Betfair Exch early": BFE_EARLY, "Betfair Exch close": BFE_CLOSE,
    "Kick-off time": ["Time"], "Result": ["FTR"],
}
# Columns a Phase 1 decision may see: everything collected at the pre-closing snapshot.
DECISION_COLS = ["event_id", "league", "season", "date", "selection", "pin_early_fair",
                 "pin_early_fair_prop", "bfe_early", "tts_bin"]


def parse_file(path: Path) -> pd.DataFrame:
    raw = sealed.read_bytes(path)
    df = pd.read_csv(io.StringIO(raw.decode("latin-1")), low_memory=False)
    df = df.dropna(how="all")
    df = df[df["HomeTeam"].notna() & df["AwayTeam"].notna()].copy()
    name = Path(path).stem  # e.g. 1920_E1
    season, league = name.split("_", 1)
    df["season"] = season
    df["league"] = league
    return df


def _num(df: pd.DataFrame, cols) -> np.ndarray:
    out = np.full((len(df), len(cols)), np.nan)
    for j, c in enumerate(cols):
        if c in df.columns:
            out[:, j] = pd.to_numeric(df[c], errors="coerce").to_numpy()
    return out


def coverage(df: pd.DataFrame) -> dict:
    """Share of rows with a complete, valid price set for each field group."""
    res = {"rows": len(df)}
    for label, cols in COVERAGE_COLS.items():
        if label in ("Kick-off time", "Result"):
            res[label] = float(df[cols[0]].notna().mean()) if cols[0] in df.columns else 0.0
        else:
            a = _num(df, cols)
            res[label] = float(np.all(np.isfinite(a) & (a > 1.0), axis=1).mean())
    return res


def tts_bin(dates: pd.Series) -> np.ndarray:
    """Proxy for time-to-start at the pre-closing snapshot (football-data gives no
    collection timestamp): days from the collection day (Fri for Fri-Mon games, Tue for
    Tue-Thu games) to the match date."""
    wd = dates.dt.weekday.to_numpy()  # Mon=0 .. Sun=6
    anchor = np.where(np.isin(wd, [1, 2, 3]), 1, 4)  # Tue or Fri
    return (wd - anchor) % 7


def outcome_table(df: pd.DataFrame) -> pd.DataFrame:
    """One row per (event, selection) with early (decision-time) and closing prices."""
    from mvt.odds import fair_power, fair_proportional, overround

    dates = pd.to_datetime(df["Date"], dayfirst=True, errors="coerce")
    pe, pc = _num(df, PIN_EARLY), _num(df, PIN_CLOSE)
    be, bc = _num(df, BFE_EARLY), _num(df, BFE_CLOSE)
    fe, fc = fair_power(pe), fair_power(pc)
    fe_prop, fc_prop = fair_proportional(pe), fair_proportional(pc)
    or_e, or_c = overround(pe), overround(pc)
    ids = (df["season"] + "_" + df["league"] + "_" + dates.dt.strftime("%Y%m%d").fillna("NA")
           + "_" + df["HomeTeam"].astype(str) + "_v_" + df["AwayTeam"].astype(str)).to_numpy()
    tts = tts_bin(dates)
    parts = []
    for j, s in enumerate(SIDES):
        parts.append(pd.DataFrame({
            "event_id": ids, "league": df["league"].to_numpy(), "season": df["season"].to_numpy(),
            "date": dates.to_numpy(), "selection": s,
            "pin_early_overround": or_e, "pin_close_overround": or_c,
            "pin_early_fair": fe[:, j], "pin_early_fair_prop": fe_prop[:, j],
            "bfe_early": be[:, j], "tts_bin": tts,
            "pin_close_fair": fc[:, j], "pin_close_fair_prop": fc_prop[:, j],
            "bfe_close": bc[:, j],
            "won": (df["FTR"].to_numpy() == s),
            "result_known": df["FTR"].isin(list(SIDES)).to_numpy(),
        }))
    return pd.concat(parts, ignore_index=True)
