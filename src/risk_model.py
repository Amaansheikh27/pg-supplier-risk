import numpy as np
import pandas as pd

# Dimension weights must sum to 1.0
WEIGHTS = {
    "financial_risk":     0.25,
    "geographic_risk":    0.20,
    "operational_risk":   0.30,
    "concentration_risk": 0.15,
    "esg_risk":           0.10,
}

TIER_LABELS = {1: "Tier 1 — High Risk", 2: "Tier 2 — Moderate Risk", 3: "Tier 3 — Low Risk"}
TIER_COLORS = {1: "#E31837", 2: "#FF8C00", 3: "#28A745"}
TIER_ACTIONS = {
    1: "Immediate Action Required",
    2: "Monitor Closely",
    3: "Maintain & Optimize",
}


def compute_composite_score(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["composite_risk_score"] = (
        df["financial_risk"]     * WEIGHTS["financial_risk"]
        + df["geographic_risk"]  * WEIGHTS["geographic_risk"]
        + df["operational_risk"] * WEIGHTS["operational_risk"]
        + df["concentration_risk"] * WEIGHTS["concentration_risk"]
        + df["esg_risk"]         * WEIGHTS["esg_risk"]
    ).round(1)
    return df


def assign_tiers(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["risk_tier"] = pd.cut(
        df["composite_risk_score"],
        bins=[0, 35, 55, 100],
        labels=[3, 2, 1],
    ).astype(int)
    df["tier_label"]  = df["risk_tier"].map(TIER_LABELS)
    df["tier_color"]  = df["risk_tier"].map(TIER_COLORS)
    df["tier_action"] = df["risk_tier"].map(TIER_ACTIONS)
    return df


def compute_disruption_exposure(df: pd.DataFrame) -> pd.DataFrame:
    """Exposure = spend × disruption_probability × impact_multiplier."""
    df = df.copy()
    # Sigmoid: score 50 → ~50% probability; score 80 → ~90%
    df["disruption_probability"] = (
        1 / (1 + np.exp(-0.09 * (df["composite_risk_score"] - 50)))
    ).round(3)
    df["impact_multiplier"] = np.where(df["is_single_source"] == 1, 2.2, 1.3)
    df["disruption_exposure_usd_m"] = (
        df["annual_spend_usd_m"]
        * df["disruption_probability"]
        * df["impact_multiplier"]
    ).round(2)
    return df


def generate_recommendations(row: pd.Series) -> list[str]:
    recs = []
    score = row["composite_risk_score"]
    tier  = row["risk_tier"]

    if row["is_single_source"] and tier <= 2:
        recs.append("Qualify at least one alternate supplier — eliminate single-source dependency")
    if row["geographic_risk"] > 62:
        recs.append("Consider dual-sourcing from a geopolitically stable region")
    if row["financial_risk"] > 60:
        recs.append("Request latest audited financials + initiate credit watch")
    if row["operational_risk"] > 58:
        recs.append("Deploy supplier development team; set OTD improvement KPIs")
    if row["defect_rate_ppm"] > 800:
        recs.append(f"Defect rate {row['defect_rate_ppm']} ppm exceeds threshold — trigger quality audit")
    if row["on_time_delivery_pct"] < 88:
        recs.append(f"OTD {row['on_time_delivery_pct']}% below 90% SLA — review logistics SLA contract")
    if row["esg_risk"] > 55:
        recs.append("Initiate ESG/sustainability audit and request corrective action plan")
    if row["category"] == "Palm Oil" and row["esg_risk"] > 40:
        recs.append("Verify RSPO (Roundtable on Sustainable Palm Oil) certification status")
    if row["payment_delay_days"] > 25:
        recs.append(f"Payment delays averaging {row['payment_delay_days']} days — financial stress signal")
    if row["concentration_risk"] > 65 and not row["is_single_source"]:
        recs.append("High spend concentration — negotiate multi-supplier framework agreement")
    if tier == 3 and score < 30:
        recs.append("Strategic partner — explore preferred supplier program & cost-down collaboration")

    if not recs:
        recs.append("No immediate actions — maintain regular review cadence")
    return recs


def build_full_scorecard(df: pd.DataFrame) -> pd.DataFrame:
    df = compute_composite_score(df)
    df = assign_tiers(df)
    df = compute_disruption_exposure(df)
    df["recommendations"] = df.apply(
        lambda r: " | ".join(generate_recommendations(r)), axis=1
    )
    return df.sort_values("composite_risk_score", ascending=False).reset_index(drop=True)


def portfolio_summary(df: pd.DataFrame) -> dict:
    return {
        "total_suppliers":      len(df),
        "tier1_count":          int((df["risk_tier"] == 1).sum()),
        "tier2_count":          int((df["risk_tier"] == 2).sum()),
        "tier3_count":          int((df["risk_tier"] == 3).sum()),
        "total_spend_m":        round(df["annual_spend_usd_m"].sum(), 1),
        "at_risk_spend_m":      round(df.loc[df["risk_tier"] == 1, "annual_spend_usd_m"].sum(), 1),
        "total_exposure_m":     round(df["disruption_exposure_usd_m"].sum(), 1),
        "avg_composite_score":  round(df["composite_risk_score"].mean(), 1),
        "single_source_count":  int(df["is_single_source"].sum()),
    }
