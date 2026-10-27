"""
app.py - Interactive Retail Sales Dashboard (PKR)
Run:  streamlit run app.py      (or use run.bat on Windows / run.sh on Mac-Linux)
"""
from pathlib import Path

import plotly.express as px
import streamlit as st

import data_cleaning as dc

st.set_page_config(page_title="Retail Sales Dashboard (PKR)", page_icon="📊", layout="wide")

DEFAULT_FILE = Path(__file__).parent / "data" / "imtiaz_sales_raw.csv"
PALETTE = ["#1F3A5F", "#2A9D8F", "#F4A261", "#E9C46A", "#E76F51", "#6C8EBF", "#8E7DBE", "#9AA5B1"]


@st.cache_data(show_spinner="Loading and cleaning data...")
def load(source):
    return dc.prepare(source)


def pkr(x: float) -> str:
    return f"PKR {x:,.0f}"


def fmt_m(x: float) -> str:
    return f"PKR {x / 1e6:,.2f}M"


# ----------------------------------------------------------------- data
st.sidebar.title("Controls")
upload = st.sidebar.file_uploader("Use your own file (CSV / XLSX)", type=["csv", "xlsx"],
                                  help="Must contain the same columns as data/imtiaz_sales_raw.csv")
try:
    if upload is not None:
        df, log = load(upload)
    elif DEFAULT_FILE.exists():
        df, log = load(str(DEFAULT_FILE))
    else:
        st.error("No data found. Put imtiaz_sales_raw.csv in the data/ folder or upload a file.")
        st.stop()
except Exception as e:  # noqa: BLE001
    st.error(f"Could not read the data: {e}")
    st.stop()

# ----------------------------------------------------------------- slicers
st.sidebar.markdown("---")
st.sidebar.subheader("Slicers")
st.sidebar.caption("Leave a slicer empty = no filter (All).")
sel_year = st.sidebar.multiselect("Year", sorted(df["Year"].unique()))
sel_q = st.sidebar.multiselect("Quarter", dc.QUARTER_ORDER)
sel_month = st.sidebar.multiselect("Month", [m for m in dc.MONTH_ORDER if m in set(df["Month"])])
sel_branch = st.sidebar.multiselect("Branch", sorted(df["Branch"].unique()))
sel_cat = st.sidebar.multiselect("Category", sorted(df["Category"].unique()))
sub_opts = sorted(df[df["Category"].isin(sel_cat)]["Subcategory"].unique() if sel_cat else df["Subcategory"].unique())
sel_sub = st.sidebar.multiselect("Subcategory", sub_opts)
sel_disc = st.sidebar.multiselect("Discount Applied", ["Yes", "No"])

f = df
for col, sel in [("Year", sel_year), ("Quarter", sel_q), ("Month", sel_month), ("Branch", sel_branch),
                 ("Category", sel_cat), ("Subcategory", sel_sub), ("Discount Applied", sel_disc)]:
    if sel:
        f = f[f[col].isin(sel)]

# ----------------------------------------------------------------- header + KPIs
st.title("📊 Retail Sales Analysis Dashboard (PKR)")
st.caption(f"{df['Date'].min():%d %b %Y} to {df['Date'].max():%d %b %Y}  |  showing {len(f):,} of {len(df):,} transactions  |  "
           "All amounts in Pakistani Rupees")

if f.empty:
    st.warning("No rows match the selected slicers. Clear a slicer to continue.")
    st.stop()

k = dc.kpis(f)
c = st.columns(6)
c[0].metric("Transactions", f"{k['Transactions']:,}")
c[1].metric("Gross Sales", fmt_m(k["Gross Sales (PKR)"]))
c[2].metric("Discount Given", pkr(k["Discount Given (PKR)"]))
c[3].metric("Net Sales", fmt_m(k["Net Sales (PKR)"]))
c[4].metric("Avg Transaction Value", pkr(k["Avg Transaction Value (PKR)"]))
c[5].metric("Discount Rate", f"{k['Discount Rate']:.1%}")


def style(fig, h=380):
    fig.update_layout(height=h, margin=dict(l=10, r=10, t=50, b=10), legend_title_text="")
    return fig


tab1, tab2, tab3, tab4, tab5 = st.tabs(["Overview", "Branch & Category", "Products", "Discounts", "Data"])

with tab1:
    ym = f.groupby(["Month No", "Month", "Year"], as_index=False)["Net Sales (PKR)"].sum().sort_values("Month No")
    ym["Year"] = ym["Year"].astype(str)
    a, b = st.columns(2)
    a.plotly_chart(style(px.line(ym, x="Month", y="Net Sales (PKR)", color="Year", markers=True,
                                 color_discrete_sequence=PALETTE, title="Monthly Net Sales by Year (PKR)")),
                   use_container_width=True)
    y = dc.summarize(f, "Year", order=sorted(f["Year"].unique()))
    y["Year"] = y["Year"].astype(str)
    b.plotly_chart(style(px.bar(y, x="Year", y=["Gross Sales (PKR)", "Net Sales (PKR)"], barmode="group",
                                color_discrete_sequence=PALETTE, title="Gross vs Net Sales by Year (PKR)")),
                   use_container_width=True)
    st.dataframe(y, use_container_width=True, hide_index=True)

with tab2:
    br = dc.summarize(f, "Branch")
    ca = dc.summarize(f, "Category")
    a, b = st.columns(2)
    a.plotly_chart(style(px.bar(br, x="Branch", y="Net Sales (PKR)", color_discrete_sequence=PALETTE,
                                title="Net Sales by Branch (PKR)")), use_container_width=True)
    b.plotly_chart(style(px.bar(ca, x="Net Sales (PKR)", y="Category", orientation="h",
                                color_discrete_sequence=PALETTE, title="Net Sales by Category (PKR)")
                         .update_yaxes(autorange="reversed")), use_container_width=True)
    x = f.pivot_table(index="Branch", columns="Category", values="Net Sales (PKR)", aggfunc="sum", fill_value=0)
    st.plotly_chart(style(px.imshow(x, text_auto=",.0f", aspect="auto", color_continuous_scale="Teal",
                                    title="Branch x Category - Net Sales (PKR)"), 380), use_container_width=True)
    st.dataframe(dc.summarize(f, "Subcategory"), use_container_width=True, hide_index=True)

with tab3:
    st.info("Note: the same product appears at very different unit prices in this dataset, so treat product ranks as indicative.")
    top = dc.summarize(f, "Product").head(10)
    st.plotly_chart(style(px.bar(top, x="Net Sales (PKR)", y="Product", orientation="h",
                                 color_discrete_sequence=PALETTE, title="Top 10 Products by Net Sales (PKR)")
                          .update_yaxes(autorange="reversed"), 430), use_container_width=True)
    st.dataframe(dc.summarize(f, "Product").head(30), use_container_width=True, hide_index=True)

with tab4:
    bd = dc.summarize(f, "Discount Band", order=dc.BAND_ORDER)
    cd = dc.summarize(f, "Category").sort_values("Discount (PKR)", ascending=False)
    a, b = st.columns(2)
    a.plotly_chart(style(px.bar(bd, x="Discount Band", y="Transactions", color_discrete_sequence=PALETTE,
                                title="Transactions by Discount Band")), use_container_width=True)
    b.plotly_chart(style(px.bar(cd, x="Discount (PKR)", y="Category", orientation="h",
                                color_discrete_sequence=PALETTE, title="Discount Given by Category (PKR)")
                         .update_yaxes(autorange="reversed")), use_container_width=True)
    st.dataframe(bd, use_container_width=True, hide_index=True)

with tab5:
    with st.expander("Cleaning / validation log"):
        st.json(log)
    st.dataframe(f.head(1000), use_container_width=True, hide_index=True)
    st.download_button("Download filtered data (CSV)", f.to_csv(index=False).encode("utf-8"),
                       file_name="retail_sales_filtered_pkr.csv", mime="text/csv")
