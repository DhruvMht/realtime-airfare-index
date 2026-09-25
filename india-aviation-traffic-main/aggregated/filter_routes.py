"""
Filter a DGCA city-pair passenger traffic dataset down to the
APIx project's 6-route basket, and compute normalized weights.

Adjust ORIGIN_COL / DEST_COL / PAX_COL to match your actual CSV headers
-- these vary between DGCA's raw tables and community-parsed versions
(e.g. Vonter/india-aviation-traffic uses different naming than DGCA's
own portal exports).
"""

import pandas as pd

# ---- 1. Load the raw dataset ----
INPUT_FILE = "dgca_city_pair_traffic.csv"   # <-- point this at your downloaded file
df = pd.read_csv(INPUT_FILE)

print("Columns found:", list(df.columns))
print(df.head())

# ---- 2. Set these to match your actual column names ----
ORIGIN_COL = "Origin"
DEST_COL = "Destination"
PAX_COL = "Passengers"          # or "Total_Passengers", "Pax_Carried", etc.

# ---- 3. Define your basket ----
# Use IATA codes as they appear in the dataset -- check df[ORIGIN_COL].unique()
# if you're not sure of the exact spelling/codes DGCA uses.
BASKET = [
    ("DEL", "BOM"),
    ("DEL", "BLR"),
    ("BOM", "BLR"),
    ("DEL", "CCU"),
    ("BLR", "HYD"),
    ("MAA", "DEL"),
]

def route_key(o, d):
    """Undirected route key so DEL-BOM and BOM-DEL count as one route."""
    return tuple(sorted([o, d]))

# ---- 4. Tag every row with its undirected route, then filter ----
df["route_key"] = df.apply(lambda r: route_key(r[ORIGIN_COL], r[DEST_COL]), axis=1)
basket_keys = {route_key(o, d) for o, d in BASKET}

filtered = df[df["route_key"].isin(basket_keys)].copy()

if filtered.empty:
    raise ValueError(
        "No rows matched your basket -- check that BASKET codes match "
        "the exact spelling/case used in the dataset (print df[ORIGIN_COL].unique())."
    )

# ---- 5. Aggregate: sum passengers per route across carriers & both directions ----
route_totals = (
    filtered.groupby("route_key")[PAX_COL]
    .sum()
    .reset_index()
    .rename(columns={PAX_COL: "total_passengers"})
)
route_totals["route"] = route_totals["route_key"].apply(lambda k: f"{k[0]}-{k[1]}")
route_totals = route_totals.drop(columns="route_key")

# ---- 6. Normalize into weights that sum to 1 ----
route_totals["weight"] = route_totals["total_passengers"] / route_totals["total_passengers"].sum()
route_totals = route_totals.sort_values("weight", ascending=False)

print("\nRoute weights:")
print(route_totals.to_string(index=False))

# ---- 7. Save as the reference file the scraper + index module both read ----
route_totals.to_csv("route_weights.csv", index=False)
print("\nSaved to route_weights.csv")
