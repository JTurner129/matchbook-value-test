"""No lookahead: the Phase 1 decision sees only pre-closing columns."""
import numpy as np
import pandas as pd
import pytest

from mvt import fd, phase1, variants


def synthetic(n=200, seed=0):
    rng = np.random.default_rng(seed)
    p = rng.dirichlet([3, 2, 2], n)
    early = 1 / (p * 1.025)
    close = 1 / (rng.dirichlet([3, 2, 2], n) * 1.02)
    bfe = 1 / p * rng.uniform(0.95, 1.08, (n, 3))
    df = pd.DataFrame({
        "Date": pd.date_range("2020-08-01", periods=n, freq="D").strftime("%d/%m/%Y"),
        "HomeTeam": [f"H{i}" for i in range(n)], "AwayTeam": [f"A{i}" for i in range(n)],
        "FTR": rng.choice(list("HDA"), n), "season": "2021", "league": "E1",
    })
    for j, s in enumerate("HDA"):
        df[f"PS{s}"], df[f"PSC{s}"], df[f"BFE{s}"], df[f"BFEC{s}"] = early[:, j], close[:, j], bfe[:, j], bfe[:, j]
    return df


def test_decision_refuses_future_columns():
    t = fd.outcome_table(synthetic())
    with pytest.raises(ValueError):
        phase1.decide(t)  # full table includes closing prices and results
    phase1.decide(t[fd.DECISION_COLS])


def test_flags_unchanged_when_future_is_scrambled():
    df = synthetic()
    base = phase1.flags_for(fd.outcome_table(df))
    rng = np.random.default_rng(9)
    df2 = df.copy()
    for c in ["PSCH", "PSCD", "PSCA", "BFECH", "BFECD", "BFECA"]:
        df2[c] = rng.permutation(df2[c].to_numpy())
    df2["FTR"] = rng.choice(list("HDA"), len(df2))
    scr = phase1.flags_for(fd.outcome_table(df2))
    assert base[["event_id", "selection"]].equals(scr[["event_id", "selection"]])
    assert len(base) > 0


def test_decision_cols_exclude_closing_and_results():
    for c in fd.DECISION_COLS:
        assert "close" not in c and c not in ("won", "result_known")


def test_analyse_requires_variant():
    with pytest.raises(variants.NoVariantError):
        phase1.analyse("dev")


def test_placebo_keeps_records_whole():
    t = fd.outcome_table(synthetic(600))
    f = phase1.flags_for(t)
    key = ["event_id", "selection"]
    for p in phase1.placebo_sets(t, f, 3, seed=1):
        merged = p.merge(t, on=key, suffixes=("", "_orig"))
        for c in ["bfe_early", "pin_close_fair", "won"]:
            assert (merged[c] == merged[c + "_orig"]).all()
        assert len(p) == len(f)
        assert (phase1.strata(p).value_counts().sort_index() == phase1.strata(f).value_counts().sort_index()).all()


def test_holdout_files_refused_while_sealed():
    from mvt import sealed
    if sealed.MARKER.exists():
        pytest.skip("holdout already unsealed")
    cfg = phase1.load_config()
    paths = phase1.files_for("holdout", cfg)
    assert all(sealed.is_sealed_path(p) for p in paths)
    with pytest.raises(sealed.SealedError):
        phase1.build("holdout", cfg)
