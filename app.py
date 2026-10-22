
from pathlib import Path
from io import BytesIO

import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import streamlit as st

# ==========================================================
# INDIA OIL & GAS INDUSTRY ANALYTICS DASHBOARD
# Data source: PPAC
# ==========================================================

st.set_page_config(
    page_title="India Oil & Gas Industry Analytics",
    page_icon="🛢️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# -------------------- Dashboard Styling --------------------

st.markdown("""
<style>
.block-container {
    padding-top: 1.1rem;
    padding-bottom: 1.8rem;
    max-width: 1600px;
}
.hero {
    padding: 1.2rem;
    border-radius: 16px;
    background: linear-gradient(115deg, #0b2545, #155e75, #0f766e);
    color: white;
    margin-bottom: 1rem;
}
.hero h1 {
    font-size: 2rem;
    color: white;
}
.hero p {
    color: #dcecf5;
    font-size: 1rem;
}
div[data-testid="stMetric"] {
    background: #f4f8fb;
    border: 1px solid #dce8f0;
    padding: 13px 15px;
    border-radius: 13px;
}
.insight {
    background: #f2f8fb;
    border-left: 4px solid #0e7490;
    padding: 10px 13px;
    border-radius: 8px;
    margin: 5px 0;
}
.source {
    font-size: 0.85rem;
    color: #526477;
}
h2, h3 {
    color: #102a43;
}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="hero">
    <h1>🛢️ India Oil &amp; Gas Industry Analytics</h1>
    <p>
        From crude supply to refining, petroleum demand and natural gas
        | Annual analysis based on PPAC data
    </p>
</div>
""", unsafe_allow_html=True)

# -------------------- Load Excel Workbook --------------------

DATA_FILE = Path(__file__).with_name("PPAC_Data.xlsx")


@st.cache_data(show_spinner=False)
def load_workbook(file_bytes):
    excel_file = pd.ExcelFile(BytesIO(file_bytes))

    expected_sheets = [
        "Dashboard_Annual",
        "Petroleum_Products",
        "Petroleum_Totals",
        "Domestic_Crude",
        "Crude_Imports",
        "Refining_Capacity",
        "Refinery_Throughput",
        "Natural_Gas",
    ]

    missing = set(expected_sheets) - set(excel_file.sheet_names)

    if missing:
        raise ValueError(
            "Missing worksheet(s): " + ", ".join(sorted(missing))
        )

    sheets = {
        name: pd.read_excel(excel_file, sheet_name=name)
        for name in expected_sheets
    }

    for frame in sheets.values():
        if "Financial Year" in frame.columns:
            frame["Financial Year"] = (
                frame["Financial Year"].astype(str).str.strip()
            )

    return sheets


uploaded_file = st.file_uploader(
    "Upload PPAC_Data.xlsx, or keep it beside app.py",
    type=["xlsx"],
    help="Upload the consolidated PPAC workbook containing the required sheets.",
)

try:
    if uploaded_file is not None:
        sheets = load_workbook(uploaded_file.getvalue())
        source_label = "Uploaded PPAC_Data.xlsx"

    elif DATA_FILE.exists():
        sheets = load_workbook(DATA_FILE.read_bytes())
        source_label = "PPAC_Data.xlsx in application folder"

    else:
        st.info(
            "Please upload PPAC_Data.xlsx to display the dashboard."
        )
        st.stop()

except Exception as error:
    st.error(f"Could not load the Excel workbook: {error}")
    st.stop()


annual = sheets["Dashboard_Annual"].copy()
products = sheets["Petroleum_Products"].copy()
gas = sheets["Natural_Gas"].copy()

# Convert numeric columns where possible
for frame in [annual, products, gas]:
    for column in frame.columns:
        if column != "Financial Year":
            converted = pd.to_numeric(frame[column], errors="coerce")
            if converted.notna().any():
                frame[column] = converted

# -------------------- Validate Required Columns --------------------

required_columns = [
    "Financial Year",
    "Petroleum Total MMT",
    "Domestic Crude MMT",
    "Crude Imports MMT",
    "Crude Import Share %",
    "Refining Capacity MMTPA",
    "Refinery Throughput MMT",
    "Natural Gas MMSCM",
    "Gas Net Production MMSCM",
    "LNG Imports MMSCM",
]

missing_columns = [
    column for column in required_columns
    if column not in annual.columns
]

if missing_columns:
    st.error(
        "Dashboard_Annual is missing these columns: "
        + ", ".join(missing_columns)
    )
    st.stop()

years = annual["Financial Year"].dropna().astype(str).tolist()

if not years:
    st.error("No financial years were found in the annual worksheet.")
    st.stop()

annual = annual.sort_values("Financial Year").reset_index(drop=True)
years = annual["Financial Year"].astype(str).tolist()

# -------------------- Financial Year Filter --------------------

filter_col, info_col = st.columns([1, 2.5])

with filter_col:
    selected_year = st.selectbox(
        "Select financial year",
        years,
        index=len(years) - 1,
    )

with info_col:
    st.markdown(
        f"""
        <div style="padding-top:1.9rem;color:#5c6f82">
        <b>Data source:</b> {source_label}
        &nbsp; | &nbsp;
        <b>Coverage:</b> {years[0]} to {years[-1]}
        &nbsp; | &nbsp;
        <b>Selected year:</b> {selected_year}
        </div>
        """,
        unsafe_allow_html=True,
    )

selected_row = annual[
    annual["Financial Year"].astype(str) == selected_year
].iloc[0]

products_year = products[
    products["Financial Year"].astype(str) == selected_year
].copy()

gas_year = gas[
    gas["Financial Year"].astype(str) == selected_year
].copy()


def format_number(value, digits=1):
    try:
        return f"{float(value):,.{digits}f}"
    except (TypeError, ValueError):
        return "N/A"


# -------------------- KPI Cards --------------------

st.markdown("### Industry Snapshot")

k1, k2, k3, k4, k5 = st.columns(5)

k1.metric(
    "Petroleum consumption",
    f"{format_number(selected_row['Petroleum Total MMT'])} MMT",
)
k2.metric(
    "Crude oil imports",
    f"{format_number(selected_row['Crude Imports MMT'])} MMT",
)
k3.metric(
    "Crude import share",
    f"{format_number(selected_row['Crude Import Share %'])}%",
)
k4.metric(
    "Domestic crude output",
    f"{format_number(selected_row['Domestic Crude MMT'])} MMT",
)
k5.metric(
    "Refinery throughput",
    f"{format_number(selected_row['Refinery Throughput MMT'])} MMT",
)

st.markdown("## Four Connected Industry Views")

st.caption(
    "Explore crude availability, refinery processing, petroleum demand, "
    "and natural gas supply using the selected financial year."
)

# ==========================================================
# CHART 1: DOMESTIC CRUDE PRODUCTION VS CRUDE IMPORTS
# ==========================================================

st.markdown("### 1. Crude Supply: Domestic Production and Imports")

chart_col, gauge_col = st.columns([1.7, 1])

with chart_col:
    fig1 = go.Figure()

    fig1.add_trace(
        go.Bar(
            x=annual["Financial Year"],
            y=annual["Domestic Crude MMT"],
            name="Domestic crude production",
            marker_color="#1769aa",
            text=annual["Domestic Crude MMT"].round(1),
            textposition="outside",
        )
    )

    fig1.add_trace(
        go.Bar(
            x=annual["Financial Year"],
            y=annual["Crude Imports MMT"],
            name="Crude imports",
            marker_color="#18a999",
            text=annual["Crude Imports MMT"].round(1),
            textposition="outside",
        )
    )

    fig1.update_layout(
        barmode="group",
        height=360,
        margin=dict(l=10, r=10, t=25, b=10),
        xaxis_title="Financial year",
        yaxis_title="Volume (MMT)",
        legend=dict(orientation="h", y=1.12, x=0),
    )

    fig1.update_yaxes(gridcolor="#e8eef3")

    st.plotly_chart(fig1, use_container_width=True)

with gauge_col:
    current_share = float(selected_row["Crude Import Share %"])

    fig_gauge = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=current_share,
            number={
                "suffix": "%",
                "font": {"size": 34, "color": "#0b2545"},
            },
            title={
                "text": (
                    "Crude Import Share<br>"
                    f"<span style='font-size:12px'>{selected_year}</span>"
                )
            },
            gauge={
                "axis": {"range": [0, 100], "ticksuffix": "%"},
                "bar": {"color": "#e58e26"},
                "steps": [
                    {"range": [0, 50], "color": "#e9f5f2"},
                    {"range": [50, 80], "color": "#fff2d8"},
                    {"range": [80, 100], "color": "#fde8e7"},
                ],
                "threshold": {
                    "line": {"color": "#0b2545", "width": 3},
                    "value": 90,
                },
            },
        )
    )

    fig_gauge.update_layout(
        height=260,
        margin=dict(l=20, r=20, t=65, b=10),
    )

    st.plotly_chart(fig_gauge, use_container_width=True)

    starting_share = float(annual.iloc[0]["Crude Import Share %"])
    ending_share = float(annual.iloc[-1]["Crude Import Share %"])

    st.markdown(
        f"""
        <div class="insight">
        Crude import share changed from <b>{starting_share:.1f}%</b>
        in {years[0]} to <b>{ending_share:.1f}%</b> in {years[-1]}.
        This indicates the importance of imported crude in India's supply mix.
        </div>
        """,
        unsafe_allow_html=True,
    )

# ==========================================================
# CHART 2: REFINING CAPACITY VS THROUGHPUT
# ==========================================================

st.markdown("### 2. Refining: Capacity Compared with Throughput")

fig2 = go.Figure()

fig2.add_trace(
    go.Bar(
        x=annual["Financial Year"],
        y=annual["Refining Capacity MMTPA"],
        name="Capacity reference (MMTPA)",
        marker_color="#1769aa",
        text=annual["Refining Capacity MMTPA"].round(1),
        textposition="outside",
    )
)

fig2.add_trace(
    go.Bar(
        x=annual["Financial Year"],
        y=annual["Refinery Throughput MMT"],
        name="Annual throughput (MMT)",
        marker_color="#18a999",
        text=annual["Refinery Throughput MMT"].round(1),
        textposition="outside",
    )
)

fig2.update_layout(
    barmode="group",
    height=350,
    margin=dict(l=10, r=10, t=25, b=10),
    xaxis_title="Financial year",
    yaxis_title="Capacity / throughput (million tonnes)",
    legend=dict(orientation="h", y=1.12, x=0),
)

fig2.update_yaxes(gridcolor="#e8eef3")

st.plotly_chart(fig2, use_container_width=True)

st.markdown(
    """
    <div class="insight">
    <b>Interpretation:</b> Refinery throughput represents material processed
    over a year, while capacity is a capacity reference. If throughput
    appears above capacity, check the original source definitions and
    reference dates before drawing conclusions about utilization.
    </div>
    """,
    unsafe_allow_html=True,
)

# ==========================================================
# CHART 3: PETROLEUM PRODUCT-WISE CONSUMPTION
# ==========================================================

st.markdown("### 3. Petroleum Demand: Product-wise Consumption")

if products_year.empty:
    st.warning(
        f"No product-wise records were found for {selected_year}."
    )

elif "MMT (calculated)" not in products_year.columns:
    st.error(
        "The Petroleum_Products sheet must contain "
        "the 'MMT (calculated)' column."
    )

elif "Product" not in products_year.columns:
    st.error(
        "The Petroleum_Products sheet must contain a 'Product' column."
    )

else:
    products_year["MMT (calculated)"] = pd.to_numeric(
        products_year["MMT (calculated)"],
        errors="coerce",
    )

    products_year = products_year.dropna(
        subset=["MMT (calculated)"]
    )

    products_year = products_year.sort_values(
        "MMT (calculated)",
        ascending=True,
    )

    total_product = products_year["MMT (calculated)"].sum()

    if total_product > 0:
        products_year["Share (%)"] = (
            products_year["MMT (calculated)"] / total_product * 100
        )
    else:
        products_year["Share (%)"] = 0.0

    if not products_year.empty:
        fig3 = px.bar(
            products_year,
            x="MMT (calculated)",
            y="Product",
            orientation="h",
            text=products_year.apply(
                lambda row: (
                    f"{row['MMT (calculated)']:.1f} MMT · "
                    f"{row['Share (%)']:.1f}%"
                ),
                axis=1,
            ),
            color="MMT (calculated)",
            color_continuous_scale=["#9bd9e8", "#1769aa"],
            labels={
                "MMT (calculated)": "Consumption (MMT)",
                "Product": "",
            },
        )

        fig3.update_traces(
            textposition="outside",
            cliponaxis=False,
        )

        fig3.update_layout(
            height=max(340, 35 * len(products_year) + 80),
            margin=dict(l=10, r=100, t=15, b=10),
            coloraxis_showscale=False,
            xaxis=dict(gridcolor="#e8eef3"),
        )

        st.plotly_chart(fig3, use_container_width=True)

        top_products = products_year.nlargest(
            2, "MMT (calculated)"
        )

        top_two_share = (
            top_products["MMT (calculated)"].sum()
            / total_product * 100
            if total_product > 0
            else 0
        )

        top_names = " and ".join(
            top_products["Product"].astype(str).tolist()
        )

        st.markdown(
            f"""
            <div class="insight">
            The two largest product categories in {selected_year} are
            <b>{top_names}</b>. Together, they account for approximately
            <b>{top_two_share:.1f}%</b> of the total in the product-wise sheet.
            </div>
            """,
            unsafe_allow_html=True,
        )

# ==========================================================
# CHART 4: NATURAL GAS PRODUCTION VS LNG IMPORTS
# ==========================================================

st.markdown("### 4. Natural Gas: Domestic Production and LNG Imports")

required_gas_columns = [
    "Financial Year",
    "Net Production MMSCM",
    "LNG Imports MMSCM",
]

missing_gas_columns = [
    column for column in required_gas_columns
    if column not in gas.columns
]

if missing_gas_columns:
    st.error(
        "Natural_Gas is missing column(s): "
        + ", ".join(missing_gas_columns)
    )
    st.stop()

gas_chart = gas.sort_values("Financial Year").copy()

gas_chart["LNG Share (%)"] = (
    gas_chart["LNG Imports MMSCM"]
    / (
        gas_chart["Net Production MMSCM"]
        + gas_chart["LNG Imports MMSCM"]
    ).replace(0, float("nan"))
    * 100
)

fig4 = go.Figure()

fig4.add_trace(
    go.Bar(
        x=gas_chart["Financial Year"],
        y=gas_chart["Net Production MMSCM"],
        name="Domestic net production",
        marker_color="#1769aa",
    )
)

fig4.add_trace(
    go.Bar(
        x=gas_chart["Financial Year"],
        y=gas_chart["LNG Imports MMSCM"],
        name="LNG imports",
        marker_color="#18a999",
    )
)

fig4.add_trace(
    go.Scatter(
        x=gas_chart["Financial Year"],
        y=gas_chart["LNG Share (%)"],
        name="LNG share of listed supply",
        yaxis="y2",
        mode="lines+markers+text",
        line=dict(color="#e58e26", width=3),
        text=gas_chart["LNG Share (%)"].round(1).astype(str) + "%",
        textposition="top center",
    )
)

fig4.update_layout(
    barmode="group",
    height=370,
    margin=dict(l=10, r=10, t=25, b=10),
    xaxis_title="Financial year",
    yaxis=dict(
        title="Volume (MMSCM)",
        gridcolor="#e8eef3",
    ),
    yaxis2=dict(
        title="LNG share (%)",
        overlaying="y",
        side="right",
        range=[0, 100],
        ticksuffix="%",
    ),
    legend=dict(orientation="h", y=1.12, x=0),
)

st.plotly_chart(fig4, use_container_width=True)

selected_gas = gas_chart[
    gas_chart["Financial Year"].astype(str) == selected_year
]

if not selected_gas.empty:
    gas_row = selected_gas.iloc[0]

    st.markdown(
        f"""
        <div class="insight">
        For {selected_year}, domestic net production was
        <b>{gas_row['Net Production MMSCM'] / 1000:.1f} BCM</b>
        and LNG imports were
        <b>{gas_row['LNG Imports MMSCM'] / 1000:.1f} BCM</b>.
        The orange line shows LNG's share of the sum of these two measures.
        </div>
        """,
        unsafe_allow_html=True,
    )

# ==========================================================
# INDUSTRY TAKEAWAYS
# ==========================================================

st.markdown("## Industry Takeaways")

first_year = annual.iloc[0]
last_year = annual.iloc[-1]


def percentage_change(first_value, last_value):
    if pd.isna(first_value) or pd.isna(last_value) or first_value == 0:
        return None
    return (last_value / first_value - 1) * 100


consumption_change = percentage_change(
    first_year["Petroleum Total MMT"],
    last_year["Petroleum Total MMT"],
)

domestic_change = percentage_change(
    first_year["Domestic Crude MMT"],
    last_year["Domestic Crude MMT"],
)

imports_change = percentage_change(
    first_year["Crude Imports MMT"],
    last_year["Crude Imports MMT"],
)

lng_start_share = gas_chart.iloc[0]["LNG Share (%)"]
lng_end_share = gas_chart.iloc[-1]["LNG Share (%)"]


def change_text(value):
    return "not available" if value is None else f"{value:+.1f}%"


takeaway1, takeaway2, takeaway3 = st.columns(3)

takeaway1.markdown(
    f"""
    <div class="insight">
    <b>Petroleum demand</b><br>
    Changed by {change_text(consumption_change)}
    between {years[0]} and {years[-1]}.
    </div>
    """,
    unsafe_allow_html=True,
)

takeaway2.markdown(
    f"""
    <div class="insight">
    <b>Crude supply mix</b><br>
    Domestic production changed by {change_text(domestic_change)};
    crude imports changed by {change_text(imports_change)}.
    </div>
    """,
    unsafe_allow_html=True,
)

takeaway3.markdown(
    f"""
    <div class="insight">
    <b>Natural gas supply mix</b><br>
    LNG share of listed domestic production plus LNG imports
    changed from {lng_start_share:.1f}% to {lng_end_share:.1f}%.
    </div>
    """,
    unsafe_allow_html=True,
)

# -------------------- Source Tables --------------------

with st.expander("View source tables"):
    st.markdown("**Annual summary**")
    st.dataframe(
        annual,
        use_container_width=True,
        hide_index=True,
    )

    st.markdown(f"**Petroleum products — {selected_year}**")
    st.dataframe(
        products_year,
        use_container_width=True,
        hide_index=True,
    )

    st.markdown("**Natural gas**")
    st.dataframe(
        gas_chart,
        use_container_width=True,
        hide_index=True,
    )

# -------------------- Data Source and Notes --------------------

st.markdown("---")

st.markdown(
    f"""
    <div class="source">
    <b>Data source:</b> Petroleum Planning &amp; Analysis Cell (PPAC),
    Ministry of Petroleum and Natural Gas, Government of India.
    <a href="https://ppac.gov.in/" target="_blank">
    https://ppac.gov.in/
    </a><br>
    <b>Workbook:</b> {source_label}.
    <b>Coverage:</b> {years[0]}–{years[-1]}.<br>
    Figures are displayed as provided in the consolidated workbook.
    Treat provisional values accordingly where indicated in the source.
    Verify import-share and capacity/utilization definitions against
    the original PPAC source notes.
    </div>
    """,
    unsafe_allow_html=True,
)
