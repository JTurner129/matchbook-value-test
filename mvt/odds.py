"""Margin removal, edge, commission and CLV maths (definitions fixed in CLAUDE.md s6)."""
from __future__ import annotations

import numpy as np

COMMISSION = 0.02
FLAG_EDGE = 0.03


def _as2d(odds) -> np.ndarray:
    a = np.asarray(odds, dtype=float)
    return a[None, :] if a.ndim == 1 else a


def fair_power(odds) -> np.ndarray:
    """Margin-free prices by the power method.

    Implied probabilities p_i = 1/o_i are raised to a common exponent k chosen so that
    sum(p_i ** k) == 1; the fair price is 1 / p_i ** k. Works row-wise on an (n, 3) array.
    Rows with any non-finite or <= 1 price return NaN.
    """
    o = _as2d(odds)
    out = np.full(o.shape, np.nan)
    ok = np.all(np.isfinite(o) & (o > 1.0), axis=1)
    p = 1.0 / o[ok]
    lo = np.full(len(p), 0.01)   # sum(p**k) is decreasing in k because 0 < p < 1
    hi = np.full(len(p), 100.0)
    for _ in range(200):
        mid = (lo + hi) / 2
        s = np.sum(p ** mid[:, None], axis=1)
        too_big = s > 1.0
        lo = np.where(too_big, mid, lo)
        hi = np.where(too_big, hi, mid)
    k = (lo + hi) / 2
    out[ok] = 1.0 / p ** k[:, None]
    return out[0] if np.asarray(odds).ndim == 1 else out


def fair_proportional(odds) -> np.ndarray:
    """Margin-free prices by the proportional (basic normalisation) method. Robustness only."""
    o = _as2d(odds)
    out = np.full(o.shape, np.nan)
    ok = np.all(np.isfinite(o) & (o > 1.0), axis=1)
    p = 1.0 / o[ok]
    out[ok] = 1.0 / (p / p.sum(axis=1, keepdims=True))
    return out[0] if np.asarray(odds).ndim == 1 else out


def overround(odds) -> np.ndarray:
    o = _as2d(odds)
    return np.sum(1.0 / o, axis=1)


def edge(back_price, fair):
    """edge_t = back price / fair_t - 1."""
    return np.asarray(back_price, dtype=float) / np.asarray(fair, dtype=float) - 1.0


def effective_price(back_price, commission: float = COMMISSION):
    """eff = 1 + (back - 1) * (1 - commission)."""
    return 1.0 + (np.asarray(back_price, dtype=float) - 1.0) * (1.0 - commission)


def clv(back_price, fair_close, commission: float = COMMISSION):
    """CLV = eff / fair_close - 1."""
    return effective_price(back_price, commission) / np.asarray(fair_close, dtype=float) - 1.0
