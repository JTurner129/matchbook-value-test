import numpy as np

from mvt.stats import cluster_bootstrap


def test_mean_and_ci_contain_truth():
    rng = np.random.default_rng(1)
    v = rng.normal(0.01, 0.1, 3000)
    cl = np.repeat(np.arange(1000), 3)
    r = cluster_bootstrap(v, cl, n_boot=2000)
    assert np.isclose(r.mean, v.mean())
    assert r.ci_low < r.mean < r.ci_high
    assert r.n == 3000 and r.n_clusters == 1000


def test_clustering_widens_ci_for_correlated_values():
    rng = np.random.default_rng(2)
    shared = np.repeat(rng.normal(0, 0.1, 500), 3)  # perfectly shared within event
    cl = np.repeat(np.arange(500), 3)
    wide = cluster_bootstrap(shared, cl, n_boot=2000)
    naive = cluster_bootstrap(shared, np.arange(1500), n_boot=2000)
    assert (wide.ci_high - wide.ci_low) > 1.5 * (naive.ci_high - naive.ci_low)


def test_p_value_null_is_roughly_uniform():
    rng = np.random.default_rng(3)
    ps = [cluster_bootstrap(rng.normal(0, 1, 300), np.arange(300), n_boot=500, seed=i).p_one_sided
          for i in range(200)]
    rate = np.mean(np.array(ps) < 0.05)
    assert 0.01 <= rate <= 0.10


def test_strong_positive_has_small_p():
    v = np.full(500, 0.05) + np.random.default_rng(4).normal(0, 0.01, 500)
    assert cluster_bootstrap(v, np.arange(500), n_boot=1000).p_one_sided < 0.01
