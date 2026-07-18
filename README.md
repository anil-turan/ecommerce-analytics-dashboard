# UK E-Commerce Analytics Dashboard

[![Python](https://img.shields.io/badge/python-3.11-blue)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.38-FF4B4B)](https://streamlit.io/)
[![Plotly](https://img.shields.io/badge/Plotly-5.22-3F4F75)](https://plotly.com/python/)
[![tests](https://img.shields.io/badge/tests-19%20passing-brightgreen)](tests/)
[![Looker Studio](https://img.shields.io/badge/Looker%20Studio-report-4285F4?logo=looker)](https://lookerstudio.google.com/reporting/94e3f261-a530-46c7-86b5-1a6dec8a66af)

An executive-facing, **fully interactive** analytics dashboard — KPI cards,
revenue trend, category/region/channel breakdowns, and a top-products table,
all reactive to sidebar filters (date range, region, category, channel).
Built with Streamlit + Plotly rather than a desktop BI tool so the whole
thing is scriptable, testable, and runnable from a GitHub clone with no
license or desktop install required.

**Dataset:** synthetic but structurally realistic UK e-commerce sales —
3,500 customers, ~2,200 completed orders, July 2024 - June 2026, 6 regions,
6 categories, 5 acquisition channels, with Nov/Dec seasonality and a
tenure-decaying purchase hazard (same generation approach as the sibling
[sql-analytics-case-study](../sql-analytics-case-study) project, applied
here to a single denormalised fact table instead of a relational schema).

---

## Interactive Report (Looker Studio)

**[Ecommerce Channel Performance Report →](https://lookerstudio.google.com/reporting/94e3f261-a530-46c7-86b5-1a6dec8a66af)**

A Looker Studio report built on the same order-level data as the Streamlit
dashboard above: revenue by acquisition channel, monthly revenue trend,
revenue by category, and headline KPIs (total revenue, total orders) —
a second, Google-native BI artifact alongside the Streamlit + Tableau ones,
since Looker Studio is a distinct named tool in many UK Data Analyst job
postings.

---

## Why this project

1. **Interactivity is the point.** Filtering by region/category/channel
   updates every KPI and chart in place — this is what a stakeholder
   actually does with a dashboard, and it's what a static chart export
   can't demonstrate.
2. **KPI logic is separated from the UI** (`src/metrics.py`) and
   independently unit-tested — Streamlit callbacks aren't testable, but the
   numbers they display are, and that's exactly where a silent bug would
   mislead a stakeholder.
3. **No desktop BI license required.** Power BI Desktop is Windows-only and
   Tableau Desktop needs a license; a Streamlit + Plotly dashboard is fully
   open, scriptable, and deployable to Streamlit Community Cloud for free.
4. **Reports whether a gap is real, not just what it is.** `src/significance.py`
   bootstrap-tests every cross-channel/region KPI gap the dashboard surfaces —
   a BI tool will happily chart noise as if it were a finding.

---

## Project Structure

```
ecommerce-analytics-dashboard/
├── src/
│   ├── generator.py           # synthetic UK e-commerce sales generator
│   ├── metrics.py              # KPI/aggregation logic (filter, KPIs, top products)
│   ├── significance.py        # bootstrap significance testing on cross-group KPI gaps
│   ├── app.py                  # the Streamlit app
│   └── export_screenshots.py  # static Plotly exports for this README
├── tests/
│   ├── test_generator.py
│   ├── test_metrics.py        # KPI correctness, independent of the UI
│   └── test_significance.py   # bootstrap CI correctness
├── reports/screenshots/       # static preview images (see below)
├── .streamlit/config.toml     # dark theme config
└── pyproject.toml
```

---

## Preview

**KPI row** — reactive to every filter below it:

![KPI row](reports/screenshots/01_kpi_row.png)

**Revenue trend** (monthly + cumulative overlay):

![Revenue trend](reports/screenshots/02_revenue_trend.png)

**Revenue by category:**

![Category revenue](reports/screenshots/03_category_revenue.png)

**Revenue by region and acquisition channel:**

![Region revenue](reports/screenshots/04_region_revenue.png)
![Channel revenue](reports/screenshots/05_channel_revenue.png)

**Top 10 products:**

![Top products](reports/screenshots/06_top_products.png)

**Is the AOV gap between channels real, or just noise?**

![Significance by channel](reports/screenshots/07_significance_channels.png)

A bar chart showing "Paid Search AOV is £279, Organic is £269" invites a
stakeholder to read a difference into noise. `src/significance.py` runs a
bootstrap 95% confidence interval on the AOV difference between every pair
of acquisition channels — on the full synthetic dataset, **none of the 10
pairwise channel gaps are statistically significant** (every CI crosses
zero), while every pairwise **category** gap is (Electronics' AOV genuinely
differs from Books' — no surprise given the price ranges baked into the
generator, but it's the right control case showing the test isn't just
always saying "not significant"). This is the difference between reporting
a number and knowing whether to act on it.

> These are static exports (`python -m src.export_screenshots`) for
> browsing on GitHub. The live app (`streamlit run src/app.py`) is fully
> interactive — filtering by region, category, date range, or channel
> updates every number and chart above in place. In a live filter test,
> restricting to London alone dropped Total Revenue from £581,983 to
> £175,448 and Orders from 2,204 to 644, with every chart updating
> accordingly.

---

## Quickstart

```bash
# 1. install
pip install -e ".[dev]"

# 2. generate the dataset (optional — the app generates it on first run
#    if data/sales.csv doesn't exist)
python -m src.generator

# 3. run the interactive dashboard
streamlit run src/app.py

# 4. regenerate the static preview images used in this README
python -m src.export_screenshots

# 5. run the tests
pytest tests/ -v
```

### Deploying for free

Push this repo to GitHub, then connect it at
[share.streamlit.io](https://share.streamlit.io) (Streamlit Community
Cloud) pointing at `src/app.py` — no server or license needed, and it gives
a shareable public URL for a CV/LinkedIn link.

---

## Technical Notes

- **Only completed orders count** toward every KPI and chart — the
  dashboard's caption states this explicitly, matching the convention in
  the SQL case study project.
- **`src/metrics.py` is UI-agnostic**: `filter_sales`, `compute_kpis`,
  `revenue_by_period`, `revenue_by_dimension`, and `top_products` take and
  return plain DataFrames, so they're tested directly with `pytest` rather
  than through Streamlit's app-testing harness.
- **Same tenure-decaying purchase hazard as the SQL case study project** —
  each customer's monthly ordering probability decays with months since
  signup (boosted in Nov/Dec) so the revenue trend has genuine growth and
  seasonality structure rather than being uniform noise.
- **`@st.cache_data`** on the data loader avoids regenerating/reloading the
  dataset on every filter interaction.
- **`src/significance.py`'s bootstrap is from-scratch** (no `scipy.stats`
  dependency added) — resamples each group independently with replacement
  and reports the CI on the difference in means; a gap is "significant"
  when that CI excludes zero. Recomputed live on whatever the sidebar
  filters currently select, not just on the full dataset.
