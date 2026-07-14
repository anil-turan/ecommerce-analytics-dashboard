"""Tests for bootstrap significance testing on cross-group KPI comparisons."""

import numpy as np
import pandas as pd
import pytest

from src.significance import bootstrap_mean_diff_ci, compare_dimension_pairs


def test_bootstrap_ci_not_significant_for_identical_distributions():
    rng = np.random.default_rng(0)
    group_a = rng.normal(50, 10, 200)
    group_b = rng.normal(50, 10, 200)
    result = bootstrap_mean_diff_ci(group_a, group_b, n_boot=1000, seed=1)
    assert result["significant"] is False
    assert result["ci_low"] < 0 < result["ci_high"]


def test_bootstrap_ci_significant_for_clearly_shifted_distributions():
    rng = np.random.default_rng(0)
    group_a = rng.normal(50, 5, 200)
    group_b = rng.normal(70, 5, 200)
    result = bootstrap_mean_diff_ci(group_a, group_b, n_boot=1000, seed=1)
    assert result["significant"] is True
    assert result["ci_low"] > 0
    assert result["diff"] == pytest.approx(20, abs=3)


def test_bootstrap_ci_diff_sign_convention():
    # group_b higher than group_a -> positive diff
    group_a = np.array([10.0] * 50)
    group_b = np.array([20.0] * 50)
    result = bootstrap_mean_diff_ci(group_a, group_b, n_boot=500, seed=2)
    assert result["diff"] == pytest.approx(10.0)


def test_compare_dimension_pairs_excludes_non_completed_orders():
    df = pd.DataFrame({
        "acquisition_channel": ["A", "A", "B", "B", "B"],
        "revenue": [10.0, 12.0, 100.0, 110.0, 90.0],
        "status": ["completed", "completed", "completed", "completed", "cancelled"],
    })
    out = compare_dimension_pairs(df, "acquisition_channel", n_boot=200, seed=3)
    assert len(out) == 1
    row = out.iloc[0]
    assert row["mean_b"] == pytest.approx((100.0 + 110.0) / 2)  # cancelled order excluded


def test_compare_dimension_pairs_sorted_by_absolute_diff_descending():
    rng = np.random.default_rng(4)
    df = pd.DataFrame({
        "acquisition_channel": ["A"] * 100 + ["B"] * 100 + ["C"] * 100,
        "revenue": np.concatenate([
            rng.normal(20, 3, 100),
            rng.normal(22, 3, 100),
            rng.normal(80, 3, 100),
        ]),
        "status": ["completed"] * 300,
    })
    out = compare_dimension_pairs(df, "acquisition_channel", n_boot=500, seed=5)
    assert len(out) == 3  # A-B, A-C, B-C
    abs_diffs = out["diff"].abs().tolist()
    assert abs_diffs == sorted(abs_diffs, reverse=True)


def test_compare_dimension_pairs_skips_groups_with_too_few_orders():
    df = pd.DataFrame({
        "acquisition_channel": ["A", "A", "A", "B"],
        "revenue": [10.0, 12.0, 11.0, 50.0],
        "status": ["completed"] * 4,
    })
    out = compare_dimension_pairs(df, "acquisition_channel", n_boot=200, seed=6)
    assert out.empty  # group B has only 1 order, below the minimum of 2
