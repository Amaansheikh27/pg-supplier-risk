import numpy as np
import pandas as pd

# World Bank LPI (Logistics Performance Index): scale 1-5, higher = better
# Political stability: 0-100, higher = more stable
# Disaster risk: 0-100, higher = more prone
COUNTRY_DATA = {
    "USA":          {"lat": 37.09,  "lon": -95.71,  "political_stability": 85, "disaster_risk": 20, "lpi": 4.6},
    "Germany":      {"lat": 51.17,  "lon": 10.45,   "political_stability": 92, "disaster_risk": 12, "lpi": 4.2},
    "China":        {"lat": 35.86,  "lon": 104.19,  "political_stability": 55, "disaster_risk": 45, "lpi": 3.6},
    "India":        {"lat": 20.59,  "lon": 78.96,   "political_stability": 52, "disaster_risk": 50, "lpi": 3.2},
    "Japan":        {"lat": 36.20,  "lon": 138.25,  "political_stability": 88, "disaster_risk": 62, "lpi": 4.0},
    "Brazil":       {"lat": -14.24, "lon": -51.93,  "political_stability": 45, "disaster_risk": 38, "lpi": 2.9},
    "UK":           {"lat": 55.38,  "lon": -3.44,   "political_stability": 89, "disaster_risk": 10, "lpi": 4.0},
    "France":       {"lat": 46.23,  "lon": 2.21,    "political_stability": 83, "disaster_risk": 15, "lpi": 3.8},
    "Netherlands":  {"lat": 52.13,  "lon": 5.29,    "political_stability": 91, "disaster_risk": 12, "lpi": 4.2},
    "South Korea":  {"lat": 35.91,  "lon": 127.77,  "political_stability": 72, "disaster_risk": 35, "lpi": 3.8},
    "Indonesia":    {"lat": -0.79,  "lon": 113.92,  "political_stability": 40, "disaster_risk": 72, "lpi": 2.8},
    "Thailand":     {"lat": 15.87,  "lon": 100.99,  "political_stability": 45, "disaster_risk": 50, "lpi": 3.2},
    "Malaysia":     {"lat": 4.21,   "lon": 101.98,  "political_stability": 60, "disaster_risk": 35, "lpi": 3.4},
    "Vietnam":      {"lat": 14.06,  "lon": 108.28,  "political_stability": 48, "disaster_risk": 55, "lpi": 3.0},
    "Turkey":       {"lat": 38.96,  "lon": 35.24,   "political_stability": 38, "disaster_risk": 58, "lpi": 3.1},
    "South Africa": {"lat": -30.56, "lon": 22.94,   "political_stability": 48, "disaster_risk": 20, "lpi": 2.9},
    "Australia":    {"lat": -25.27, "lon": 133.78,  "political_stability": 88, "disaster_risk": 30, "lpi": 3.8},
    "Switzerland":  {"lat": 46.82,  "lon": 8.23,    "political_stability": 95, "disaster_risk": 8,  "lpi": 4.1},
    "Italy":        {"lat": 41.87,  "lon": 12.57,   "political_stability": 72, "disaster_risk": 32, "lpi": 3.4},
    "Singapore":    {"lat": 1.35,   "lon": 103.82,  "political_stability": 88, "disaster_risk": 10, "lpi": 4.2},
    "Saudi Arabia": {"lat": 23.89,  "lon": 45.08,   "political_stability": 48, "disaster_risk": 15, "lpi": 3.3},
    "Mexico":       {"lat": 23.63,  "lon": -102.55, "political_stability": 42, "disaster_risk": 42, "lpi": 3.0},
    "Poland":       {"lat": 51.92,  "lon": 19.15,   "political_stability": 74, "disaster_risk": 15, "lpi": 3.4},
    "Canada":       {"lat": 56.13,  "lon": -106.35, "political_stability": 91, "disaster_risk": 15, "lpi": 3.9},
    "Spain":        {"lat": 40.46,  "lon": -3.75,   "political_stability": 79, "disaster_risk": 18, "lpi": 3.5},
}

# (name, country, category, annual_spend_usd_m, is_single_source)
SUPPLIER_DATA = [
    # ── Surfactants & Chemicals ─────────────────────────────────────────────
    ("BASF SE",               "Germany",      "Surfactants",             45.2, False),
    ("Stepan Company",        "USA",          "Surfactants",             28.6, False),
    ("Huntsman Corporation",  "USA",          "Surfactants",             19.3, True),
    ("Galaxy Surfactants",    "India",        "Surfactants",             12.8, False),

    # ── Fragrances ──────────────────────────────────────────────────────────
    ("Givaudan SA",           "Switzerland",  "Fragrances",              34.5, True),
    ("IFF International",     "USA",          "Fragrances",              28.2, False),
    ("Symrise AG",            "Germany",      "Fragrances",              18.4, False),
    ("SH Kelkar & Co",        "India",        "Fragrances",               8.2, False),

    # ── Packaging ───────────────────────────────────────────────────────────
    ("Amcor PLC",             "Australia",    "Packaging",               67.3, False),
    ("Berry Global",          "USA",          "Packaging",               54.8, False),
    ("Sealed Air Corp",       "USA",          "Packaging",               41.2, False),
    ("Mondi Group",           "UK",           "Packaging",               23.4, False),
    ("Uflex Limited",         "India",        "Packaging",               12.3, False),
    ("Constantia Flexibles",  "Germany",      "Packaging",               19.8, True),

    # ── Palm Oil & Derivatives ──────────────────────────────────────────────
    ("IOI Corporation",       "Malaysia",     "Palm Oil",                38.4, False),
    ("Wilmar International",  "Singapore",    "Palm Oil",                44.2, False),
    ("Sime Darby Plantation", "Malaysia",     "Palm Oil",                29.7, False),
    ("PT Musim Mas",          "Indonesia",    "Palm Oil",                22.1, True),
    ("Cargill Palm",          "Indonesia",    "Palm Oil",                18.6, False),

    # ── Superabsorbent Polymers (Pampers) ───────────────────────────────────
    ("Nippon Shokubai",       "Japan",        "Superabsorbent Polymers", 31.2, False),
    ("Evonik Industries",     "Germany",      "Superabsorbent Polymers", 27.8, False),
    ("Sumitomo Seika",        "Japan",        "Superabsorbent Polymers", 14.9, True),

    # ── Contract Manufacturing ──────────────────────────────────────────────
    ("Jabil Inc",             "USA",          "Contract Manufacturing",  52.3, False),
    ("Flex Ltd",              "Singapore",    "Contract Manufacturing",  43.7, False),
    ("Fareva Group",          "France",       "Contract Manufacturing",  24.1, False),
    ("Kolmar Korea",          "South Korea",  "Contract Manufacturing",  19.8, False),
    ("PT Indo Cosmetic",      "Indonesia",    "Contract Manufacturing",  11.3, True),
    ("Cosmax Mexico",         "Mexico",       "Contract Manufacturing",   9.6, False),

    # ── Resins & Plastics ───────────────────────────────────────────────────
    ("Dow Chemical",          "USA",          "Resins & Plastics",       38.7, False),
    ("LyondellBasell",        "Netherlands",  "Resins & Plastics",       33.2, False),
    ("SABIC",                 "Saudi Arabia", "Resins & Plastics",       28.9, False),
    ("Braskem SA",            "Brazil",       "Resins & Plastics",       22.4, False),
    ("Reliance Industries",   "India",        "Resins & Plastics",       17.6, False),
    ("Lotte Chemical",        "South Korea",  "Resins & Plastics",       14.3, False),

    # ── Logistics & 3PL ─────────────────────────────────────────────────────
    ("DHL Supply Chain",      "Germany",      "Logistics",               89.4, False),
    ("Maersk Logistics",      "Netherlands",  "Logistics",               76.2, False),
    ("DB Schenker",           "Germany",      "Logistics",               54.7, False),
    ("CEVA Logistics",        "Netherlands",  "Logistics",               43.8, False),
    ("Geodis",                "France",       "Logistics",               38.2, False),
    ("Kerry Logistics",       "China",        "Logistics",               28.4, False),
    ("Blue Dart Express",     "India",        "Logistics",               18.7, False),
    ("J&T Express SEA",       "Indonesia",    "Logistics",               12.3, True),

    # ── Titanium Dioxide & Pigments ─────────────────────────────────────────
    ("Chemours Company",      "USA",          "Titanium Dioxide",        24.6, False),
    ("Venator Materials",     "UK",           "Titanium Dioxide",        18.9, False),
    ("Kronos Worldwide",      "Germany",      "Titanium Dioxide",        16.4, False),
    ("Tronox Holdings",       "USA",          "Titanium Dioxide",        14.2, False),
    ("Lomon Billions",        "China",        "Titanium Dioxide",        11.8, False),

    # ── Enzymes ─────────────────────────────────────────────────────────────
    ("Novozymes",             "Netherlands",  "Enzymes",                 22.3, False),
    ("DSM-Firmenich",         "Netherlands",  "Enzymes",                 18.7, False),
    ("AB Enzymes GmbH",       "Germany",      "Enzymes",                 12.4, True),
    ("Advanced Enzymes",      "India",        "Enzymes",                  8.6, False),
]


def generate_supplier_universe(seed=42) -> pd.DataFrame:
    np.random.seed(seed)
    rows = []

    for name, country, category, spend_m, is_single_source in SUPPLIER_DATA:
        c = COUNTRY_DATA[country]

        # ── Financial Risk (0-100, higher = riskier) ──────────────────────
        # Larger, well-known companies tend to be more financially stable
        size_adj = min(spend_m / 60.0, 1.0) * 35
        fin_base = np.clip(65 - size_adj + np.random.normal(0, 10), 5, 95)
        credit_score = int(np.clip(850 - fin_base * 1.4 + np.random.normal(0, 15), 480, 850))
        payment_delay_days = int(np.clip(fin_base * 0.45 + np.random.normal(0, 4), 0, 60))
        revenue_volatility = round(np.clip(fin_base * 0.5 + np.random.normal(0, 5), 2, 45), 1)

        # ── Geographic Risk (0-100) ────────────────────────────────────────
        geo_base = (
            (100 - c["political_stability"]) * 0.40
            + c["disaster_risk"] * 0.40
            + (5.0 - c["lpi"]) / 4.0 * 100 * 0.20
        )
        geo_risk = np.clip(geo_base + np.random.normal(0, 6), 5, 95)

        # ── Operational Risk (0-100) ───────────────────────────────────────
        ops_base = 28 + is_single_source * 22
        lead_time_variance_pct = int(np.clip(ops_base * 0.4 + np.random.normal(0, 5), 4, 40))
        defect_rate_ppm = int(np.clip(ops_base * 18 + np.random.normal(0, 150), 50, 2000))
        on_time_delivery_pct = round(np.clip(97 - ops_base * 0.35 + np.random.normal(0, 2), 68, 99.5), 1)
        ops_risk = np.clip(ops_base + np.random.normal(0, 12), 5, 95)

        # ── Concentration Risk (0-100) ─────────────────────────────────────
        spend_conc = min(spend_m / 90.0, 1.0) * 30
        conc_base = 18 + is_single_source * 52 + spend_conc
        conc_risk = np.clip(conc_base + np.random.normal(0, 7), 5, 95)

        # ── ESG Risk (0-100) ───────────────────────────────────────────────
        esg_base = (100 - c["political_stability"]) * 0.30
        if category == "Palm Oil":
            esg_base += 32           # deforestation & land use risk
        if country in ["Indonesia", "Vietnam", "Bangladesh", "Pakistan"]:
            esg_base += 18           # labor standards risk
        if category in ["Resins & Plastics", "Titanium Dioxide"]:
            esg_base += 10           # carbon & chemical emission risk
        esg_risk = np.clip(esg_base + np.random.normal(0, 10), 5, 95)

        rows.append({
            "supplier_name":          name,
            "country":                country,
            "category":               category,
            "annual_spend_usd_m":     spend_m,
            "is_single_source":       int(is_single_source),
            "lat":                    c["lat"],
            "lon":                    c["lon"],
            "credit_score":           credit_score,
            "payment_delay_days":     payment_delay_days,
            "revenue_volatility_pct": revenue_volatility,
            "lead_time_variance_pct": lead_time_variance_pct,
            "defect_rate_ppm":        defect_rate_ppm,
            "on_time_delivery_pct":   on_time_delivery_pct,
            "political_stability":    c["political_stability"],
            "disaster_risk_index":    c["disaster_risk"],
            "lpi_score":              c["lpi"],
            "financial_risk":         round(float(fin_base), 1),
            "geographic_risk":        round(float(geo_risk), 1),
            "operational_risk":       round(float(ops_risk), 1),
            "concentration_risk":     round(float(conc_risk), 1),
            "esg_risk":               round(float(esg_risk), 1),
        })

    return pd.DataFrame(rows)
