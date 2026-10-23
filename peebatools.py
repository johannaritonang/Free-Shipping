"""Helpers for the Peeba hypothesis-testing notebook.

`load()` rebuilds the order-level unit economics with the same rules as the Power BI model
(implied FX to TWD, commission, shipping, incentives, returns, payment fees, contribution margin, new vs repeat retailer,
receivable status), so the numbers reconcile with the dashboard *Shipping Pays the Bills*.
"""
from pathlib import Path

import numpy as np
import pandas as pd

# ---------------------------------------------------------------- palette (matches the Power BI report)
SLATE, SEA, SAND, CORAL, ORANGE, LILAC, GREY, INK, MUTED, LINE = (
    "#264653", "#2A9D8F", "#E9C46A", "#E76F51", "#F4A261", "#8E7DBE", "#B8B8B8", "#1E293B", "#64748B", "#E7E2D8")


def style_charts():
    import matplotlib.pyplot as plt
    plt.rcParams.update({"figure.dpi": 110, "axes.spines.top": False, "axes.spines.right": False, "axes.edgecolor": "#CFC8BA",
                         "axes.titleweight": "bold", "axes.titlesize": 12, "axes.titlecolor": INK, "axes.labelcolor": MUTED,
                         "xtick.color": MUTED, "ytick.color": MUTED, "figure.facecolor": "white", "axes.facecolor": "white"})


def find_workbook(folders):
    """First .xlsx whose name mentions 'interview' (else the first .xlsx) in the given folders."""
    for folder in folders:
        folder = Path(folder)
        if folder.exists():
            files = sorted(f for f in folder.glob("*.xlsx") if not f.name.startswith("~$"))
            pref = [f for f in files if "interview" in f.name.lower()]
            if pref or files:
                return (pref or files)[0]
    return None


def load(path):
    raw = pd.read_excel(path, sheet_name="Raw Data", header=1)   # row 1 = column descriptions, row 2 = headers
    d = raw.loc[:, [c for c in raw.columns if not str(c).startswith("Unnamed")]].copy()
    for c in ["create_date", "due_date", "brand_paydate", "payout_date", "last_payment_date", "First Order Month", "Brand Join Date", "Retailer Join Date"]:
        d[c] = pd.to_datetime(d[c], errors="coerce")
    for c in ["subtotal", "commission_value", "commission", "brand_shipping_cost", "brand_total_payout", "item_subtotal", "coupon_discount",
              "shipping_cost", "return_value", "peeba_cash", "collect_from_retailer", "Collected Amount", "Airwallex Fees (%)", "Stripe Fees (%)"]:
        d[c] = pd.to_numeric(d[c], errors="coerce").fillna(0.0)
    d["Brand Category"] = d["Brand Category"].astype(str).str.replace("_", " ").str.title()
    d["Retailer Type"] = d["Retailer Type"].astype(str).str.replace("_", " ").str.title()

    fx = np.where(d.subtotal == 0, 1.0, d.item_subtotal / d.subtotal.replace(0, np.nan))
    o = pd.DataFrame({"order_id": d.uid.astype(str), "brand_id": d.brand_id.astype(str), "retailer_id": d.retailer_id.astype(str),
                      "date": d.create_date, "due_date": d.due_date, "paid_date": d.last_payment_date,
                      "brand_pay_date": d.brand_paydate, "brand_payout_date": d.payout_date,
                      "commission_pct": d.commission, "brand_category": d["Brand Category"], "brand_country": d["Brand Country"],
                      "retailer_type": d["Retailer Type"], "retailer_source": d["Retailer Source"], "first_order_month": d["First Order Month"]})
    o["gmv"] = d.item_subtotal
    o["commission"] = d.commission_value * fx
    o["shipping_charged"] = d.shipping_cost
    o["shipping_paid_to_brand"] = d.brand_shipping_cost * fx
    o["coupons"] = d.coupon_discount
    o["peeba_cash"] = d.peeba_cash
    o["returns"] = d.return_value
    o["fee_payout"] = d.brand_total_payout * fx * d["Airwallex Fees (%)"]
    o["fee_collection"] = d.collect_from_retailer.clip(lower=0) * d["Stripe Fees (%)"]
    o["payment_fees"] = o.fee_payout + o.fee_collection
    o["receivable"] = d.collect_from_retailer
    o["net_revenue"] = o.commission + o.shipping_charged - o.shipping_paid_to_brand
    o["cm"] = o.net_revenue - o.coupons - o.peeba_cash - o.returns - o.payment_fees
    o["shipping_margin"] = o.shipping_charged - o.shipping_paid_to_brand
    o["cm_excl_shipping"] = o.cm - o.shipping_margin
    o["shipping_pct"] = o.shipping_charged / o.gmv
    o["new_retailer"] = o.first_order_month.dt.to_period("M") == o.date.dt.to_period("M")
    o["incentive"] = (o.coupons + o.peeba_cash) > 0
    as_of = pd.concat([o.date, o.brand_payout_date, o.paid_date]).max()
    o["as_of"] = as_of
    o["days_late"] = (o.paid_date - o.due_date).dt.days
    o["receivable_status"] = np.select(
        [o.paid_date.notna() & (o.paid_date <= o.due_date), o.paid_date.notna(), o.due_date < as_of],
        ["Paid on time", "Paid late", "Overdue"], "Open - not due")
    o["month"] = o.date.dt.to_period("M").dt.to_timestamp()
    return o.sort_values("date").reset_index(drop=True)


def twd(v):
    return f"TWD {v / 1e6:,.2f}M" if abs(v) >= 1e6 else f"TWD {v / 1e3:,.0f}K"


def bootstrap(df, stat, n=5000, seed=7):
    """Bootstrap distribution of stat(df) over orders (rows resampled with replacement)."""
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(df), (n, len(df)))
    return np.array([stat(df.iloc[i]) for i in idx])
