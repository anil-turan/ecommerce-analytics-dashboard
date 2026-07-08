"""Tests for the dashboard's KPI/aggregation logic -- the numbers a
stakeholder would actually act on, kept independently testable from the
Streamlit UI."""

import pandas as pd
import pytest

from src.metrics import (
    compute_kpis,
    filter_sales,
    revenue_by_dimension,
    revenue_by_period,
    top_products,
)


@pytest.fixture
def sample_df():
    return pd.DataFrame({
        "order_id": [1, 2, 3, 4, 5],
        "order_date": pd.to_datetime(
            ["2025-01-05", "2025-01-20", "2025-02-10", "2025-02-15", "2025-03-01"]
        ),
        "customer_id": [1, 1, 2, 3, 3],
        "region": ["London", "London", "Scotland", "Wales", "Wales"],
        "acquisition_channel": ["Organic Search"] * 5,
        "category": ["Electronics", "Books", "Electronics", "Fashion", "Fashion"],
        "product_name": ["Widget A", "Book B", "Widget A", "Shirt C", "Shirt C"],
        "quantity": [1, 2, 1, 3, 1],
        "unit_price": [100.0, 10.0, 100.0, 20.0, 20.0],
        "discount_pct": [0, 0, 0, 0, 0],
        "revenue": [100.0, 20.0, 100.0, 60.0, 20.0],
        "status": ["completed", "completed", "returned", "completed", "cancelled"],
    })


def test_filter_sales_by_region(sample_df):
    out = filter_sales(sample_df, regions=["London"])
    assert set(out["region"]) == {"London"}
    assert len(out) == 2


def test_filter_sales_by_date_range(sample_df):
    out = filter_sales(sample_df, start_date=pd.Timestamp("2025-02-01"))
    assert (out["order_date"] >= pd.Timestamp("2025-02-01")).all()
    assert len(out) == 3


def test_filter_sales_no_filters_returns_everything(sample_df):
    out = filter_sales(sample_df)
    assert len(out) == len(sample_df)


def test_compute_kpis_excludes_non_completed(sample_df):
    kpis = compute_kpis(sample_df)
    # only rows 1, 2, 4 are completed: revenue 100 + 20 + 60 = 180, 3 orders
    assert kpis["total_revenue"] == pytest.approx(180.0)
    assert kpis["total_orders"] == 3
    assert kpis["unique_customers"] == 2  # customers 1 and 3 (not 2, whose order was returned)


def test_compute_kpis_aov(sample_df):
    kpis = compute_kpis(sample_df)
    assert kpis["aov"] == pytest.approx(180.0 / 3)


def test_revenue_by_period_has_cumulative_column(sample_df):
    trend = revenue_by_period(sample_df)
    assert "cumulative_revenue" in trend.columns
    assert trend["cumulative_revenue"].iloc[-1] == pytest.approx(trend["revenue"].sum())
    assert (trend["cumulative_revenue"].diff().dropna() >= 0).all()


def test_revenue_by_dimension_sorted_descending(sample_df):
    by_region = revenue_by_dimension(sample_df, "region")
    assert list(by_region["revenue"]) == sorted(by_region["revenue"], reverse=True)
    # returned/cancelled orders excluded -> Scotland (returned) has 0 rows, not present
    assert "Scotland" not in set(by_region["region"])


def test_top_products_limits_and_sorts(sample_df):
    top = top_products(sample_df, n=2)
    assert len(top) == 2
    assert list(top["revenue"]) == sorted(top["revenue"], reverse=True)
