"""Synthetic UK e-commerce sales dataset generator, denormalised into a
single fact table (one row per order line item) -- the shape a BI tool
actually consumes, as opposed to the normalised relational schema a SQL
case study would use.

Not real data: no public dataset has the needed size, UK-region/channel
mix, and known seasonal/growth structure, so every "insight" the dashboard
surfaces can be traced back to a parameter here.
"""

from __future__ import annotations

from datetime import date, timedelta

import numpy as np
import pandas as pd

START_DATE = date(2024, 7, 1)
END_DATE = date(2026, 6, 30)
N_CUSTOMERS = 3500

REGIONS = ["London", "South East", "North West", "Scotland", "West Midlands", "Wales"]
CHANNELS = ["Organic Search", "Paid Search", "Social Media", "Referral", "Email"]
CATEGORIES = {
    "Electronics": (25, 800),
    "Home & Garden": (10, 300),
    "Fashion": (8, 150),
    "Beauty": (5, 60),
    "Sports & Outdoors": (10, 250),
    "Books": (5, 30),
}
PRODUCT_NAMES = {
    "Electronics": [
        "Wireless Earbuds", "Smart Speaker", "4K Monitor", "Laptop Stand", "Power Bank",
    ],
    "Home & Garden": ["Garden Chair", "LED Lamp", "Storage Box", "Plant Pot", "Cushion Set"],
    "Fashion": ["Denim Jacket", "Running Shoes", "Wool Scarf", "Leather Belt", "Sunglasses"],
    "Beauty": ["Face Serum", "Shampoo Bar", "Lip Balm Set", "Hand Cream", "Body Wash"],
    "Sports & Outdoors": [
        "Yoga Mat", "Cycling Helmet", "Camping Tent", "Water Bottle", "Hiking Boots",
    ],
    "Books": ["Fiction Bestseller", "Cookbook", "Biography", "Business Book", "Children's Book"],
}


def _months_between(signup: date, end: date) -> pd.PeriodIndex:
    return pd.period_range(pd.Period(signup, freq="M"), pd.Period(end, freq="M"), freq="M")


def generate_sales(seed: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    n_customers = N_CUSTOMERS
    total_days = (END_DATE - START_DATE).days

    signup_offsets = np.sort(
        rng.triangular(0, total_days, total_days, size=n_customers)
    ).astype(int)
    customer_ids = np.arange(1, n_customers + 1)
    signup_dates = [START_DATE + timedelta(days=int(d)) for d in signup_offsets]
    regions = rng.choice(REGIONS, size=n_customers, p=[0.28, 0.18, 0.16, 0.14, 0.14, 0.10])
    channels = rng.choice(CHANNELS, size=n_customers, p=[0.32, 0.24, 0.20, 0.14, 0.10])
    loyalty = rng.beta(2, 5, size=n_customers)

    rows = []
    order_id = 1
    for i in range(n_customers):
        signup = signup_dates[i]
        region = regions[i]
        channel = channels[i]
        loy = loyalty[i]

        for m, period in enumerate(_months_between(signup, END_DATE)):
            month_start = max(period.start_time.date(), signup)
            month_end = min(period.end_time.date(), END_DATE)
            if month_start > month_end:
                continue

            seasonal = 2.2 if period.month in (11, 12) else 1.0
            prob = min(0.45 * loy * 0.85**m * seasonal, 0.95)
            if rng.random() >= prob:
                continue

            n_orders_this_month = 1 + rng.poisson(loy * 0.25)
            span_days = (month_end - month_start).days
            for _ in range(n_orders_this_month):
                order_date = month_start + timedelta(days=int(rng.integers(0, span_days + 1)))
                status = rng.choice(["completed", "returned", "cancelled"], p=[0.90, 0.06, 0.04])
                category = rng.choice(list(CATEGORIES.keys()))
                low, high = CATEGORIES[category]
                unit_price = round(rng.uniform(low, high), 2)
                quantity = int(rng.integers(1, 4))
                discount_pct = int(rng.choice([0, 0, 0, 5, 10, 15, 20],
                                              p=[0.55, 0.1, 0.1, 0.1, 0.08, 0.05, 0.02]))
                product_name = rng.choice(PRODUCT_NAMES[category])
                revenue = round(quantity * unit_price * (1 - discount_pct / 100.0), 2)

                rows.append({
                    "order_id": order_id,
                    "order_date": order_date,
                    "customer_id": customer_ids[i],
                    "region": region,
                    "acquisition_channel": channel,
                    "category": category,
                    "product_name": product_name,
                    "quantity": quantity,
                    "unit_price": unit_price,
                    "discount_pct": discount_pct,
                    "revenue": revenue,
                    "status": status,
                })
                order_id += 1

    df = pd.DataFrame(rows)
    df["order_date"] = pd.to_datetime(df["order_date"])
    return df


if __name__ == "__main__":
    from pathlib import Path

    out = Path(__file__).resolve().parents[1] / "data" / "sales.csv"
    out.parent.mkdir(parents=True, exist_ok=True)
    generate_sales().to_csv(out, index=False)
    print(f"Wrote {out}")
