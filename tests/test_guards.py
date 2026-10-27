import csv
import json

import pytest

from mvt import sealed, variants


def test_sealed_folder_refused_without_marker(tmp_path):
    p = sealed.SEALED / "2425_E1.csv"
    with pytest.raises(sealed.SealedError):
        sealed.check_read(p, marker=tmp_path / "missing.json")
    with pytest.raises(sealed.SealedError):
        sealed.check_read(sealed.SEALED / "sub" / ".." / "x.csv", marker=tmp_path / "missing.json")


def test_sealed_folder_allowed_after_marker(tmp_path):
    m = tmp_path / "UNSEALED.json"
    m.write_text("{}")
    sealed.check_read(sealed.SEALED / "2425_E1.csv", marker=m)


def test_raw_folder_not_sealed():
    assert not sealed.is_sealed_path(sealed.ROOT / "data" / "raw" / "1920_E1.csv")


def test_read_bytes_on_real_sealed_dir_refused_until_unsealed():
    if sealed.MARKER.exists():
        pytest.skip("holdout already unsealed")
    with pytest.raises(sealed.SealedError):
        sealed.read_bytes(sealed.SEALED / "anything.csv")


def test_variant_wrapper_logs_and_enforces(tmp_path):
    log = tmp_path / "variants.csv"
    with pytest.raises(variants.NoVariantError):
        variants.require_variant()
    with variants.variant("t1", "dev", {"a": 1}, path=log) as res:
        variants.require_variant()
        res.update(n_flags=5, mean_clv=0.01, p_one_sided=0.2)
    with pytest.raises(ValueError):
        with variants.variant("t2", "dev", {}, path=log):
            raise ValueError("boom")
    rows = list(csv.DictReader(open(log)))
    assert [r["status"] for r in rows] == ["started", "finished", "started", "crashed"]
    assert variants.n_variants(log) == 2
    assert json.loads(rows[0]["params"]) == {"a": 1}
