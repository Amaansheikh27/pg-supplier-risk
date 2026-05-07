import os
import pandas as pd

from src.data_generator import generate_supplier_universe
from src.risk_model import build_full_scorecard, portfolio_summary, WEIGHTS

os.makedirs("data", exist_ok=True)

# ── 1. Generate supplier universe ─────────────────────────────────────────────
print("Building P&G supplier universe...")
df = generate_supplier_universe()
print(f"  {len(df)} suppliers  |  {df['country'].nunique()} countries  |  {df['category'].nunique()} categories")

# ── 2. Compute risk scores, tiers, exposures ──────────────────────────────────
print("\nScoring suppliers across 5 risk dimensions...")
scored = build_full_scorecard(df)

# ── 3. Print portfolio summary ────────────────────────────────────────────────
summary = portfolio_summary(scored)
print("\n=== PORTFOLIO RISK SUMMARY ===")
print(f"  Total suppliers          : {summary['total_suppliers']}")
print(f"  Tier 1 (High Risk)       : {summary['tier1_count']}  ({summary['tier1_count']/summary['total_suppliers']*100:.0f}%)")
print(f"  Tier 2 (Moderate Risk)   : {summary['tier2_count']}  ({summary['tier2_count']/summary['total_suppliers']*100:.0f}%)")
print(f"  Tier 3 (Low Risk)        : {summary['tier3_count']}  ({summary['tier3_count']/summary['total_suppliers']*100:.0f}%)")
print(f"  Total Annual Spend       : ${summary['total_spend_m']:.1f}M")
print(f"  At-Risk Spend (Tier 1)   : ${summary['at_risk_spend_m']:.1f}M")
print(f"  Disruption Exposure      : ${summary['total_exposure_m']:.1f}M")
print(f"  Single-Source Suppliers  : {summary['single_source_count']}")
print(f"  Avg Composite Risk Score : {summary['avg_composite_score']}/100")

print("\n=== TOP 10 HIGHEST RISK SUPPLIERS ===")
cols = ["supplier_name", "country", "category", "composite_risk_score", "tier_label", "is_single_source"]
print(scored[cols].head(10).to_string(index=False))

print("\n=== DIMENSION WEIGHTS USED ===")
for k, v in WEIGHTS.items():
    print(f"  {k:<22}: {v*100:.0f}%")

# ── 4. Save scorecard ─────────────────────────────────────────────────────────
scored.to_csv("data/supplier_scorecard.csv", index=False)
print("\nScorecard saved. Run dashboard with:  python -m streamlit run app.py")
