import os
import subprocess
import sys

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import plotly.io as pio

st.set_page_config(
    page_title="P&G Supplier Risk Intelligence",
    page_icon="🌐",
    layout="wide",
)

st.markdown(
    """
    <style>
    .kpi-red   { background:linear-gradient(135deg,#7B0D1E,#E31837); padding:18px 22px;
                 border-radius:10px; color:white; text-align:center;
                 border:1px solid rgba(227,24,55,0.4); }
    .kpi-blue  { background:linear-gradient(135deg,#003594,#0052CC); padding:18px 22px;
                 border-radius:10px; color:white; text-align:center;
                 border:1px solid rgba(74,158,255,0.3); }
    .kpi-orange{ background:linear-gradient(135deg,#7A3B00,#FF8C00); padding:18px 22px;
                 border-radius:10px; color:white; text-align:center;
                 border:1px solid rgba(255,140,0,0.4); }
    .kpi-green { background:linear-gradient(135deg,#0D3B1F,#28A745); padding:18px 22px;
                 border-radius:10px; color:white; text-align:center;
                 border:1px solid rgba(40,167,69,0.4); }
    .kpi-value { font-size:2rem; font-weight:700; margin:0; }
    .kpi-label { font-size:0.85rem; opacity:0.9; margin:4px 0 0 0; }
    .kpi-sub   { font-size:0.78rem; opacity:0.75; margin:2px 0 0 0; }
    [data-testid="stMetric"] { background:rgba(255,255,255,0.05); border-radius:8px;
                                padding:12px; border:1px solid rgba(255,255,255,0.08); }
    </style>
    """,
    unsafe_allow_html=True,
)

pio.templates["pg_dark"] = go.layout.Template(
    layout=go.Layout(
        font=dict(color="#E8EAED", family="sans-serif"),
        xaxis=dict(tickfont=dict(color="#E8EAED"), linecolor="rgba(255,255,255,0.15)"),
        yaxis=dict(tickfont=dict(color="#E8EAED"), linecolor="rgba(255,255,255,0.15)"),
        legend=dict(font=dict(color="#E8EAED"), bgcolor="rgba(255,255,255,0.05)",
                    bordercolor="rgba(255,255,255,0.1)"),
        hoverlabel=dict(bgcolor="#1E2A3A", font=dict(color="#E8EAED"),
                        bordercolor="rgba(74,158,255,0.5)"),
        colorway=["#4A9EFF","#E31837","#FF8C00","#28A745","#9B59B6","#1ABC9C"],
    )
)
pio.templates.default = "pg_dark"

TIER_COLORS = {1: "#E31837", 2: "#FF8C00", 3: "#28A745"}
TIER_LABELS = {1: "Tier 1 — High Risk", 2: "Tier 2 — Moderate Risk", 3: "Tier 3 — Low Risk"}
DIMS = ["financial_risk", "geographic_risk", "operational_risk", "concentration_risk", "esg_risk"]
DIM_LABELS = ["Financial", "Geographic", "Operational", "Concentration", "ESG"]


def _bootstrap():
    if not os.path.exists("data/supplier_scorecard.csv"):
        with st.spinner("First run — scoring supplier portfolio (~30 seconds)..."):
            subprocess.run([sys.executable, "score.py"], check=True)


@st.cache_data
def load_data() -> pd.DataFrame:
    return pd.read_csv("data/supplier_scorecard.csv")


# ── Bootstrap & load ──────────────────────────────────────────────────────────
_bootstrap()
try:
    df = load_data()
except FileNotFoundError:
    st.error("Run `python score.py` first, then refresh.")
    st.stop()

total       = len(df)
tier1       = int((df["risk_tier"] == 1).sum())
total_spend = df["annual_spend_usd_m"].sum()
exposure    = df["disruption_exposure_usd_m"].sum()
ss_count    = int(df["is_single_source"].sum())

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("## 🌐 P&G Supplier Risk Intelligence Platform")
st.markdown(
    "*Multi-dimensional risk scoring across the P&G direct materials supply base*"
)
st.divider()

# ── KPI Cards ─────────────────────────────────────────────────────────────────
c1, c2, c3, c4 = st.columns(4)
with c1:
    st.markdown(
        f'<div class="kpi-red"><p class="kpi-value">{tier1}</p>'
        f'<p class="kpi-label">Tier 1 High-Risk Suppliers</p>'
        f'<p class="kpi-sub">{tier1/total*100:.0f}% of portfolio — immediate action</p></div>',
        unsafe_allow_html=True,
    )
with c2:
    st.markdown(
        f'<div class="kpi-blue"><p class="kpi-value">${total_spend:.0f}M</p>'
        f'<p class="kpi-label">Total Annual Spend Monitored</p>'
        f'<p class="kpi-sub">{total} suppliers · {df["country"].nunique()} countries</p></div>',
        unsafe_allow_html=True,
    )
with c3:
    st.markdown(
        f'<div class="kpi-orange"><p class="kpi-value">${exposure:.0f}M</p>'
        f'<p class="kpi-label">Disruption Exposure</p>'
        f'<p class="kpi-sub">Probability-weighted at-risk spend</p></div>',
        unsafe_allow_html=True,
    )
with c4:
    st.markdown(
        f'<div class="kpi-green"><p class="kpi-value">{ss_count}</p>'
        f'<p class="kpi-label">Single-Source Dependencies</p>'
        f'<p class="kpi-sub">Require immediate dual-sourcing review</p></div>',
        unsafe_allow_html=True,
    )

st.markdown("<br>", unsafe_allow_html=True)

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs(
    ["🗺️ Global Risk Map", "🔍 Supplier Deep Dive", "📊 Portfolio Analytics", "⚡ Action Plan"]
)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — GLOBAL RISK MAP
# ══════════════════════════════════════════════════════════════════════════════
with tab1:
    st.subheader("Supplier Risk Map — Bubble size = Annual Spend · Color = Risk Score")

    col_f1, col_f2 = st.columns([2, 1])
    with col_f1:
        cat_filter = st.multiselect(
            "Filter by category",
            sorted(df["category"].unique()),
            default=sorted(df["category"].unique()),
        )
    with col_f2:
        tier_filter = st.multiselect(
            "Filter by tier", [1, 2, 3], default=[1, 2, 3],
            format_func=lambda x: TIER_LABELS[x],
        )

    view = df[df["category"].isin(cat_filter) & df["risk_tier"].isin(tier_filter)]

    fig_map = go.Figure()
    for tier in [3, 2, 1]:
        sub = view[view["risk_tier"] == tier]
        if sub.empty:
            continue
        fig_map.add_trace(
            go.Scattergeo(
                lat=sub["lat"],
                lon=sub["lon"],
                mode="markers",
                name=TIER_LABELS[tier],
                marker=dict(
                    size=sub["annual_spend_usd_m"] ** 0.52 * 2.2,
                    color=TIER_COLORS[tier],
                    opacity=0.85,
                    line=dict(width=1, color="white"),
                ),
                text=sub.apply(
                    lambda r: (
                        f"<b>{r['supplier_name']}</b><br>"
                        f"Country: {r['country']}<br>"
                        f"Category: {r['category']}<br>"
                        f"Risk Score: {r['composite_risk_score']}/100<br>"
                        f"Annual Spend: ${r['annual_spend_usd_m']}M<br>"
                        f"Single Source: {'Yes ⚠️' if r['is_single_source'] else 'No'}"
                    ),
                    axis=1,
                ),
                hoverinfo="text",
            )
        )

    fig_map.update_layout(
        geo=dict(
            showframe=False,
            showcoastlines=True,
            coastlinecolor="rgba(74,158,255,0.4)",
            showland=True,
            landcolor="#0D1B2A",
            showocean=True,
            oceancolor="#060D18",
            showcountries=True,
            countrycolor="rgba(255,255,255,0.15)",
            projection_type="natural earth",
            bgcolor="rgba(0,0,0,0)",
            lakecolor="#060D18",
        ),
        paper_bgcolor="rgba(0,0,0,0)",
        height=520,
        margin=dict(l=0, r=0, t=10, b=0),
        legend=dict(orientation="h", yanchor="bottom", y=-0.05, x=0.5, xanchor="center"),
    )
    st.plotly_chart(fig_map, use_container_width=True)

    # Country risk heatmap
    country_avg = (
        df.groupby("country")
        .agg(avg_score=("composite_risk_score", "mean"), count=("supplier_name", "count"))
        .reset_index()
        .sort_values("avg_score", ascending=False)
    )
    fig_country = px.bar(
        country_avg,
        x="country", y="avg_score", color="avg_score",
        color_continuous_scale=[[0, "#28A745"], [0.45, "#FF8C00"], [1, "#E31837"]],
        text="count",
        title="Average Risk Score by Country (number = supplier count)",
        labels={"avg_score": "Avg Risk Score", "country": ""},
    )
    fig_country.update_traces(texttemplate="%{text} suppliers", textposition="outside")
    fig_country.update_layout(
        height=340, coloraxis_showscale=False,
        plot_bgcolor="rgba(255,255,255,0.03)", paper_bgcolor="rgba(0,0,0,0)",
        xaxis_tickangle=-35, margin=dict(t=50, b=80),
    )
    st.plotly_chart(fig_country, use_container_width=True)


# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — SUPPLIER DEEP DIVE
# ══════════════════════════════════════════════════════════════════════════════
with tab2:
    col_sel, col_sort = st.columns([3, 1])
    with col_sort:
        sort_by = st.selectbox("Sort list by", ["Risk Score ↓", "Spend ↓", "Alphabetical"])
    sort_map = {
        "Risk Score ↓": ("composite_risk_score", False),
        "Spend ↓":       ("annual_spend_usd_m", False),
        "Alphabetical":  ("supplier_name", True),
    }
    s_col, s_asc = sort_map[sort_by]
    sorted_names = df.sort_values(s_col, ascending=s_asc)["supplier_name"].tolist()
    with col_sel:
        selected = st.selectbox("Select Supplier", sorted_names)

    row = df[df["supplier_name"] == selected].iloc[0]
    avg = df[DIMS].mean()

    # Header info
    tier_col = TIER_COLORS[row["risk_tier"]]
    h1, h2, h3, h4, h5 = st.columns(5)
    h1.metric("Composite Score", f"{row['composite_risk_score']}/100")
    h2.metric("Risk Tier", row["tier_label"].split("—")[1].strip())
    h3.metric("Annual Spend", f"${row['annual_spend_usd_m']}M")
    h4.metric("Disruption Exposure", f"${row['disruption_exposure_usd_m']}M")
    h5.metric("Single Source", "Yes ⚠️" if row["is_single_source"] else "No ✓")

    st.divider()

    left, right = st.columns(2)

    with left:
        # Radar chart
        vals_sup = [row[d] for d in DIMS]
        vals_avg = [avg[d] for d in DIMS]
        fig_radar = go.Figure()
        fig_radar.add_trace(go.Scatterpolar(
            r=vals_avg + [vals_avg[0]],
            theta=DIM_LABELS + [DIM_LABELS[0]],
            fill="toself", fillcolor="rgba(0,82,204,0.15)",
            line=dict(color="#0052CC", width=2),
            name="Portfolio Average",
        ))
        fig_radar.add_trace(go.Scatterpolar(
            r=vals_sup + [vals_sup[0]],
            theta=DIM_LABELS + [DIM_LABELS[0]],
            fill="toself", fillcolor=f"rgba(227,24,55,0.20)",
            line=dict(color=tier_col, width=2.5),
            name=selected,
        ))
        fig_radar.update_layout(
            polar=dict(
                radialaxis=dict(visible=True, range=[0, 100],
                                gridcolor="rgba(255,255,255,0.1)",
                                tickfont=dict(color="#E8EAED")),
                angularaxis=dict(tickfont=dict(color="#E8EAED"),
                                 linecolor="rgba(255,255,255,0.15)"),
                bgcolor="rgba(255,255,255,0.03)",
            ),
            showlegend=True,
            title=f"Risk Profile vs Portfolio Average",
            height=420,
            paper_bgcolor="rgba(0,0,0,0)",
        )
        st.plotly_chart(fig_radar, use_container_width=True)

    with right:
        # Dimension bar breakdown
        dim_df = pd.DataFrame({
            "Dimension": DIM_LABELS,
            f"{selected}": vals_sup,
            "Portfolio Avg": [round(a, 1) for a in vals_avg],
        })
        fig_bars = go.Figure()
        fig_bars.add_trace(go.Bar(
            name="Portfolio Avg", x=dim_df["Dimension"], y=dim_df["Portfolio Avg"],
            marker_color="#AAAAAA", opacity=0.7,
        ))
        fig_bars.add_trace(go.Bar(
            name=selected, x=dim_df["Dimension"], y=dim_df[selected],
            marker_color=tier_col,
        ))
        fig_bars.update_layout(
            barmode="group", title="Dimension Scores vs Portfolio Average",
            yaxis=dict(range=[0, 100], title="Risk Score"),
            height=420, plot_bgcolor="rgba(255,255,255,0.03)", paper_bgcolor="rgba(0,0,0,0)",
        )
        st.plotly_chart(fig_bars, use_container_width=True)

    # Operational details
    st.subheader("Operational Details")
    d1, d2, d3, d4, d5, d6 = st.columns(6)
    d1.metric("Credit Score", row["credit_score"])
    d2.metric("Payment Delay", f"{row['payment_delay_days']} days")
    d3.metric("Revenue Volatility", f"{row['revenue_volatility_pct']}%")
    d4.metric("Lead Time Variance", f"{row['lead_time_variance_pct']}%")
    d5.metric("Defect Rate", f"{row['defect_rate_ppm']} ppm")
    d6.metric("On-Time Delivery", f"{row['on_time_delivery_pct']}%")

    # Recommendations
    st.subheader("Recommended Actions")
    for i, rec in enumerate(row["recommendations"].split(" | "), 1):
        icon = "🔴" if row["risk_tier"] == 1 else ("🟠" if row["risk_tier"] == 2 else "🟢")
        st.markdown(f"{icon} **{i}.** {rec}")


# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 — PORTFOLIO ANALYTICS
# ══════════════════════════════════════════════════════════════════════════════
with tab3:
    # ── Row 1: Tier donut + Spend at risk bar ─────────────────────────────────
    row1_l, row1_r = st.columns(2)

    tier_counts = (
        df.groupby("risk_tier")
        .agg(count=("supplier_name", "count"), spend=("annual_spend_usd_m", "sum"))
        .reset_index()
        .sort_values("risk_tier")
    )
    tier_counts["short_label"] = tier_counts["risk_tier"].map(
        {1: "🔴 Tier 1 High", 2: "🟠 Tier 2 Moderate", 3: "🟢 Tier 3 Low"}
    )

    with row1_l:
        fig_donut = go.Figure(go.Pie(
            labels=tier_counts["short_label"],
            values=tier_counts["count"],
            hole=0.62,
            marker=dict(
                colors=[TIER_COLORS[t] for t in tier_counts["risk_tier"]],
                line=dict(color="white", width=3),
            ),
            textinfo="label+value",
            textfont_size=13,
            pull=[0.05 if t == 1 else 0 for t in tier_counts["risk_tier"]],
            direction="clockwise",
        ))
        fig_donut.add_annotation(
            text=f"<b>{len(df)}</b><br>Suppliers",
            x=0.5, y=0.5, font_size=16, showarrow=False,
        )
        fig_donut.update_layout(
            title=dict(text="Supplier Count by Risk Tier", font_size=15),
            height=380, paper_bgcolor="rgba(0,0,0,0)",
            showlegend=True,
            legend=dict(orientation="h", y=-0.1, x=0.5, xanchor="center"),
            margin=dict(t=50, b=60, l=20, r=20),
        )
        st.plotly_chart(fig_donut, use_container_width=True)

    with row1_r:
        fig_spend = go.Figure()
        spend_by_tier = tier_counts.sort_values("risk_tier")
        fig_spend.add_trace(go.Bar(
            x=spend_by_tier["short_label"],
            y=spend_by_tier["spend"],
            marker_color=[TIER_COLORS[t] for t in spend_by_tier["risk_tier"]],
            marker_line=dict(color="white", width=2),
            text=["${:.0f}M".format(s) for s in spend_by_tier["spend"]],
            textposition="outside",
            textfont_size=13,
            width=0.5,
        ))
        fig_spend.update_layout(
            title=dict(text="Annual Spend by Risk Tier ($M)", font_size=15),
            yaxis=dict(title="Spend ($M)", showgrid=True, gridcolor="rgba(255,255,255,0.08)"),
            xaxis=dict(tickfont_size=12),
            height=380, plot_bgcolor="rgba(255,255,255,0.03)", paper_bgcolor="rgba(0,0,0,0)",
            showlegend=False,
            margin=dict(t=50, b=60),
        )
        st.plotly_chart(fig_spend, use_container_width=True)

    # ── Row 2: Category risk heatmap ──────────────────────────────────────────
    cat_risk = (
        df.groupby("category")
        .agg(
            avg_score=("composite_risk_score", "mean"),
            total_spend=("annual_spend_usd_m", "sum"),
            tier1=("risk_tier", lambda x: (x == 1).sum()),
            tier2=("risk_tier", lambda x: (x == 2).sum()),
            tier3=("risk_tier", lambda x: (x == 3).sum()),
        )
        .reset_index()
        .sort_values("avg_score", ascending=False)
    )

    fig_cat = go.Figure()
    fig_cat.add_trace(go.Bar(
        name="🔴 High Risk",
        x=cat_risk["category"],
        y=cat_risk["tier1"],
        marker_color="#E31837",
        marker_line=dict(color="white", width=1),
    ))
    fig_cat.add_trace(go.Bar(
        name="🟠 Moderate Risk",
        x=cat_risk["category"],
        y=cat_risk["tier2"],
        marker_color="#FF8C00",
        marker_line=dict(color="white", width=1),
    ))
    fig_cat.add_trace(go.Bar(
        name="🟢 Low Risk",
        x=cat_risk["category"],
        y=cat_risk["tier3"],
        marker_color="#28A745",
        marker_line=dict(color="white", width=1),
    ))
    fig_cat.update_layout(
        barmode="stack",
        title=dict(text="Risk Tier Breakdown by Category (supplier count)", font_size=15),
        yaxis=dict(title="Number of Suppliers", showgrid=True, gridcolor="rgba(255,255,255,0.08)"),
        xaxis=dict(tickangle=-30, tickfont_size=11),
        height=380, plot_bgcolor="rgba(255,255,255,0.03)", paper_bgcolor="rgba(0,0,0,0)",
        legend=dict(orientation="h", y=1.12, x=0.5, xanchor="center"),
        margin=dict(t=70, b=100),
    )
    st.plotly_chart(fig_cat, use_container_width=True)

    # ── Row 3: Risk vs Spend scatter (the "danger quadrant" chart) ────────────
    st.markdown("#### Risk vs Spend — Danger Quadrant Analysis")
    st.caption("Top-right quadrant = highest priority (high spend + high risk). Bubble size = disruption exposure.")

    median_spend = df["annual_spend_usd_m"].median()
    median_score = df["composite_risk_score"].median()

    fig_scatter = go.Figure()
    for tier in [3, 2, 1]:
        sub = df[df["risk_tier"] == tier]
        fig_scatter.add_trace(go.Scatter(
            x=sub["composite_risk_score"],
            y=sub["annual_spend_usd_m"],
            mode="markers+text",
            name=TIER_LABELS[tier],
            text=sub["supplier_name"].str.split().str[0],
            textposition="top center",
            textfont=dict(size=9, color="#333"),
            marker=dict(
                size=sub["disruption_exposure_usd_m"] ** 0.6 * 2.5,
                color=TIER_COLORS[tier],
                opacity=0.85,
                line=dict(width=1.5, color="white"),
            ),
            hovertext=sub.apply(
                lambda r: (
                    f"<b>{r['supplier_name']}</b><br>"
                    f"Score: {r['composite_risk_score']}/100<br>"
                    f"Spend: ${r['annual_spend_usd_m']}M<br>"
                    f"Exposure: ${r['disruption_exposure_usd_m']}M<br>"
                    f"Category: {r['category']}"
                ), axis=1,
            ),
            hoverinfo="text",
        ))

    fig_scatter.add_vline(x=55, line_dash="dash", line_color="#E31837", line_width=1.5,
                          annotation_text="High Risk threshold", annotation_font_color="#E31837")
    fig_scatter.add_hline(y=median_spend, line_dash="dash", line_color="#666", line_width=1,
                          annotation_text=f"Median spend ${median_spend:.0f}M",
                          annotation_font_color="#666")

    fig_scatter.add_shape(type="rect", x0=55, x1=100, y0=median_spend,
                          y1=df["annual_spend_usd_m"].max() * 1.1,
                          fillcolor="rgba(227,24,55,0.06)", line_width=0)
    fig_scatter.add_annotation(x=77, y=df["annual_spend_usd_m"].max() * 1.05,
                                text="⚠️ DANGER ZONE", font=dict(color="#E31837", size=12),
                                showarrow=False)

    fig_scatter.update_layout(
        xaxis=dict(title="Composite Risk Score", range=[0, 105], showgrid=True, gridcolor="rgba(255,255,255,0.08)"),
        yaxis=dict(title="Annual Spend ($M)", showgrid=True, gridcolor="rgba(255,255,255,0.08)"),
        height=500, plot_bgcolor="rgba(255,255,255,0.03)", paper_bgcolor="rgba(0,0,0,0)",
        legend=dict(orientation="h", y=1.05, x=0.5, xanchor="center"),
        hovermode="closest",
        margin=dict(t=60, b=50),
    )
    st.plotly_chart(fig_scatter, use_container_width=True)


# ══════════════════════════════════════════════════════════════════════════════
# TAB 4 — ACTION PLAN
# ══════════════════════════════════════════════════════════════════════════════
with tab4:
    st.subheader("Prioritized Supplier Action Plan")
    st.markdown(
        "Sorted by disruption exposure — highest financial risk at the top."
    )

    tier1_df = df[df["risk_tier"] == 1].sort_values(
        "disruption_exposure_usd_m", ascending=False
    )
    tier2_df = df[df["risk_tier"] == 2].sort_values(
        "disruption_exposure_usd_m", ascending=False
    )

    for tier, tdf, label in [
        (1, tier1_df, "🔴 TIER 1 — IMMEDIATE ACTION"),
        (2, tier2_df, "🟠 TIER 2 — MONITOR CLOSELY"),
    ]:
        st.markdown(f"#### {label}")
        for _, r in tdf.iterrows():
            with st.expander(
                f"**{r['supplier_name']}** ({r['country']}) — "
                f"Score: {r['composite_risk_score']}/100 · "
                f"Spend: ${r['annual_spend_usd_m']}M · "
                f"Exposure: ${r['disruption_exposure_usd_m']}M"
                f"{'  ⚠️ SINGLE SOURCE' if r['is_single_source'] else ''}"
            ):
                c1, c2 = st.columns(2)
                with c1:
                    st.markdown(f"**Category:** {r['category']}")
                    st.markdown(f"**Disruption Probability:** {r['disruption_probability']*100:.1f}%")
                    st.markdown(f"**Credit Score:** {r['credit_score']}")
                    st.markdown(f"**OTD:** {r['on_time_delivery_pct']}%")
                with c2:
                    st.markdown("**Recommended Actions:**")
                    for rec in r["recommendations"].split(" | "):
                        st.markdown(f"- {rec}")
        st.markdown("---")

    # Downloadable full scorecard
    st.subheader("Full Scorecard Export")
    export_cols = [
        "supplier_name", "country", "category", "annual_spend_usd_m",
        "is_single_source", "composite_risk_score", "tier_label",
        "financial_risk", "geographic_risk", "operational_risk",
        "concentration_risk", "esg_risk",
        "disruption_probability", "disruption_exposure_usd_m",
        "recommendations",
    ]
    st.dataframe(df[export_cols], use_container_width=True, hide_index=True)

    csv = df[export_cols].to_csv(index=False).encode("utf-8")
    st.download_button(
        "Download Full Scorecard as CSV",
        data=csv,
        file_name="pg_supplier_risk_scorecard.csv",
        mime="text/csv",
    )

    # Resume metric callout
    t1_pct = tier1 / total * 100
    ss_t1 = int(df[(df["risk_tier"] == 1) & (df["is_single_source"] == 1)].shape[0])
    at_risk = df.loc[df["risk_tier"] == 1, "annual_spend_usd_m"].sum()
    st.info(
        f"**Resume metric to use:** "
        f"\"Built a supplier risk intelligence platform scoring {total} global suppliers "
        f"across 5 dimensions (Financial, Geographic, Operational, Concentration, ESG); "
        f"identified {tier1} ({t1_pct:.0f}%) as Tier 1 high-risk (composite score >55/100) "
        f"including {ss_t1} single-source dependencies, flagging ${at_risk:.0f}M in at-risk "
        f"annual spend requiring immediate dual-sourcing strategy.\""
    )
