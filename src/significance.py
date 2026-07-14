"""Statistical significance testing for cross-group KPI comparisons.

A dashboard showing "Paid Search AOV is £42, Organic is £38" invites a
stakeholder to read a difference into noise. This module answers the actual
question -- is that gap bigger than sampling variation would produce anyway?
-- with a bootstrap confidence interval on the difference in per-order
revenue (AOV) between two groups, computed from scratch (no scipy.stats
dependency beyond what's already used elsewhere in this project).

A difference is called significant here when its 95% bootstrap CI excludes
zero -- the standard nonparametric analogue of a two-sided test at alpha=0.05,
without assuming normality of per-order revenue (which is right-skewed).
"""

from __future__ import annotations

import numpy as np
import pandas as pd

COMPLETED = "completed"


def bootstrap_mean_diff_ci(
    group_a: np.ndarray,
    group_b: np.ndarray,
    n_boot: int = 2000,
    alpha: float = 0.05,
    seed: int = 42,
) -> dict:
    """Bootstrap CI for mean(group_b) - mean(group_a).

    Resamples each group independently, with replacement, `n_boot` times.
    Positive `diff` means group_b's mean is higher.
    """
    rng = np.random.default_rng(seed)
    group_a = np.asarray(group_a, dtype=float)
    group_b = np.asarray(group_b, dtype=float)

    diffs = np.empty(n_boot)
    for i in range(n_boot):
        sample_a = rng.choice(group_a, size=len(group_a), replace=True)
        sample_b = rng.choice(group_b, size=len(group_b), replace=True)
        diffs[i] = sample_b.mean() - sample_a.mean()

    lower, upper = np.percentile(diffs, [100 * alpha / 2, 100 * (1 - alpha / 2)])
    point_diff = float(group_b.mean() - group_a.mean())
    significant = bool(lower > 0 or upper < 0)

    return {
        "diff": point_diff,
        "ci_low": float(lower),
        "ci_high": float(upper),
        "significant": significant,
        "n_a": len(group_a),
        "n_b": len(group_b),
    }


def compare_dimension_pairs(
    df: pd.DataFrame,
    dim_col: str,
    metric_col: str = "revenue",
    n_boot: int = 2000,
    alpha: float = 0.05,
    seed: int = 42,
) -> pd.DataFrame:
    """Pairwise bootstrap comparison of `metric_col` (default: per-order
    revenue, i.e. AOV) across every pair of categories in `dim_col`,
    completed orders only.

    Returns one row per unordered pair, sorted by |diff| descending, so the
    largest and most-defensible gaps surface first.
    """
    completed = df[df["status"] == COMPLETED]
    groups = sorted(completed[dim_col].dropna().unique())

    rows = []
    for i, a in enumerate(groups):
        for b in groups[i + 1 :]:
            values_a = completed.loc[completed[dim_col] == a, metric_col].to_numpy()
            values_b = completed.loc[completed[dim_col] == b, metric_col].to_numpy()
            if len(values_a) < 2 or len(values_b) < 2:
                continue
            result = bootstrap_mean_diff_ci(
                values_a, values_b, n_boot=n_boot, alpha=alpha, seed=seed
            )
            rows.append(
                {
                    "group_a": a,
                    "group_b": b,
                    "mean_a": float(values_a.mean()),
                    "mean_b": float(values_b.mean()),
                    **result,
                }
            )

    out = pd.DataFrame(rows)
    if out.empty:
        return out
    return out.reindex(out["diff"].abs().sort_values(ascending=False).index).reset_index(drop=True)
