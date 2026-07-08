"""Executive-facing e-commerce analytics dashboard (Streamlit + Plotly).

Run with: streamlit run src/app.py
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from src.generator import generate_sales
from src.metrics import (
    compute_kpis,
    filter_sales,
    revenue_by_dimension,
    revenue_by_period,
    top_products,
)

DATA_PATH = Path(__file__).resolve().parents[1] / "data" / "sales.csv"

st.set_page_config(page_title="UK E-Commerce Analytics", layout="wide", page_icon="\U0001F4CA")


@st.cache_data
def load_data() -> pd.DataFrame:
    if DATA_PATH.exists():
        df = pd.read_csv(DATA_PATH, parse_dates=["order_date"])
    else:
        df = generate_sales()
    return df


def kpi_card(col, label: str, value: str, delta: str | None = None):
    col.metric(label, value, delta)


def main():
    df = load_data()

    st.title("UK E-Commerce Analytics Dashboard")
    st.caption(
        "Synthetic UK e-commerce sales data, July 2024 - June 2026. "
        "All figures are completed orders only; returned/cancelled orders are excluded."
    )

    with st.sidebar:
        st.header("Filters")
        min_date, max_date = df["order_date"].min(), df["order_date"].max()
        date_range = st.date_input(
            "Order date range", value=(min_date.date(), max_date.date()),
            min_value=min_date.date(), max_value=max_date.date(),
        )
        regions = st.multiselect("Region", sorted(df["region"].unique()))
        categories = st.multiselect("Category", sorted(df["category"].unique()))
        channels = st.multiselect("Acquisition channel", sorted(df["acquisition_channel"].unique()))

    start_date = pd.Timestamp(date_range[0]) if len(date_range) > 0 else None
    end_date = pd.Timestamp(date_range[1]) if len(date_range) > 1 else None

    filtered = filter_sales(
        df, start_date=start_date, end_date=end_date,
        regions=regions, categories=categories, channels=channels,
    )

    kpis = compute_kpis(filtered)

    col1, col2, col3, col4, col5 = st.columns(5)
    kpi_card(col1, "Total Revenue", f"£{kpis['total_revenue']:,.0f}")
    kpi_card(col2, "Orders", f"{kpis['total_orders']:,}")
    kpi_card(col3, "Avg. Order Value", f"£{kpis['aov']:,.2f}")
    kpi_card(col4, "Unique Customers", f"{kpis['unique_customers']:,}")
    mom = kpis["mom_growth_pct"]
    kpi_card(col5, "MoM Revenue Growth", f"{mom:+.1f}%" if pd.notna(mom) else "n/a")

    st.divider()

    left, right = st.columns([2, 1])

    with left:
        st.subheader("Revenue trend")
        trend = revenue_by_period(filtered)
        fig = go.Figure()
        fig.add_bar(x=trend["period"], y=trend["revenue"], name="Monthly revenue",
                   marker_color="#94a3b8")
        fig.add_trace(go.Scatter(
            x=trend["period"], y=trend["cumulative_revenue"], name="Cumulative revenue",
            yaxis="y2", mode="lines+markers", line=dict(color="#e76f51", width=3),
        ))
        fig.update_layout(
            yaxis=dict(title="Monthly revenue (£)"),
            yaxis2=dict(title="Cumulative revenue (£)", overlaying="y", side="right"),
            legend=dict(orientation="h", yanchor="bottom", y=1.02),
            margin=dict(t=10, b=10),
        )
        st.plotly_chart(fig, use_container_width=True)

    with right:
        st.subheader("Revenue by category")
        cat_rev = revenue_by_dimension(filtered, "category")
        fig = px.bar(cat_rev, x="revenue", y="category", orientation="h", color="revenue",
                    color_continuous_scale="Teal")
        fig.update_layout(showlegend=False, coloraxis_showscale=False, margin=dict(t=10, b=10),
                          yaxis=dict(categoryorder="total ascending"))
        st.plotly_chart(fig, use_container_width=True)

    col_a, col_b = st.columns(2)

    with col_a:
        st.subheader("Revenue by region")
        region_rev = revenue_by_dimension(filtered, "region")
        fig = px.bar(region_rev, x="region", y="revenue", color="revenue",
                    color_continuous_scale="Blues")
        fig.update_layout(showlegend=False, coloraxis_showscale=False, margin=dict(t=10, b=10))
        st.plotly_chart(fig, use_container_width=True)

    with col_b:
        st.subheader("Revenue by acquisition channel")
        channel_rev = revenue_by_dimension(filtered, "acquisition_channel")
        fig = px.pie(channel_rev, names="acquisition_channel", values="revenue", hole=0.45)
        fig.update_layout(margin=dict(t=10, b=10))
        st.plotly_chart(fig, use_container_width=True)

    st.subheader("Top 10 products by revenue")
    st.dataframe(
        top_products(filtered, n=10).style.format({"revenue": "£{:,.2f}"}),
        use_container_width=True, hide_index=True,
    )


if __name__ == "__main__":
    main()
