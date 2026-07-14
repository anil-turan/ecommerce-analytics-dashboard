"""Export static preview images of the dashboard's charts for the README.

The live dashboard (`streamlit run src/app.py`) is fully interactive; these
are dark-themed static snapshots of the same Plotly figures, generated with
kaleido, so the README shows real output without requiring a running
Streamlit server or a browser screenshot pipeline.

Usage: python -m src.export_screenshots
"""

from __future__ import annotations

from pathlib import Path

import plotly.express as px
import plotly.graph_objects as go

from src.generator import generate_sales
from src.metrics import compute_kpis, revenue_by_dimension, revenue_by_period, top_products
from src.significance import compare_dimension_pairs

OUT_DIR = Path(__file__).resolve().parents[1] / "reports" / "screenshots"
TEMPLATE = "plotly_dark"


def export_kpi_row(df, out_dir: Path) -> None:
    kpis = compute_kpis(df)
    labels = ["Total Revenue", "Orders", "Avg. Order Value", "Unique Customers", "MoM Growth"]
    values = [
        f"£{kpis['total_revenue']:,.0f}",
        f"{kpis['total_orders']:,}",
        f"£{kpis['aov']:,.2f}",
        f"{kpis['unique_customers']:,}",
        f"{kpis['mom_growth_pct']:+.1f}%",
    ]
    fig = go.Figure()
    positions = [0, 2.2, 4.4, 6.8, 9.0]
    for x, label, value in zip(positions, labels, values):
        fig.add_annotation(
            x=x, y=1, text=label, showarrow=False, font=dict(size=15, color="#94a3b8"),
            yshift=30, xanchor="left",
        )
        fig.add_annotation(
            x=x, y=1, text=value, showarrow=False, font=dict(size=28, color="#f1f5f9"),
            xanchor="left",
        )
    fig.update_xaxes(visible=False, range=[-0.3, 10.5])
    fig.update_yaxes(visible=False, range=[0.7, 1.3])
    fig.update_layout(
        template=TEMPLATE, height=180, width=1300,
        margin=dict(t=20, b=20, l=20, r=20),
        paper_bgcolor="#0e1117", plot_bgcolor="#0e1117",
    )
    fig.write_image(out_dir / "01_kpi_row.png", scale=2)


def export_revenue_trend(df, out_dir: Path) -> None:
    trend = revenue_by_period(df)
    fig = go.Figure()
    fig.add_bar(x=trend["period"], y=trend["revenue"], name="Monthly revenue",
               marker_color="#94a3b8")
    fig.add_trace(go.Scatter(
        x=trend["period"], y=trend["cumulative_revenue"], name="Cumulative revenue",
        yaxis="y2", mode="lines+markers", line=dict(color="#e76f51", width=3),
    ))
    fig.update_layout(
        template=TEMPLATE,
        title="Revenue trend",
        yaxis=dict(title="Monthly revenue (£)"),
        yaxis2=dict(title="Cumulative revenue (£)", overlaying="y", side="right"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
        margin=dict(t=60, b=40),
    )
    fig.write_image(out_dir / "02_revenue_trend.png", width=1000, height=500, scale=2)


def export_category_revenue(df, out_dir: Path) -> None:
    cat_rev = revenue_by_dimension(df, "category")
    fig = px.bar(cat_rev, x="revenue", y="category", orientation="h", color="revenue",
                color_continuous_scale="Teal", title="Revenue by category")
    fig.update_layout(template=TEMPLATE, showlegend=False, coloraxis_showscale=False,
                      yaxis=dict(categoryorder="total ascending"), margin=dict(t=60, b=40))
    fig.write_image(out_dir / "03_category_revenue.png", width=800, height=500, scale=2)


def export_region_and_channel(df, out_dir: Path) -> None:
    region_rev = revenue_by_dimension(df, "region")
    fig = px.bar(region_rev, x="region", y="revenue", color="revenue",
                color_continuous_scale="Blues", title="Revenue by region")
    fig.update_layout(template=TEMPLATE, showlegend=False, coloraxis_showscale=False,
                      margin=dict(t=60, b=40))
    fig.write_image(out_dir / "04_region_revenue.png", width=800, height=500, scale=2)

    channel_rev = revenue_by_dimension(df, "acquisition_channel")
    fig = px.pie(channel_rev, names="acquisition_channel", values="revenue", hole=0.45,
                title="Revenue by acquisition channel")
    fig.update_layout(template=TEMPLATE, margin=dict(t=60, b=40))
    fig.write_image(out_dir / "05_channel_revenue.png", width=800, height=500, scale=2)


def export_top_products_table(df, out_dir: Path) -> None:
    top = top_products(df, n=10)
    fig = go.Figure(data=[go.Table(
        header=dict(values=["Product", "Revenue", "Units Sold", "Category"],
                   fill_color="#1e293b", font=dict(color="#f1f5f9", size=13), align="left"),
        cells=dict(
            values=[
                top["product_name"], top["revenue"].map(lambda x: f"£{x:,.2f}"),
                top["units_sold"], top["category"],
            ],
            fill_color="#0e1117", font=dict(color="#e2e8f0", size=12), align="left", height=28,
        ),
    )])
    fig.update_layout(template=TEMPLATE, title="Top 10 products by revenue",
                     margin=dict(t=60, b=20))
    fig.write_image(out_dir / "06_top_products.png", width=1000, height=450, scale=2)


def export_significance_panel(df, out_dir: Path) -> None:
    sig = compare_dimension_pairs(df, "acquisition_channel", metric_col="revenue")
    sig = sig.copy()
    sig["pair"] = sig["group_a"] + " vs " + sig["group_b"]
    sig["error_low"] = sig["diff"] - sig["ci_low"]
    sig["error_high"] = sig["ci_high"] - sig["diff"]

    colors = ["#e76f51" if s else "#64748b" for s in sig["significant"]]
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=sig["diff"], y=sig["pair"], mode="markers",
        marker=dict(size=10, color=colors),
        error_x=dict(
            type="data", symmetric=False,
            array=sig["error_high"], arrayminus=sig["error_low"],
        ),
    ))
    fig.add_vline(x=0, line_dash="dash", line_color="#94a3b8")
    fig.update_layout(
        template=TEMPLATE,
        title="AOV difference by acquisition channel (95% bootstrap CI)",
        xaxis_title="Difference in mean order value (£)",
        margin=dict(t=60, b=40),
    )
    height = 80 + 40 * len(sig)
    fig.write_image(out_dir / "07_significance_channels.png", width=1000, height=height, scale=2)


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    df = generate_sales()
    export_kpi_row(df, OUT_DIR)
    export_revenue_trend(df, OUT_DIR)
    export_category_revenue(df, OUT_DIR)
    export_region_and_channel(df, OUT_DIR)
    export_top_products_table(df, OUT_DIR)
    export_significance_panel(df, OUT_DIR)
    print(f"Wrote preview images to {OUT_DIR}")


if __name__ == "__main__":
    main()
