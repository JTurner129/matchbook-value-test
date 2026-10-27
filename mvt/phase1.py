"""Phase 1: historical sanity check on football-data.co.uk (CLAUDE.md s8).

Usage (each step is separate and in this order):
  python -m mvt.phase1 coverage   field coverage table, all fetched files (no prices compared)
  python -m mvt.phase1 placebo    placebo calibration: 200 matched random sets, nominal alpha
  python -m mvt.phase1 dev        the pre-registered development analysis (a logged variant)
  python -m mvt.unseal            once, after the dev result is committed
  python -m mvt.phase1 holdout    the holdout, once (a logged variant)

Settings come from config/phase1.json, which is fixed in PREREGISTRATION.md.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from mvt import fd, sealed, variants
from mvt.odds import FLAG_EDGE, clv, edge, effective_price
from mvt.stats import cluster_bootstrap

ROOT = Path(__file__).resolve().parent.parent
CONFIG = ROOT / "config" / "phase1.json"
RESULTS = ROOT / "results"
PRICE_BANDS = [1.0, 1.5, 2.0, 3.0, 5.0, 10.0, np.inf]


def load_config() -> dict:
    return json.loads(CONFIG.read_text())


def files_for(scope: str, cfg: dict) -> list[Path]:
    seasons = cfg["dev_seasons"] if scope == "dev" else cfg["holdout_seasons"]
    folder = fd.DATA / ("raw" if scope == "dev" else "sealed")
    return [folder / f"{s}_{lg}.csv" for s in seasons for lg in cfg["leagues"]]


# ----------------------------------------------------------------------------- building

def build(scope: str, cfg: dict) -> tuple[pd.DataFrame, dict]:
    """Eligible outcome records plus exclusion counts. Nothing here looks at closing
    prices or results except the exclusion checks for missing closing data."""
    frames = [fd.outcome_table(fd.parse_file(p)) for p in files_for(scope, cfg)]
    t = pd.concat(frames, ignore_index=True)
    excl = {"outcome_records_total": int(len(t))}
    lo, hi = cfg["pinnacle_overround_range"]

    def drop(mask, label):
        nonlocal t
        excl[label] = int(mask.sum())
        t = t[~mask]

    drop(~np.isfinite(t["pin_early_fair"]), "excl_no_pinnacle_early")
    drop((t["pin_early_overround"] < lo) | (t["pin_early_overround"] > hi), "excl_pinnacle_early_overround_out_of_range")
    drop(~(np.isfinite(t["bfe_early"]) & (t["bfe_early"] > 1.0)), "excl_no_betfair_early")
    drop(t["date"].isna(), "excl_no_date")
    drop(~np.isfinite(t["pin_close_fair"]), "excl_no_pinnacle_close")
    drop((t["pin_close_overround"] < lo) | (t["pin_close_overround"] > hi), "excl_pinnacle_close_overround_out_of_range")
    drop(~t["result_known"], "excl_no_result")
    excl["eligible_records"] = int(len(t))
    return t.reset_index(drop=True), excl


def decide(view: pd.DataFrame, fair_col: str = "pin_early_fair") -> np.ndarray:
    """The flag decision. Takes only decision-time columns (no lookahead)."""
    bad = set(view.columns) - set(fd.DECISION_COLS)
    if bad:
        raise ValueError(f"decision may not see {sorted(bad)}")
    return np.asarray(edge(view["bfe_early"], view[fair_col]) >= FLAG_EDGE)


def flags_for(t: pd.DataFrame, fair_col: str = "pin_early_fair") -> pd.DataFrame:
    f = t[decide(t[fd.DECISION_COLS], fair_col)].copy()
    # One bet per selection: each (event, selection) has one pre-closing snapshot here,
    # so this is a check rather than a filter.
    assert not f.duplicated(["event_id", "selection"]).any()
    f["edge"] = edge(f["bfe_early"], f[fair_col])
    return f


def strata(df: pd.DataFrame) -> pd.Series:
    band = pd.cut(df["bfe_early"], PRICE_BANDS, right=False, labels=False)
    return df["league"].astype(str) + "|" + band.astype(str) + "|" + df["tts_bin"].astype(str)


# ----------------------------------------------------------------------------- tests

def passes(boot, alpha: float, min_mean: float) -> bool:
    """Pre-registered pass rule: mean CLV >= min_mean and one-sided p < alpha."""
    return bool(boot.mean >= min_mean and boot.p_one_sided < alpha)


def summarise(f: pd.DataFrame, value_col: str = "clv") -> dict:
    b = cluster_bootstrap(f[value_col], f["event_id"])
    return b.as_dict()


def per_group(f: pd.DataFrame, col: str) -> list[dict]:
    rows = []
    for k, g in f.groupby(col, sort=True):
        b = cluster_bootstrap(g["clv"], g["event_id"])
        rows.append({col: k, "n": b.n, "mean_clv": b.mean, "ci_low": b.ci_low, "ci_high": b.ci_high})
    return rows


def season_trend(by_season: list[dict]) -> dict:
    x = np.arange(len(by_season), dtype=float)
    y = np.array([r["mean_clv"] for r in by_season])
    if len(x) < 2:
        return {"slope_per_season": float("nan")}
    slope = float(np.polyfit(x, y, 1)[0])
    return {"slope_per_season": slope, "seasons": [r["season"] for r in by_season]}


def analyse(scope: str) -> dict:
    """The pre-registered analysis. Must run inside a variant."""
    variants.require_variant()
    cfg = load_config()
    t, excl = build(scope, cfg)
    f = flags_for(t)
    f["clv"] = clv(f["bfe_early"], f["pin_close_fair"])
    f["clv_vs_exchange_close"] = effective_price(f["bfe_early"]) / f["bfe_close"] - 1.0
    eff = effective_price(f["bfe_early"])
    f["pnl"] = np.where(f["won"], eff - 1.0, -1.0)

    n_var = variants.n_variants()
    boot = cluster_bootstrap(f["clv"], f["event_id"])
    primary = boot.as_dict()
    alpha = 0.05 / max(n_var, 1)
    out = {
        "scope": scope, "config": cfg, "exclusions": excl,
        "n_eligible_records": int(len(t)), "n_flags": int(len(f)),
        "flag_rate": float(len(f) / len(t)) if len(t) else float("nan"),
        "primary_clv": primary,
        "variants_at_run": n_var, "bonferroni_alpha": alpha,
        "passes_hypothesis_at_bonferroni": passes(boot, alpha, cfg["min_mean_clv"]),
        "mean_clv_above_zero": bool(primary["mean"] > 0),
    }
    # Robustness: proportional margin removal for both the flag and the close.
    fp = flags_for(t, "pin_early_fair_prop")
    fp["clv"] = clv(fp["bfe_early"], fp["pin_close_fair_prop"])
    rb = summarise(fp)
    out["robustness_proportional"] = {
        **rb, "n_flags": int(len(fp)),
        "agrees_in_sign": bool(np.sign(rb["mean"]) == np.sign(primary["mean"])),
        "within_1pp": bool(abs(rb["mean"] - primary["mean"]) <= 0.01),
    }
    ok_close = f[np.isfinite(f["clv_vs_exchange_close"]) & (f["bfe_close"] > 1.0)]
    out["secondary_clv_vs_exchange_close"] = {**summarise(ok_close, "clv_vs_exchange_close"),
                                              "n_missing_exchange_close": int(len(f) - len(ok_close))}
    out["pnl_flat_stake_noisy_secondary"] = summarise(f, "pnl")
    big = f["edge"] > 0.20
    out["edge_above_20pct"] = {"n": int(big.sum()),
                               "mean_clv_without_them": summarise(f[~big])["mean"] if (~big).any() else None}
    out["by_season"] = per_group(f, "season")
    out["by_league"] = per_group(f, "league")
    out["season_trend"] = season_trend(out["by_season"])
    # Only one development season exists (see PREREGISTRATION.md), so fading is checked
    # within the period: by calendar month, and first vs second half split at the median
    # match date of the flags.
    f["month"] = f["date"].dt.strftime("%Y-%m")
    out["by_month"] = per_group(f, "month")
    out["month_trend"] = season_trend([{"season": r["month"], "mean_clv": r["mean_clv"]}
                                       for r in out["by_month"]])
    cut = f["date"].median()
    early, late = f[f["date"] < cut], f[f["date"] >= cut]
    out["early_vs_late"] = {"split_date": str(cut.date()), "early": summarise(early),
                            "late": summarise(late)}
    if out["by_league"]:
        best = max(out["by_league"], key=lambda r: r["mean_clv"])["league"]
        out["without_best_league"] = {"dropped": best, **summarise(f[f["league"] != best])}
    out["placebo_comparison"] = placebo_comparison(t, f, cfg)
    return out


# ----------------------------------------------------------------------------- placebo

def placebo_sets(t: pd.DataFrame, f: pd.DataFrame, n_sets: int, seed: int):
    """Yield placebo sets: for each flag, a random eligible record from the same stratum
    (league x price band x time-to-start). Whole records are drawn, so each record's
    price, closing price and result stay together; nothing is shuffled separately."""
    rng = np.random.default_rng(seed)
    st_all = strata(t).to_numpy()
    st_flag = strata(f).value_counts()
    pools = {s: np.flatnonzero(st_all == s) for s in st_flag.index}
    for _ in range(n_sets):
        idx = np.concatenate([rng.choice(pools[s], size=k, replace=len(pools[s]) < k)
                              for s, k in st_flag.items()])
        yield t.iloc[idx]


def placebo_comparison(t, f, cfg, n_sets: int = 20) -> dict:
    means = []
    for p in placebo_sets(t, f, n_sets, seed=cfg["placebo_seed"] + 1):
        means.append(float(np.mean(clv(p["bfe_early"], p["pin_close_fair"]))))
    return {"n_sets": n_sets, "placebo_mean_clv_avg": float(np.mean(means)),
            "placebo_mean_clv_range": [float(min(means)), float(max(means))]}


def calibrate(scope: str = "dev") -> dict:
    """Run the full pass/fail rule on 200 placebo sets at nominal alpha 0.05.
    (a) as written: matched random records; (b) null-centred: the same sets with the
    pool's mean CLV subtracted, so the true mean is exactly zero and a correct test
    should pass about 5% of the time."""
    cfg = load_config()
    t, excl = build(scope, cfg)
    f = flags_for(t)
    t = t.assign(clv=clv(t["bfe_early"], t["pin_close_fair"]))
    pool_mean = float(t["clv"].mean())
    res_a, res_c = [], []
    for p in placebo_sets(t, f, cfg["placebo_sets"], seed=cfg["placebo_seed"]):
        b = cluster_bootstrap(p["clv"], p["event_id"])
        res_a.append(passes(b, 0.05, cfg["min_mean_clv"]))
        bc = cluster_bootstrap(p["clv"] - pool_mean, p["event_id"])
        res_c.append(bool(bc.p_one_sided < 0.05))
    out = {
        "scope": scope, "n_sets": len(res_a), "set_size": int(len(f)), "exclusions": excl,
        "pass_rate_as_written": float(np.mean(res_a)),
        "reject_rate_null_centred_p_lt_0.05": float(np.mean(res_c)),
        "limit": 0.10,
    }
    out["calibration_ok"] = bool(out["pass_rate_as_written"] <= 0.10
                                 and out["reject_rate_null_centred_p_lt_0.05"] <= 0.10)
    return out


# ----------------------------------------------------------------------------- coverage

def coverage_table() -> pd.DataFrame:
    rows = []
    for folder in ("raw", "sealed"):
        for p in sorted((fd.DATA / folder).glob("*.csv")):
            if folder == "sealed" and not sealed.MARKER.exists():
                continue  # sealed files are covered before they are moved, see PROGRESS.md
            df = fd.parse_file(p)
            season, league = p.stem.split("_", 1)
            rows.append({"league": league, "season": season, **fd.coverage(df)})
    return pd.DataFrame(rows)


def _json(o):
    if isinstance(o, (np.floating, np.integer)):
        return o.item()
    if isinstance(o, np.bool_):
        return bool(o)
    raise TypeError(type(o))


def main(argv: list[str]) -> None:
    cmd = argv[0] if argv else ""
    RESULTS.mkdir(exist_ok=True)
    if cmd == "coverage":
        cov = coverage_table()
        cov.to_csv(RESULTS / "coverage.csv", index=False)
        print(cov.to_string())
    elif cmd == "placebo":
        out = calibrate("dev")
        (RESULTS / "phase1_placebo_calibration.json").write_text(json.dumps(out, indent=2, default=_json))
        print(json.dumps(out, indent=2, default=_json))
    elif cmd in ("dev", "holdout"):
        target = RESULTS / f"phase1_{cmd}.json"
        if target.exists():
            sys.exit(f"{target.name} exists; the pre-registered {cmd} analysis runs once")
        cfg = load_config()
        with variants.variant(f"phase1_{cmd}_prereg", cmd, cfg) as res:
            out = analyse(cmd)
            res.update(n_flags=out["n_flags"], mean_clv=out["primary_clv"]["mean"],
                       p_one_sided=out["primary_clv"]["p_one_sided"])
        target.write_text(json.dumps(out, indent=2, default=_json))
        print(json.dumps(out, indent=2, default=_json))
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main(sys.argv[1:])
