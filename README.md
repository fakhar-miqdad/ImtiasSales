# Retail Sales Analysis (PKR)

A complete analysis package for `imitiaz_sales.xlsx` - 1,000 retail transactions, 2 Jan 2023 to 31 Dec 2025,
4 branches (Karachi, Lahore, Islamabad, Hyderabad), 8 categories, 34 subcategories, 138 products.
All amounts are in **Pakistani Rupees (PKR)** (the source file is already in PKR, so no conversion is applied).

## What is inside

| File / folder | Purpose |
|---|---|
| `reports/imtiaz_sales_analysis_report_PKR.xlsx` | Excel report: Dashboard (KPIs, 6 charts, 6 dropdown slicers), Report, Step1-Step9 pivot sheets with charts, Dash_Calc, Data |
| `app.py` | Streamlit web dashboard with real multi-select slicers, KPIs, charts, CSV download |
| `data_cleaning.py` | Loads, validates, cleans and summarises the data (used by the app; also runs from the command line) |
| `data/imtiaz_sales_raw.csv` | Raw transactions exported from the supplied workbook |
| `requirements.txt` | Python packages |
| `run.bat` / `run.sh` | One-click launchers for Windows / Mac-Linux |

## Quick start

**Windows:** double-click `run.bat`
**Mac / Linux:** `chmod +x run.sh && ./run.sh`

The launcher creates a `.venv`, installs `requirements.txt` and opens the dashboard at http://localhost:8501.
Python 3.9 or newer is required.

Manual start:

```
pip install -r requirements.txt
streamlit run app.py
```

## Command-line validation / cleaning

```
python data_cleaning.py --input data/imtiaz_sales_raw.csv --output data/imtiaz_sales_clean.csv
```

Prints a validation log and the headline KPIs, and saves the cleaned file with helper columns.

## Cleaning and validation steps

1. Trim whitespace in column names and text values.
2. Parse dates and numbers; drop unusable rows (none found).
3. Remove duplicate rows / Transaction IDs (none found).
4. Check on every row: Gross = Quantity x Unit Price, Discount = Gross x Discount %, Net = Gross - Discount (all pass), and that Year / Month agree with Date (all pass).
5. Add helper columns: Quarter, Month No, Discount Applied (Yes/No), Discount Band (No discount, Up to 5%, 5-10%, 10-20%, Over 20%).

No source values are changed.

## Definitions

* **Net Sales** = Gross Sales - Discount Amount.
* **Avg Transaction Value** = Net Sales / Transactions.
* **Discount Rate** = Discount Amount / Gross Sales.

## Important notes

* **Price consistency:** every product appears at several different unit prices (for example *Sandwich Maker* from PKR 1,550 to PKR 85,000). Row arithmetic is consistent, but product names do not map to one price. The large Electronics share (about 64% of net sales) and the product rankings depend on this. Please verify against the source price list.
* The Excel pivot sheets are formula-driven pivot-style tables (COUNTIFS / SUMIFS) and the Excel slicers are dropdown cells. They are not native PivotTable objects or slicer objects. The Streamlit app provides true multi-select slicers.
* Each calendar month has only three years of observations, so the seasonality view is indicative.
"# ImtiasSales" 
