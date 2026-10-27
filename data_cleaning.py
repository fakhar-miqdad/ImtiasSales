"""
data_cleaning.py
================
Load, validate, clean and summarise the retail sales dataset (all amounts already in PKR).

Used by:
  * app.py            (Streamlit dashboard)
  * command line      python data_cleaning.py --input data/imtiaz_sales_raw.csv

What it does
------------
1. Strips whitespace from column names and text values.
2. Parses dates and numbers; drops rows that cannot be used.
3. Removes duplicate Transaction IDs / fully duplicate rows.
4. Checks the arithmetic of every row:
      Gross = Quantity x Unit Price
      Discount Amount = Gross x Discount %
      Net = Gross - Discount Amount
   and checks that Year / Month agree with Date. Mismatches are logged (nothing is silently changed).
5. Adds helper columns: Quarter, Month No, Discount Applied (Yes/No), Discount Band.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

MONTH_ORDER = ["January", "February", "March", "April", "May", "June",
               "July", "August", "September", "October", "November", "December"]
QUARTER_ORDER = ["Q1", "Q2", "Q3", "Q4"]
BAND_ORDER = ["No discount", "Up to 5%", "5-10%", "10-20%", "Over 20%"]

REQUIRED = ["Transaction ID", "Date", "Branch", "City", "Category", "Subcategory", "Product Name",
            "Quantity", "Unit Price (PKR)", "Gross Sales (PKR)", "Discount %",
            "Discount Amount (PKR)", "Net Sales (PKR)"]

TEXT_COLS = ["Transaction ID", "Branch", "City", "Category", "Subcategory", "Product"]


# --------------------------------------------------------------------------- #
def load_raw(source) -> pd.DataFrame:
    """Read a CSV / XLSX path (or an uploaded file object) into a DataFrame."""
    name = getattr(source, "name", str(source)).lower()
    if name.endswith(".csv"):
        df = pd.read_csv(source)
    else:
        xl = pd.ExcelFile(source)
        sheet = "Data" if "Data" in xl.sheet_names else xl.sheet_names[0]
        df = xl.parse(sheet)
    df.columns = [str(c).strip() for c in df.columns]
    return df


def band(p: float) -> str:
    if p <= 0:
        return "No discount"
    if p <= 0.05:
        return "Up to 5%"
    if p <= 0.10:
        return "5-10%"
    if p <= 0.20:
        return "10-20%"
    return "Over 20%"


def clean(raw: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Return (clean_df, log)."""
    missing = [c for c in REQUIRED if c not in raw.columns]
    if missing:
        raise ValueError(f"Missing required column(s): {missing}")

    df = raw.copy()
    log: dict = {"rows_in": len(df)}

    for col in df.select_dtypes(include=["object", "string"]).columns:
        df[col] = df[col].astype("string").str.strip()

    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    num = ["Quantity", "Unit Price (PKR)", "Gross Sales (PKR)", "Discount %",
           "Discount Amount (PKR)", "Net Sales (PKR)"]
    for c in num:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    bad = df["Date"].isna() | df[num].isna().any(axis=1)
    log["unusable_rows_dropped"] = int(bad.sum())
    df = df.loc[~bad].copy()

    before = len(df)
    df = df.drop_duplicates().drop_duplicates(subset="Transaction ID")
    log["duplicate_rows_dropped"] = before - len(df)

    df = df.rename(columns={"Product Name": "Product"})

    # arithmetic / consistency checks (logged, not silently fixed)
    log["gross_mismatch_rows"] = int(((df["Quantity"] * df["Unit Price (PKR)"] - df["Gross Sales (PKR)"]).abs() > 0.01).sum())
    log["discount_mismatch_rows"] = int(((df["Gross Sales (PKR)"] * df["Discount %"] - df["Discount Amount (PKR)"]).abs() > 0.01).sum())
    log["net_mismatch_rows"] = int(((df["Gross Sales (PKR)"] - df["Discount Amount (PKR)"] - df["Net Sales (PKR)"]).abs() > 0.01).sum())
    log["year_vs_date_mismatch"] = int((df["Date"].dt.year != df.get("Year", df["Date"].dt.year)).sum())
    log["month_vs_date_mismatch"] = int((df["Date"].dt.month_name() != df.get("Month", df["Date"].dt.month_name())).sum())
    log["city_per_branch_max"] = int(df.groupby("Branch")["City"].nunique().max())
    log["products_with_multiple_prices"] = int((df.groupby("Product")["Unit Price (PKR)"].nunique() > 1).sum())
    log["products"] = int(df["Product"].nunique())

    out = pd.DataFrame({
        "Transaction ID": df["Transaction ID"],
        "Date": df["Date"],
        "Year": df["Date"].dt.year,
        "Quarter": "Q" + df["Date"].dt.quarter.astype(str),
        "Month": df["Date"].dt.month_name(),
        "Month No": df["Date"].dt.month,
        "Branch": df["Branch"],
        "City": df["City"],
        "Category": df["Category"],
        "Subcategory": df["Subcategory"],
        "Product": df["Product"],
        "Quantity": df["Quantity"].astype(int),
        "Unit Price (PKR)": df["Unit Price (PKR)"],
        "Gross Sales (PKR)": df["Gross Sales (PKR)"],
        "Discount %": df["Discount %"],
        "Discount Amount (PKR)": df["Discount Amount (PKR)"],
        "Net Sales (PKR)": df["Net Sales (PKR)"],
        "Discount Applied": np.where(df["Discount %"] > 0, "Yes", "No"),
        "Discount Band": df["Discount %"].map(band),
    }).reset_index(drop=True)

    log["rows_out"] = len(out)
    log["date_min"] = str(out["Date"].min().date())
    log["date_max"] = str(out["Date"].max().date())
    return out, log


# --------------------------------------------------------------------------- #
def kpis(df: pd.DataFrame) -> dict:
    n = len(df)
    gross = float(df["Gross Sales (PKR)"].sum())
    disc = float(df["Discount Amount (PKR)"].sum())
    net = float(df["Net Sales (PKR)"].sum())
    return {
        "Transactions": n,
        "Units Sold": int(df["Quantity"].sum()),
        "Gross Sales (PKR)": gross,
        "Discount Given (PKR)": disc,
        "Net Sales (PKR)": net,
        "Avg Transaction Value (PKR)": net / n if n else 0.0,
        "Discount Rate": disc / gross if gross else 0.0,
    }


def summarize(df: pd.DataFrame, by, order: list | None = None) -> pd.DataFrame:
    """Pivot-style summary (same measures as the Excel step sheets)."""
    g = df.groupby(by, observed=True).agg(
        **{
            "Transactions": ("Transaction ID", "size"),
            "Units": ("Quantity", "sum"),
            "Gross Sales (PKR)": ("Gross Sales (PKR)", "sum"),
            "Discount (PKR)": ("Discount Amount (PKR)", "sum"),
            "Net Sales (PKR)": ("Net Sales (PKR)", "sum"),
        }
    )
    g["Avg Transaction Value (PKR)"] = g["Net Sales (PKR)"] / g["Transactions"]
    g["Discount Rate"] = np.where(g["Gross Sales (PKR)"] > 0, g["Discount (PKR)"] / g["Gross Sales (PKR)"], 0.0)
    tot = g["Net Sales (PKR)"].sum()
    g["Share of Net Sales"] = g["Net Sales (PKR)"] / tot if tot else 0.0
    if order is not None and isinstance(by, str):
        g = g.reindex([o for o in order if o in g.index])
    else:
        g = g.sort_values("Net Sales (PKR)", ascending=False)
    return g.reset_index()


def prepare(source) -> tuple[pd.DataFrame, dict]:
    return clean(load_raw(source))


# --------------------------------------------------------------------------- #
def main() -> None:
    p = argparse.ArgumentParser(description="Validate and clean the retail sales dataset.")
    p.add_argument("--input", default="data/imtiaz_sales_raw.csv")
    p.add_argument("--output", default="data/imtiaz_sales_clean.csv")
    a = p.parse_args()

    df, log = prepare(a.input)
    Path(a.output).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(a.output, index=False)

    print("Cleaning / validation log")
    for k, v in log.items():
        print(f"  {k:30s}: {v}")
    print("\nHeadline KPIs (PKR)")
    for name, val in kpis(df).items():
        print(f"  {name:28s}: {val:,.2f}" if isinstance(val, float) else f"  {name:28s}: {val:,}")
    print(f"\nSaved -> {a.output}")


if __name__ == "__main__":
    main()
