import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import warnings
warnings.filterwarnings('ignore')

# ─────────────────────────────────────────────
#  PAGE CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="Nassau Candy – Profitability Dashboard",
    page_icon="🍬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─────────────────────────────────────────────
#  CUSTOM CSS
# ─────────────────────────────────────────────
st.markdown("""
<style>
    [data-testid="stSidebar"] { background: #1a1a2e; }
    [data-testid="stSidebar"] * { color: #eee !important; }
    .metric-card {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        border: 1px solid #0f3460;
        border-radius: 12px;
        padding: 20px;
        text-align: center;
        color: white;
    }
    .metric-value { font-size: 2rem; font-weight: 700; color: #e94560; }
    .metric-label { font-size: 0.85rem; color: #aaa; margin-top: 4px; }
    .section-header {
        font-size: 1.4rem;
        font-weight: 700;
        color: #1a1a2e;
        border-left: 5px solid #e94560;
        padding-left: 12px;
        margin: 20px 0 10px 0;
    }
    .risk-badge-high   { background:#e94560; color:white; padding:2px 10px; border-radius:20px; font-size:0.75rem; }
    .risk-badge-medium { background:#f39c12; color:white; padding:2px 10px; border-radius:20px; font-size:0.75rem; }
    .risk-badge-low    { background:#27ae60; color:white; padding:2px 10px; border-radius:20px; font-size:0.75rem; }
    div[data-testid="stTabs"] button { font-weight: 600; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
#  STATIC DATA: FACTORIES & PRODUCT MAPPING
# ─────────────────────────────────────────────
FACTORY_COORDS = {
    "Lot's O' Nuts":     {"lat": 32.881893,  "lon": -111.768036},
    "Wicked Choccy's":  {"lat": 32.076176,  "lon": -81.088371},
    "Sugar Shack":       {"lat": 48.11914,   "lon": -96.18115},
    "Secret Factory":    {"lat": 41.446333,  "lon": -90.565487},
    "The Other Factory": {"lat": 35.1175,    "lon": -89.971107},
}

PRODUCT_FACTORY = {
    "Wonka Bar - Nutty Crunch Surprise":    "Lot's O' Nuts",
    "Wonka Bar - Fudge Mallows":            "Lot's O' Nuts",
    "Wonka Bar -Scrumdiddlyumptious":       "Lot's O' Nuts",
    "Wonka Bar - Milk Chocolate":           "Wicked Choccy's",
    "Wonka Bar - Triple Dazzle Caramel":    "Wicked Choccy's",
    "Laffy Taffy":                          "Sugar Shack",
    "SweeTARTS":                            "Sugar Shack",
    "Nerds":                                "Sugar Shack",
    "Fun Dip":                              "Sugar Shack",
    "Fizzy Lifting Drinks":                 "Sugar Shack",
    "Everlasting Gobstopper":               "Secret Factory",
    "Lickable Wallpaper":                   "Secret Factory",
    "Wonka Gum":                            "Secret Factory",
    "Hair Toffee":                          "The Other Factory",
    "Kazookles":                            "The Other Factory",
}

COLORS = {
    "primary":   "#e94560",
    "secondary": "#0f3460",
    "accent":    "#f39c12",
    "success":   "#27ae60",
    "bg":        "#1a1a2e",
}

PALETTE = [
    "#e94560","#0f3460","#f39c12","#27ae60","#8e44ad",
    "#2980b9","#e67e22","#1abc9c","#c0392b","#2c3e50",
    "#d35400","#16a085","#7f8c8d","#2ecc71","#3498db"
]

# ─────────────────────────────────────────────
#  DATA LOADING & PREPROCESSING
# ─────────────────────────────────────────────
@st.cache_data
def load_data():
    df = pd.read_csv("data.csv")

    # Parse dates
    for col in ["Order Date", "Ship Date"]:
        df[col] = pd.to_datetime(df[col], dayfirst=True, errors="coerce")

    # Drop invalid rows
    df = df[(df["Sales"] > 0) & (df["Units"] > 0)].copy()

    # Derived metrics
    df["Gross Margin (%)"]   = (df["Gross Profit"] / df["Sales"] * 100).round(2)
    df["Profit per Unit"]    = (df["Gross Profit"] / df["Units"]).round(3)
    df["Cost per Unit"]      = (df["Cost"] / df["Units"]).round(3)
    df["Revenue per Unit"]   = (df["Sales"] / df["Units"]).round(3)

    # Factory mapping
    df["Factory"] = df["Product Name"].map(PRODUCT_FACTORY).fillna("Unknown")

    # Month-Year for time series
    df["Month"] = df["Order Date"].dt.to_period("M").astype(str)

    return df

df_raw = load_data()

# ─────────────────────────────────────────────
#  SIDEBAR FILTERS
# ─────────────────────────────────────────────
with st.sidebar:
    st.image("https://www.nassaucandy.com/wp-content/uploads/2022/01/nassau-candy-logo.png",
             use_container_width=True)
    st.markdown("---")
    st.markdown("### 🎛️ Dashboard Filters")

    # Date range
    min_date = df_raw["Order Date"].min().date()
    max_date = df_raw["Order Date"].max().date()
    date_range = st.date_input("📅 Date Range",
                               value=(min_date, max_date),
                               min_value=min_date,
                               max_value=max_date)

    # Division
    all_divisions = sorted(df_raw["Division"].dropna().unique().tolist())
    selected_divisions = st.multiselect("🏭 Division",
                                        options=all_divisions,
                                        default=all_divisions)

    # Region
    all_regions = sorted(df_raw["Region"].dropna().unique().tolist())
    selected_regions = st.multiselect("🌎 Region",
                                      options=all_regions,
                                      default=all_regions)

    # Margin threshold
    margin_threshold = st.slider("⚠️ Low-Margin Threshold (%)",
                                 min_value=0, max_value=100, value=40,
                                 help="Products below this margin % are flagged as at-risk")

    # Product search
    product_search = st.text_input("🔍 Search Product", "")

    st.markdown("---")
    st.markdown("**Nassau Candy Distributor**  \n*Profitability Analytics v1.0*")

# ─────────────────────────────────────────────
#  APPLY FILTERS
# ─────────────────────────────────────────────
if len(date_range) == 2:
    start_d = pd.Timestamp(date_range[0])
    end_d   = pd.Timestamp(date_range[1])
else:
    start_d = df_raw["Order Date"].min()
    end_d   = df_raw["Order Date"].max()

df = df_raw[
    (df_raw["Order Date"] >= start_d) &
    (df_raw["Order Date"] <= end_d) &
    (df_raw["Division"].isin(selected_divisions)) &
    (df_raw["Region"].isin(selected_regions))
].copy()

if product_search:
    df = df[df["Product Name"].str.contains(product_search, case=False, na=False)]

# ─────────────────────────────────────────────
#  HEADER
# ─────────────────────────────────────────────
st.markdown("""
<div style='background:linear-gradient(135deg,#1a1a2e,#0f3460);
            padding:28px 36px; border-radius:16px; margin-bottom:24px;
            border-left:6px solid #e94560;'>
  <h1 style='color:white;margin:0;font-size:2rem;'>🍬 Nassau Candy Distributor</h1>
  <p style='color:#aaa;margin:6px 0 0;font-size:1.05rem;'>
      Product Line Profitability &amp; Margin Performance Analysis
  </p>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
#  EXECUTIVE KPI CARDS
# ─────────────────────────────────────────────
total_revenue  = df["Sales"].sum()
total_profit   = df["Gross Profit"].sum()
total_cost     = df["Cost"].sum()
overall_margin = (total_profit / total_revenue * 100) if total_revenue else 0
total_orders   = df["Order ID"].nunique()
total_products = df["Product Name"].nunique()
avg_profit_unit= (df["Gross Profit"].sum() / df["Units"].sum()) if df["Units"].sum() else 0
at_risk_products = df.groupby("Product Name").apply(
    lambda x: (x["Gross Profit"].sum() / x["Sales"].sum() * 100) if x["Sales"].sum() else 0
).lt(margin_threshold).sum()

k1, k2, k3, k4, k5, k6 = st.columns(6)
kpi_data = [
    (k1, f"${total_revenue:,.0f}",  "Total Revenue"),
    (k2, f"${total_profit:,.0f}",   "Gross Profit"),
    (k3, f"{overall_margin:.1f}%",  "Overall Margin"),
    (k4, f"{total_orders:,}",       "Total Orders"),
    (k5, f"${avg_profit_unit:.2f}", "Avg Profit / Unit"),
    (k6, f"{int(at_risk_products)}", "At-Risk Products"),
]
for col, val, label in kpi_data:
    with col:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{val}</div>
            <div class="metric-label">{label}</div>
        </div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ─────────────────────────────────────────────
#  TABS
# ─────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📊 Product Profitability",
    "🏭 Division Performance",
    "💰 Cost vs Margin",
    "📈 Pareto Analysis",
    "🕐 Time Trends",
    "🗺️ Factory Map",
])

# ══════════════════════════════════════════════
#  TAB 1 – PRODUCT PROFITABILITY
# ══════════════════════════════════════════════
with tab1:
    st.markdown('<div class="section-header">Product-Level Profitability Leaderboard</div>',
                unsafe_allow_html=True)

    prod = df.groupby("Product Name").agg(
        Division     = ("Division", "first"),
        Factory      = ("Factory", "first"),
        Total_Sales  = ("Sales", "sum"),
        Total_Profit = ("Gross Profit", "sum"),
        Total_Cost   = ("Cost", "sum"),
        Total_Units  = ("Units", "sum"),
        Orders       = ("Order ID", "nunique"),
    ).reset_index()
    prod["Gross Margin (%)"]  = (prod["Total_Profit"] / prod["Total_Sales"] * 100).round(2)
    prod["Profit per Unit"]   = (prod["Total_Profit"] / prod["Total_Units"]).round(3)
    prod["Revenue Share (%)"] = (prod["Total_Sales"]  / prod["Total_Sales"].sum() * 100).round(2)
    prod["Profit Share (%)"]  = (prod["Total_Profit"] / prod["Total_Profit"].sum() * 100).round(2)
    prod["Margin Risk"] = prod["Gross Margin (%)"].apply(
        lambda m: "🔴 High" if m < margin_threshold * 0.6
        else ("🟡 Medium" if m < margin_threshold else "🟢 Low")
    )
    prod_sorted = prod.sort_values("Gross Margin (%)", ascending=False)

    c1, c2 = st.columns(2)
    with c1:
        # Gross margin bar chart
        fig_margin = px.bar(
            prod_sorted,
            x="Gross Margin (%)", y="Product Name",
            orientation="h",
            color="Division",
            color_discrete_sequence=PALETTE,
            title="Gross Margin % by Product",
            text="Gross Margin (%)"
        )
        fig_margin.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
        fig_margin.add_vline(x=margin_threshold, line_dash="dash",
                             line_color="red", annotation_text=f"Threshold {margin_threshold}%")
        fig_margin.update_layout(height=520, showlegend=True,
                                 plot_bgcolor="white",
                                 yaxis={"categoryorder":"total ascending"})
        st.plotly_chart(fig_margin, use_container_width=True)

    with c2:
        # Profit contribution treemap
        fig_tree = px.treemap(
            prod_sorted,
            path=["Division", "Product Name"],
            values="Total_Profit",
            color="Gross Margin (%)",
            color_continuous_scale=["#e94560","#f39c12","#27ae60"],
            title="Profit Contribution Treemap",
            hover_data={"Total_Sales": True, "Profit per Unit": True}
        )
        fig_tree.update_layout(height=520)
        st.plotly_chart(fig_tree, use_container_width=True)

    # Bubble chart: Revenue vs Profit vs Margin
    st.markdown('<div class="section-header">Revenue vs Profit vs Margin (Bubble Chart)</div>',
                unsafe_allow_html=True)
    fig_bubble = px.scatter(
        prod_sorted,
        x="Total_Sales", y="Total_Profit",
        size="Total_Units", color="Gross Margin (%)",
        color_continuous_scale=["#e94560","#f39c12","#27ae60"],
        hover_name="Product Name",
        text="Product Name",
        title="Revenue vs Gross Profit (bubble = units sold)",
        labels={"Total_Sales":"Total Revenue ($)", "Total_Profit":"Gross Profit ($)"}
    )
    fig_bubble.update_traces(textposition="top center", textfont_size=9)
    fig_bubble.update_layout(height=480, plot_bgcolor="white")
    st.plotly_chart(fig_bubble, use_container_width=True)

    # Data table
    st.markdown('<div class="section-header">Product Profitability Table</div>',
                unsafe_allow_html=True)
    display_cols = ["Product Name","Division","Factory","Total_Sales",
                    "Total_Profit","Gross Margin (%)","Profit per Unit",
                    "Revenue Share (%)","Profit Share (%)","Margin Risk"]
    st.dataframe(
        prod_sorted[display_cols].rename(columns={
            "Total_Sales":"Revenue ($)","Total_Profit":"Gross Profit ($)"
        }).style.format({
            "Revenue ($)": "${:,.2f}",
            "Gross Profit ($)": "${:,.2f}",
            "Gross Margin (%)": "{:.2f}%",
            "Profit per Unit": "${:.3f}",
            "Revenue Share (%)": "{:.2f}%",
            "Profit Share (%)": "{:.2f}%",
        }).background_gradient(subset=["Gross Margin (%)"], cmap="RdYlGn"),
        use_container_width=True, height=420
    )

# ══════════════════════════════════════════════
#  TAB 2 – DIVISION PERFORMANCE
# ══════════════════════════════════════════════
with tab2:
    st.markdown('<div class="section-header">Division Performance Dashboard</div>',
                unsafe_allow_html=True)

    div = df.groupby("Division").agg(
        Revenue      = ("Sales", "sum"),
        Profit       = ("Gross Profit", "sum"),
        Cost         = ("Cost", "sum"),
        Units        = ("Units", "sum"),
        Orders       = ("Order ID", "nunique"),
        Products     = ("Product Name", "nunique"),
    ).reset_index()
    div["Margin (%)"]         = (div["Profit"] / div["Revenue"] * 100).round(2)
    div["Revenue Share (%)"]  = (div["Revenue"] / div["Revenue"].sum() * 100).round(2)
    div["Profit Share (%)"]   = (div["Profit"]  / div["Profit"].sum()  * 100).round(2)
    div["Cost Ratio (%)"]     = (div["Cost"]    / div["Revenue"] * 100).round(2)
    div["Profit per Unit"]    = (div["Profit"]  / div["Units"]).round(3)

    c1, c2, c3 = st.columns(3)
    for i, row in div.iterrows():
        col = [c1, c2, c3][i % 3]
        with col:
            st.markdown(f"""
            <div class="metric-card" style="margin-bottom:10px;">
                <div style="font-size:1.1rem;font-weight:700;color:#f39c12;">{row['Division']}</div>
                <div class="metric-value">{row['Margin (%)']:.1f}%</div>
                <div class="metric-label">Gross Margin | Revenue ${row['Revenue']:,.0f}</div>
            </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)

    with c1:
        # Revenue vs Profit grouped bar
        fig_div_bar = go.Figure()
        fig_div_bar.add_trace(go.Bar(name="Revenue",      x=div["Division"], y=div["Revenue"],
                                     marker_color=COLORS["secondary"]))
        fig_div_bar.add_trace(go.Bar(name="Gross Profit", x=div["Division"], y=div["Profit"],
                                     marker_color=COLORS["primary"]))
        fig_div_bar.add_trace(go.Bar(name="Cost",         x=div["Division"], y=div["Cost"],
                                     marker_color=COLORS["accent"]))
        fig_div_bar.update_layout(
            title="Revenue vs Profit vs Cost by Division",
            barmode="group", height=400, plot_bgcolor="white"
        )
        st.plotly_chart(fig_div_bar, use_container_width=True)

    with c2:
        # Margin pie
        fig_pie = make_subplots(rows=1, cols=2, specs=[[{"type":"domain"},{"type":"domain"}]])
        fig_pie.add_trace(go.Pie(labels=div["Division"], values=div["Revenue"],
                                 name="Revenue Share", hole=0.5,
                                 marker_colors=PALETTE[:3]), 1, 1)
        fig_pie.add_trace(go.Pie(labels=div["Division"], values=div["Profit"],
                                 name="Profit Share", hole=0.5,
                                 marker_colors=PALETTE[:3]), 1, 2)
        fig_pie.update_layout(
            title="Revenue Share (left) vs Profit Share (right)",
            annotations=[
                dict(text="Revenue", x=0.20, y=0.5, showarrow=False),
                dict(text="Profit",  x=0.80, y=0.5, showarrow=False),
            ],
            height=400
        )
        st.plotly_chart(fig_pie, use_container_width=True)

    # Margin efficiency radar
    st.markdown('<div class="section-header">Division Efficiency Radar</div>',
                unsafe_allow_html=True)
    metrics_radar = ["Margin (%)", "Revenue Share (%)", "Profit Share (%)", "Cost Ratio (%)"]
    fig_radar = go.Figure()
    for _, row in div.iterrows():
        vals = [row[m] for m in metrics_radar]
        fig_radar.add_trace(go.Scatterpolar(
            r=vals + [vals[0]],
            theta=metrics_radar + [metrics_radar[0]],
            fill="toself", name=row["Division"]
        ))
    fig_radar.update_layout(
        polar=dict(radialaxis=dict(visible=True)),
        title="Division KPI Radar Chart", height=450
    )
    st.plotly_chart(fig_radar, use_container_width=True)

    # Margin by product within division
    st.markdown('<div class="section-header">Product Margin Distribution by Division</div>',
                unsafe_allow_html=True)
    fig_box = px.box(
        df, x="Division", y="Gross Margin (%)", color="Division",
        color_discrete_sequence=PALETTE,
        points="all", hover_data=["Product Name"],
        title="Margin Distribution per Division"
    )
    fig_box.update_layout(height=400, plot_bgcolor="white")
    st.plotly_chart(fig_box, use_container_width=True)

    # Division summary table
    st.markdown('<div class="section-header">Division Summary Table</div>',
                unsafe_allow_html=True)
    st.dataframe(
        div.style.format({
            "Revenue":"${:,.2f}", "Profit":"${:,.2f}", "Cost":"${:,.2f}",
            "Margin (%)":"{:.2f}%", "Revenue Share (%)":"{:.2f}%",
            "Profit Share (%)":"{:.2f}%", "Cost Ratio (%)":"{:.2f}%",
            "Profit per Unit":"${:.3f}"
        }).background_gradient(subset=["Margin (%)"], cmap="RdYlGn"),
        use_container_width=True
    )

# ══════════════════════════════════════════════
#  TAB 3 – COST vs MARGIN DIAGNOSTICS
# ══════════════════════════════════════════════
with tab3:
    st.markdown('<div class="section-header">Cost vs Margin Diagnostics</div>',
                unsafe_allow_html=True)

    prod_diag = df.groupby("Product Name").agg(
        Division      = ("Division", "first"),
        Factory       = ("Factory", "first"),
        Total_Sales   = ("Sales", "sum"),
        Total_Cost    = ("Cost", "sum"),
        Total_Profit  = ("Gross Profit", "sum"),
        Total_Units   = ("Units", "sum"),
    ).reset_index()
    prod_diag["Gross Margin (%)"] = (prod_diag["Total_Profit"] / prod_diag["Total_Sales"] * 100).round(2)
    prod_diag["Cost Ratio (%)"]   = (prod_diag["Total_Cost"]   / prod_diag["Total_Sales"] * 100).round(2)
    prod_diag["Profit per Unit"]  = (prod_diag["Total_Profit"] / prod_diag["Total_Units"]).round(3)

    # Classify
    def classify_product(row):
        high_sales  = row["Total_Sales"]  >= prod_diag["Total_Sales"].median()
        high_margin = row["Gross Margin (%)"] >= margin_threshold
        if high_sales and high_margin:     return "⭐ Star"
        if high_sales and not high_margin: return "⚠️ High-Volume Low-Margin"
        if not high_sales and high_margin: return "💎 Niche High-Margin"
        return "❌ Under-Performer"

    prod_diag["Category"] = prod_diag.apply(classify_product, axis=1)

    c1, c2 = st.columns(2)
    with c1:
        # Cost vs Sales scatter
        fig_scatter = px.scatter(
            prod_diag,
            x="Total_Cost", y="Total_Sales",
            color="Gross Margin (%)",
            size="Total_Units",
            color_continuous_scale=["#e94560","#f39c12","#27ae60"],
            hover_name="Product Name",
            text="Product Name",
            title="Cost vs Revenue Scatter (Margin as Colour)",
            labels={"Total_Cost":"Total Cost ($)", "Total_Sales":"Total Revenue ($)"}
        )
        # Perfect margin line
        max_v = max(prod_diag["Total_Cost"].max(), prod_diag["Total_Sales"].max())
        fig_scatter.add_trace(go.Scatter(
            x=[0, max_v], y=[0, max_v],
            mode="lines", name="Break-even",
            line=dict(dash="dash", color="red")
        ))
        fig_scatter.update_traces(textposition="top center", textfont_size=8,
                                   selector=dict(mode="markers+text"))
        fig_scatter.update_layout(height=450, plot_bgcolor="white")
        st.plotly_chart(fig_scatter, use_container_width=True)

    with c2:
        # Cost ratio vs margin scatter
        fig_ratio = px.scatter(
            prod_diag,
            x="Cost Ratio (%)", y="Gross Margin (%)",
            color="Division",
            size="Total_Sales",
            color_discrete_sequence=PALETTE,
            hover_name="Product Name",
            text="Product Name",
            title="Cost Ratio vs Gross Margin"
        )
        fig_ratio.add_hline(y=margin_threshold, line_dash="dash",
                            line_color="red", annotation_text=f"Margin threshold {margin_threshold}%")
        fig_ratio.update_traces(textposition="top center", textfont_size=8,
                                 selector=dict(mode="markers+text"))
        fig_ratio.update_layout(height=450, plot_bgcolor="white")
        st.plotly_chart(fig_ratio, use_container_width=True)

    # Product quadrant analysis
    st.markdown('<div class="section-header">Product Quadrant Classification</div>',
                unsafe_allow_html=True)
    fig_quad = px.scatter(
        prod_diag,
        x="Total_Sales", y="Gross Margin (%)",
        color="Category",
        color_discrete_sequence=PALETTE,
        size="Total_Cost",
        hover_name="Product Name",
        text="Product Name",
        title="Quadrant Analysis: Revenue vs Margin",
    )
    median_sales  = prod_diag["Total_Sales"].median()
    fig_quad.add_vline(x=median_sales,       line_dash="dot", line_color="gray")
    fig_quad.add_hline(y=margin_threshold,   line_dash="dot", line_color="red")
    fig_quad.update_traces(textposition="top center", textfont_size=9,
                            selector=dict(mode="markers+text"))
    fig_quad.update_layout(height=500, plot_bgcolor="white")
    st.plotly_chart(fig_quad, use_container_width=True)

    # Risk flags table
    st.markdown('<div class="section-header">⚠️ Margin Risk Flags</div>',
                unsafe_allow_html=True)
    risk_df = prod_diag[prod_diag["Gross Margin (%)"] < margin_threshold].sort_values("Gross Margin (%)")
    if risk_df.empty:
        st.success("No products fall below the current margin threshold.")
    else:
        st.warning(f"{len(risk_df)} product(s) flagged below {margin_threshold}% margin threshold")
        st.dataframe(
            risk_df[["Product Name","Division","Factory",
                     "Total_Sales","Total_Cost","Gross Margin (%)","Category"]].style.format({
                "Total_Sales":"${:,.2f}","Total_Cost":"${:,.2f}","Gross Margin (%)":"{:.2f}%"
            }).background_gradient(subset=["Gross Margin (%)"], cmap="RdYlGn"),
            use_container_width=True
        )

    # Recommended actions
    st.markdown('<div class="section-header">📋 Recommended Actions</div>',
                unsafe_allow_html=True)
    actions = {
        "⭐ Star":                  ("Invest & Scale",  "Increase promotions and volume. Protect pricing."),
        "⚠️ High-Volume Low-Margin": ("Reprice / Renegotiate", "Review cost contracts or adjust pricing. Volume exists—fix margin."),
        "💎 Niche High-Margin":     ("Grow Distribution", "High margin but low sales. Expand customer reach."),
        "❌ Under-Performer":        ("Review Discontinuation", "Low sales, low margin. Evaluate portfolio rationalization."),
    }
    cat_counts = prod_diag["Category"].value_counts()
    for cat, (action, desc) in actions.items():
        count = cat_counts.get(cat, 0)
        with st.expander(f"{cat} — {count} product(s) → **{action}**"):
            st.write(desc)
            prods = prod_diag[prod_diag["Category"] == cat]["Product Name"].tolist()
            if prods:
                for p in prods:
                    st.markdown(f"- {p}")

# ══════════════════════════════════════════════
#  TAB 4 – PARETO ANALYSIS
# ══════════════════════════════════════════════
with tab4:
    st.markdown('<div class="section-header">Pareto Analysis – Profit Concentration</div>',
                unsafe_allow_html=True)

    # Product-level Pareto
    pareto = prod_sorted[["Product Name","Division","Total_Sales","Total_Profit"]].copy()
    pareto = pareto.sort_values("Total_Profit", ascending=False).reset_index(drop=True)
    pareto["Cum Profit (%)"]  = pareto["Total_Profit"].cumsum() / pareto["Total_Profit"].sum() * 100
    pareto["Cum Revenue (%)"] = pareto["Total_Sales"].cumsum()  / pareto["Total_Sales"].sum()  * 100
    pareto["Product #"]       = range(1, len(pareto) + 1)

    c1, c2 = st.columns(2)
    with c1:
        # Profit Pareto
        fig_par_profit = make_subplots(specs=[[{"secondary_y": True}]])
        fig_par_profit.add_trace(
            go.Bar(x=pareto["Product Name"], y=pareto["Total_Profit"],
                   name="Gross Profit", marker_color=COLORS["primary"]),
            secondary_y=False
        )
        fig_par_profit.add_trace(
            go.Scatter(x=pareto["Product Name"], y=pareto["Cum Profit (%)"],
                       name="Cumulative %", mode="lines+markers",
                       line=dict(color=COLORS["secondary"], width=2)),
            secondary_y=True
        )
        fig_par_profit.add_hline(y=80, secondary_y=True,
                                  line_dash="dash", line_color="orange",
                                  annotation_text="80% profit")
        fig_par_profit.update_yaxes(title_text="Gross Profit ($)", secondary_y=False)
        fig_par_profit.update_yaxes(title_text="Cumulative %", secondary_y=True, range=[0, 110])
        fig_par_profit.update_layout(title="Pareto – Profit Concentration",
                                      height=430, plot_bgcolor="white",
                                      xaxis_tickangle=-45)
        st.plotly_chart(fig_par_profit, use_container_width=True)

    with c2:
        # Revenue Pareto
        fig_par_rev = make_subplots(specs=[[{"secondary_y": True}]])
        fig_par_rev.add_trace(
            go.Bar(x=pareto["Product Name"], y=pareto["Total_Sales"],
                   name="Revenue", marker_color=COLORS["secondary"]),
            secondary_y=False
        )
        fig_par_rev.add_trace(
            go.Scatter(x=pareto["Product Name"], y=pareto["Cum Revenue (%)"],
                       name="Cumulative %", mode="lines+markers",
                       line=dict(color=COLORS["accent"], width=2)),
            secondary_y=True
        )
        fig_par_rev.add_hline(y=80, secondary_y=True,
                               line_dash="dash", line_color="orange",
                               annotation_text="80% revenue")
        fig_par_rev.update_yaxes(title_text="Revenue ($)", secondary_y=False)
        fig_par_rev.update_yaxes(title_text="Cumulative %", secondary_y=True, range=[0, 110])
        fig_par_rev.update_layout(title="Pareto – Revenue Concentration",
                                   height=430, plot_bgcolor="white",
                                   xaxis_tickangle=-45)
        st.plotly_chart(fig_par_rev, use_container_width=True)

    # 80/20 summary
    prod_80_profit  = (pareto["Cum Profit (%)"]  <= 80).sum() + 1
    prod_80_revenue = (pareto["Cum Revenue (%)"] <= 80).sum() + 1
    pct_80p = prod_80_profit  / len(pareto) * 100
    pct_80r = prod_80_revenue / len(pareto) * 100

    c1, c2 = st.columns(2)
    with c1:
        st.info(f"📌 **{prod_80_profit} products** ({pct_80p:.0f}% of portfolio) generate **80% of profit**")
    with c2:
        st.info(f"📌 **{prod_80_revenue} products** ({pct_80r:.0f}% of portfolio) generate **80% of revenue**")

    # Region-level profit concentration
    st.markdown('<div class="section-header">Regional Profit Concentration</div>',
                unsafe_allow_html=True)
    reg_profit = df.groupby(["Region","State/Province"]).agg(
        Revenue=("Sales","sum"), Profit=("Gross Profit","sum"), Orders=("Order ID","nunique")
    ).reset_index()
    reg_profit["Margin (%)"] = (reg_profit["Profit"] / reg_profit["Revenue"] * 100).round(2)

    fig_reg = px.bar(
        reg_profit.sort_values("Profit", ascending=True),
        x="Profit", y="State/Province", orientation="h",
        color="Region", color_discrete_sequence=PALETTE,
        title="Gross Profit by State/Province",
        text="Profit"
    )
    fig_reg.update_traces(texttemplate="$%{text:,.0f}", textposition="outside")
    fig_reg.update_layout(height=max(400, len(reg_profit) * 22), plot_bgcolor="white")
    st.plotly_chart(fig_reg, use_container_width=True)

    # Division Pareto
    st.markdown('<div class="section-header">Division Profit Contribution</div>',
                unsafe_allow_html=True)
    div_par = div.sort_values("Profit", ascending=False)
    div_par["Cum Profit (%)"] = div_par["Profit"].cumsum() / div_par["Profit"].sum() * 100
    fig_div_par = make_subplots(specs=[[{"secondary_y": True}]])
    fig_div_par.add_trace(
        go.Bar(x=div_par["Division"], y=div_par["Profit"],
               marker_color=PALETTE[:3], name="Profit"), secondary_y=False
    )
    fig_div_par.add_trace(
        go.Scatter(x=div_par["Division"], y=div_par["Cum Profit (%)"],
                   mode="lines+markers", name="Cumulative %",
                   line=dict(color="red")), secondary_y=True
    )
    fig_div_par.update_layout(title="Division Profit Pareto", height=380, plot_bgcolor="white")
    st.plotly_chart(fig_div_par, use_container_width=True)

# ══════════════════════════════════════════════
#  TAB 5 – TIME TRENDS
# ══════════════════════════════════════════════
with tab5:
    st.markdown('<div class="section-header">Profitability Trends Over Time</div>',
                unsafe_allow_html=True)

    time_df = df.groupby("Month").agg(
        Revenue      = ("Sales", "sum"),
        Profit       = ("Gross Profit", "sum"),
        Cost         = ("Cost", "sum"),
        Units        = ("Units", "sum"),
        Orders       = ("Order ID", "nunique"),
    ).reset_index()
    time_df["Margin (%)"] = (time_df["Profit"] / time_df["Revenue"] * 100).round(2)

    c1, c2 = st.columns(2)
    with c1:
        fig_time1 = go.Figure()
        fig_time1.add_trace(go.Scatter(x=time_df["Month"], y=time_df["Revenue"],
                                        mode="lines+markers", name="Revenue",
                                        line=dict(color=COLORS["secondary"], width=2)))
        fig_time1.add_trace(go.Scatter(x=time_df["Month"], y=time_df["Profit"],
                                        mode="lines+markers", name="Gross Profit",
                                        line=dict(color=COLORS["primary"], width=2)))
        fig_time1.add_trace(go.Scatter(x=time_df["Month"], y=time_df["Cost"],
                                        mode="lines+markers", name="Cost",
                                        line=dict(color=COLORS["accent"], width=2)))
        fig_time1.update_layout(title="Monthly Revenue / Profit / Cost",
                                 height=380, plot_bgcolor="white",
                                 xaxis_tickangle=-45)
        st.plotly_chart(fig_time1, use_container_width=True)

    with c2:
        fig_time2 = go.Figure()
        fig_time2.add_trace(go.Scatter(x=time_df["Month"], y=time_df["Margin (%)"],
                                        mode="lines+markers", fill="tozeroy",
                                        name="Gross Margin %",
                                        line=dict(color=COLORS["success"], width=2)))
        fig_time2.add_hline(y=margin_threshold, line_dash="dash",
                             line_color="red", annotation_text=f"Threshold {margin_threshold}%")
        fig_time2.update_layout(title="Monthly Gross Margin %",
                                 height=380, plot_bgcolor="white",
                                 xaxis_tickangle=-45)
        st.plotly_chart(fig_time2, use_container_width=True)

    # Per-product time trend
    st.markdown('<div class="section-header">Product-Level Monthly Margin Trend</div>',
                unsafe_allow_html=True)
    selected_products = st.multiselect(
        "Select products to compare",
        options=sorted(df["Product Name"].unique()),
        default=sorted(df["Product Name"].unique())[:4]
    )
    if selected_products:
        pt = df[df["Product Name"].isin(selected_products)].groupby(
            ["Month","Product Name"]
        ).agg(Revenue=("Sales","sum"), Profit=("Gross Profit","sum")).reset_index()
        pt["Margin (%)"] = (pt["Profit"] / pt["Revenue"] * 100).round(2)
        fig_pt = px.line(pt, x="Month", y="Margin (%)", color="Product Name",
                         color_discrete_sequence=PALETTE,
                         markers=True, title="Product Margin Trend Over Time")
        fig_pt.add_hline(y=margin_threshold, line_dash="dash", line_color="red")
        fig_pt.update_layout(height=430, plot_bgcolor="white", xaxis_tickangle=-45)
        st.plotly_chart(fig_pt, use_container_width=True)

    # Margin volatility
    st.markdown('<div class="section-header">Margin Volatility by Product</div>',
                unsafe_allow_html=True)
    mv = df.groupby(["Product Name","Month"]).apply(
        lambda x: x["Gross Profit"].sum() / x["Sales"].sum() * 100 if x["Sales"].sum() > 0 else 0
    ).reset_index(name="Margin (%)")
    mv_stats = mv.groupby("Product Name")["Margin (%)"].agg(
        Mean="mean", Std="std", Min="min", Max="max"
    ).reset_index().sort_values("Std", ascending=False)
    fig_vol = px.bar(mv_stats, x="Product Name", y="Std",
                     color="Mean", color_continuous_scale=["#27ae60","#f39c12","#e94560"],
                     title="Margin Volatility (Std Dev) by Product – higher = more volatile",
                     text="Std")
    fig_vol.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
    fig_vol.update_layout(height=400, plot_bgcolor="white", xaxis_tickangle=-30)
    st.plotly_chart(fig_vol, use_container_width=True)

# ══════════════════════════════════════════════
#  TAB 6 – FACTORY MAP
# ══════════════════════════════════════════════
with tab6:
    st.markdown('<div class="section-header">Factory Location & Profitability Map</div>',
                unsafe_allow_html=True)

    factory_perf = df.groupby("Factory").agg(
        Revenue = ("Sales","sum"),
        Profit  = ("Gross Profit","sum"),
        Units   = ("Units","sum"),
        Products= ("Product Name","nunique"),
    ).reset_index()
    factory_perf["Margin (%)"] = (factory_perf["Profit"] / factory_perf["Revenue"] * 100).round(2)

    # Merge coords
    factory_perf["lat"] = factory_perf["Factory"].map(lambda f: FACTORY_COORDS.get(f,{}).get("lat"))
    factory_perf["lon"] = factory_perf["Factory"].map(lambda f: FACTORY_COORDS.get(f,{}).get("lon"))
    factory_perf = factory_perf.dropna(subset=["lat","lon"])

    fig_map = px.scatter_mapbox(
        factory_perf,
        lat="lat", lon="lon",
        size="Revenue",
        color="Margin (%)",
        color_continuous_scale=["#e94560","#f39c12","#27ae60"],
        hover_name="Factory",
        hover_data={"Revenue":True,"Profit":True,"Margin (%)":True,"Products":True,"Units":True},
        size_max=50,
        zoom=3,
        mapbox_style="carto-positron",
        title="Factory Performance Map (bubble size = Revenue, colour = Margin %)"
    )
    fig_map.update_layout(height=540)
    st.plotly_chart(fig_map, use_container_width=True)

    # Factory performance table
    st.markdown('<div class="section-header">Factory Performance Summary</div>',
                unsafe_allow_html=True)
    c1, c2 = st.columns([2, 3])
    with c1:
        st.dataframe(
            factory_perf[["Factory","Revenue","Profit","Margin (%)","Products","Units"]].style.format({
                "Revenue":"${:,.2f}", "Profit":"${:,.2f}", "Margin (%)":"{:.2f}%"
            }).background_gradient(subset=["Margin (%)"], cmap="RdYlGn"),
            use_container_width=True
        )
    with c2:
        fig_fac = px.bar(
            factory_perf.sort_values("Margin (%)", ascending=True),
            x="Margin (%)", y="Factory", orientation="h",
            color="Margin (%)", color_continuous_scale=["#e94560","#f39c12","#27ae60"],
            text="Margin (%)", title="Gross Margin % by Factory"
        )
        fig_fac.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
        fig_fac.update_layout(height=380, plot_bgcolor="white")
        st.plotly_chart(fig_fac, use_container_width=True)

    # Products per factory
    st.markdown('<div class="section-header">Products Originating from Each Factory</div>',
                unsafe_allow_html=True)
    for factory in factory_perf["Factory"].tolist():
        prods_in_factory = [p for p, f in PRODUCT_FACTORY.items() if f == factory]
        frow = factory_perf[factory_perf["Factory"] == factory].iloc[0]
        with st.expander(f"🏭 {factory} — Margin: {frow['Margin (%)']:.1f}% | Revenue: ${frow['Revenue']:,.0f}"):
            for p in prods_in_factory:
                p_data = df[df["Product Name"] == p]
                if not p_data.empty:
                    m = p_data["Gross Profit"].sum() / p_data["Sales"].sum() * 100
                    st.markdown(f"- **{p}** — Margin: {m:.1f}%")

# ─────────────────────────────────────────────
#  FOOTER
# ─────────────────────────────────────────────
st.markdown("---")
st.markdown("""
<div style='text-align:center; color:#888; font-size:0.85rem; padding:10px;'>
  Nassau Candy Distributor • Product Line Profitability & Margin Performance Analysis •
  Built with Streamlit & Plotly
</div>
""", unsafe_allow_html=True)
