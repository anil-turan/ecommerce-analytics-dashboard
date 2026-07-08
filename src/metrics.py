"""KPI and aggregation logic behind the dashboard, kept separate from the
Streamlit UI so it's independently testable -- Streamlit callbacks aren't
unit-testable, but the numbers they display are, and those numbers are
where a bug would actually mislead a stakeholder.

Convention: only `status == 'completed'` orders count toward revenue/KPIs
throughout -- returned/cancelled orders were never fulfilled.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

COMPLETED = "completed"


def filter_sales(
    df: pd.DataFrame,
    start_date: pd.Timestamp | None = None,
    end_date: pd.Timestamp | None = None,
    regions: list[str] | None = None,
    categories: list[str] | None = None,
    channels: list[str] | None = None,
) -> pd.DataFrame:
    """Apply the dashboard's sidebar filters. Any filter left as None/empty
    means "no restriction on this dimension"."""
    out = df
    if start_date is not None:
        out = out[out["order_date"] >= start_date]
    if end_date is not None:
        out = out[out["order_date"] <= end_date]
    if regions:
        out = out[out["region"].isin(regions)]
    if categories:
        out = out[out["category"].isin(categories)]
    if channels:
        out = out[out["acquisition_channel"].isin(channels)]
    return out


def compute_kpis(df: pd.DataFrame) -> dict:
    """Headline KPI row: revenue, orders, AOV, unique customers, and
    month-over-month revenue growth on completed orders only."""
    completed = df[df["status"] == COMPLETED]
    total_revenue = float(completed["revenue"].sum())
    total_orders = int(completed["order_id"].nunique())
    unique_customers = int(completed["customer_id"].nunique())
    aov = total_revenue / total_orders if total_orders else 0.0

    monthly = revenue_by_period(completed, freq="ME")
    if len(monthly) >= 2:
        last, prior = monthly["revenue"].iloc[-1], monthly["revenue"].iloc[-2]
        mom_growth_pct = 100.0 * (last - prior) / prior if prior else np.nan
    else:
        mom_growth_pct = np.nan

    return {
        "total_revenue": total_revenue,
        "total_orders": total_orders,
        "unique_customers": unique_customers,
        "aov": aov,
        "mom_growth_pct": mom_growth_pct,
    }


def revenue_by_period(df: pd.DataFrame, freq: str = "ME") -> pd.DataFrame:
    """Revenue trend at the given pandas frequency (default month-end),
    completed orders only, with a cumulative-revenue column."""
    completed = df[df["status"] == COMPLETED].copy()
    period = completed["order_date"].dt.to_period(freq.replace("ME", "M"))
    completed["period"] = period.dt.to_timestamp()
    out = completed.groupby("period", as_index=False)["revenue"].sum()
    out = out.sort_values("period").reset_index(drop=True)
    out["cumulative_revenue"] = out["revenue"].cumsum()
    return out


def revenue_by_dimension(df: pd.DataFrame, dim_col: str) -> pd.DataFrame:
    """Revenue and order count grouped by any dimension column (region,
    category, acquisition_channel, ...), completed orders only."""
    completed = df[df["status"] == COMPLETED]
    out = completed.groupby(dim_col, as_index=False).agg(
        revenue=("revenue", "sum"),
        orders=("order_id", "nunique"),
    )
    return out.sort_values("revenue", ascending=False).reset_index(drop=True)


def top_products(df: pd.DataFrame, n: int = 10) -> pd.DataFrame:
    completed = df[df["status"] == COMPLETED]
    out = completed.groupby("product_name", as_index=False).agg(
        revenue=("revenue", "sum"),
        units_sold=("quantity", "sum"),
        category=("category", "first"),
    )
    return out.sort_values("revenue", ascending=False).head(n).reset_index(drop=True)
