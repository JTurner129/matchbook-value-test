"""Cluster bootstrap by event (CLAUDE.md s6: 10,000 resamples, clustered by event)."""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

N_BOOT = 10_000
SEED = 20261027  # fixed so every run is reproducible


@dataclass
class BootResult:
    n: int
    n_clusters: int
    mean: float
    ci_low: float     # two-sided 95% percentile interval
    ci_high: float
    p_one_sided: float  # H0: mean <= 0, H1: mean > 0

    def as_dict(self) -> dict:
        return self.__dict__.copy()


def cluster_bootstrap(values, clusters, n_boot: int = N_BOOT, seed: int = SEED,
                      chunk: int = 500) -> BootResult:
    """Mean of `values` with a cluster (event) bootstrap.

    Whole events are resampled with replacement; the statistic is the pooled mean of all
    values in the resampled events. The one-sided p-value is from the centred bootstrap:
    p = (1 + #{b : mean*_b - mean >= mean}) / (1 + B), which never reports exactly 0.
    """
    v = np.asarray(values, dtype=float)
    if len(v) == 0:
        return BootResult(0, 0, float("nan"), float("nan"), float("nan"), float("nan"))
    codes, _ = pd.factorize(pd.Series(clusters))
    sums = np.bincount(codes, weights=v)
    counts = np.bincount(codes).astype(float)
    g = len(sums)
    mean = sums.sum() / counts.sum()
    rng = np.random.default_rng(seed)
    boots = np.empty(n_boot)
    done = 0
    while done < n_boot:
        b = min(chunk, n_boot - done)
        idx = rng.integers(0, g, size=(b, g), dtype=np.int32)
        boots[done:done + b] = sums[idx].sum(axis=1) / counts[idx].sum(axis=1)
        done += b
    lo, hi = np.percentile(boots, [2.5, 97.5])
    p = (1 + np.sum(boots - mean >= mean)) / (1 + n_boot)
    return BootResult(len(v), g, float(mean), float(lo), float(hi), float(p))
