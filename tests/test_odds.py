import numpy as np
import pytest

from mvt.odds import (clv, edge, effective_price, fair_power, fair_proportional, overround)


def test_power_fair_probs_sum_to_one():
    f = fair_power([2.10, 3.40, 3.60])
    assert np.isclose(np.sum(1 / f), 1.0, atol=1e-12)


def test_power_known_value():
    # p = 1/o; find k with sum p^k = 1, check against an independent solver
    o = np.array([1.80, 3.75, 4.50])
    p = 1 / o
    from math import isclose
    lo, hi = 0.5, 2.0
    for _ in range(100):
        k = (lo + hi) / 2
        lo, hi = (k, hi) if sum(p ** k) > 1 else (lo, k)
    assert np.allclose(fair_power(o), 1 / p ** k, rtol=1e-9)


def test_power_vs_proportional_favourite_longshot():
    # power method shifts more margin onto longshots than proportional does
    o = [1.30, 5.50, 11.0]
    pw, pr = fair_power(o), fair_proportional(o)
    assert pw[0] < pr[0] and pw[2] > pr[2]


def test_no_margin_is_identity():
    p = np.array([0.5, 0.3, 0.2])
    assert np.allclose(fair_power(1 / p), 1 / p)
    assert np.allclose(fair_proportional(1 / p), 1 / p)


def test_vectorised_and_invalid_rows():
    a = np.array([[2.1, 3.4, 3.6], [np.nan, 3.0, 3.0], [1.0, 3.0, 3.0]])
    f = fair_power(a)
    assert np.isfinite(f[0]).all() and np.isnan(f[1]).all() and np.isnan(f[2]).all()
    assert np.isclose(overround(a[:1])[0], 1 / 2.1 + 1 / 3.4 + 1 / 3.6)


def test_commission_and_clv_formula():
    assert effective_price(3.0) == pytest.approx(1 + 2 * 0.98)
    assert clv(3.0, 2.8) == pytest.approx((1 + 2 * 0.98) / 2.8 - 1)
    assert clv(2.0, 2.0) == pytest.approx(0.98 / 2.0 + 0.5 - 1)  # = -1%
    assert edge(3.09, 3.0) == pytest.approx(0.03)
