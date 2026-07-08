"""Tests for the synthetic sales data generator."""

import numpy as np

from src.generator import END_DATE, START_DATE, generate_sales


def test_order_dates_within_window():
    df = generate_sales(seed=1)
    assert df["order_date"].min().date() >= START_DATE
    assert df["order_date"].max().date() <= END_DATE


def test_expected_columns_present():
    df = generate_sales(seed=2)
    expected = {
        "order_id", "order_date", "customer_id", "region", "acquisition_channel",
        "category", "product_name", "quantity", "unit_price", "discount_pct",
        "revenue", "status",
    }
    assert expected.issubset(df.columns)


def test_revenue_matches_quantity_price_discount():
    df = generate_sales(seed=3)
    expected_revenue = df["quantity"] * df["unit_price"] * (1 - df["discount_pct"] / 100)
    assert np.allclose(df["revenue"], expected_revenue, atol=0.01)


def test_status_values_valid():
    df = generate_sales(seed=4)
    assert set(df["status"].unique()).issubset({"completed", "returned", "cancelled"})


def test_order_ids_unique():
    df = generate_sales(seed=5)
    assert df["order_id"].is_unique
