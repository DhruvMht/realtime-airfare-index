"""
DGCA Traffic & Advance-Purchase Weighting Engine for APIx
Extracts actual passenger volumes from DGCA domestic city-pair traffic datasets
and computes normalized econometric weights for routes and booking windows.
"""

import os
import logging
from typing import Dict, Tuple, List, Any
from datetime import datetime
import pandas as pd
from apix.config import (
    BASKET_ROUTES, ADVANCE_WINDOW_WEIGHTS, canonical_route,
    DGCA_WEIGHTS_PATH
)

logger = logging.getLogger("APIx.Weights")

CITY_TO_IATA = {
    "DELHI": "DEL",
    "MUMBAI": "BOM",
    "MUMBAI (MUMBAI)": "BOM",
    "BENGALURU": "BLR",
    "BANGALORE": "BLR",
    "KOLKATA": "CCU",
    "HYDERABAD": "HYD",
    "CHENNAI": "MAA",
}

# Empirical fallback weights (derived from DGCA 2024-2026 data)
DEFAULT_ROUTE_WEIGHTS: Dict[str, Dict] = {
    canonical_route("DEL", "BOM"): {"annual_pax": 12808519.0, "weight": 0.2610, "origin": "DEL", "dest": "BOM"},
    canonical_route("DEL", "BLR"): {"annual_pax": 11087413.0, "weight": 0.2259, "origin": "DEL", "dest": "BLR"},
    canonical_route("BOM", "BLR"): {"annual_pax": 7801607.0,  "weight": 0.1589, "origin": "BOM", "dest": "BLR"},
    canonical_route("DEL", "CCU"): {"annual_pax": 6598594.0,  "weight": 0.1344, "origin": "DEL", "dest": "CCU"},
    canonical_route("MAA", "DEL"): {"annual_pax": 5458519.0,  "weight": 0.1112, "origin": "MAA", "dest": "DEL"},
    canonical_route("BLR", "HYD"): {"annual_pax": 5335343.0,  "weight": 0.1086, "origin": "BLR", "dest": "HYD"},
}

class WeightManager:
    def __init__(self, weights_csv_path: str = DGCA_WEIGHTS_PATH):
        self.weights_csv_path = weights_csv_path
        self._route_weights: Dict[str, float] = {}
        self._route_metadata: Dict[str, Dict] = {}
        self.load_or_compute_weights()

    def load_or_compute_weights(self):
        """Loads weights from file or computes directly from DGCA raw traffic dataset."""
        os.makedirs(os.path.dirname(self.weights_csv_path), exist_ok=True)

        if os.path.exists(self.weights_csv_path):
            try:
                df = pd.read_csv(self.weights_csv_path)
                for _, row in df.iterrows():
                    r = row["route"]
                    self._route_weights[r] = float(row["weight"])
                    self._route_metadata[r] = {
                        "annual_pax": float(row["annual_pax"]),
                        "origin": row["origin"],
                        "destination": row["destination"],
                    }
                logger.info(f"Loaded {len(self._route_weights)} route weights from {self.weights_csv_path}")
                return
            except Exception as e:
                logger.warning(f"Error reading weights file: {e}. Recomputing from DGCA data.")

        # Attempt extraction from raw DGCA domestic city dataset
        raw_path = "india-aviation-traffic-main/aggregated/domestic/city.csv"
        if os.path.exists(raw_path):
            try:
                df = pd.read_csv(raw_path)
                df["C1"] = df["City1"].map(CITY_TO_IATA)
                df["C2"] = df["City2"].map(CITY_TO_IATA)
                sub = df.dropna(subset=["C1", "C2"]).copy()
                sub["route"] = sub.apply(lambda r: canonical_route(r["C1"], r["C2"]), axis=1)
                
                # Target routes
                target_routes = {canonical_route(o, d) for o, d in BASKET_ROUTES}
                sub = sub[sub["route"].isin(target_routes)]
                sub["pax"] = (
                    pd.to_numeric(sub["PaxToCity2"], errors="coerce").fillna(0) +
                    pd.to_numeric(sub["PaxFromCity2"], errors="coerce").fillna(0)
                )

                # Filter recent 2 years
                recent = sub[sub["Year"] >= 2024]
                agg = recent.groupby("route")["pax"].sum().reset_index()
                total_pax = agg["pax"].sum()
                agg["weight"] = agg["pax"] / total_pax

                records = []
                for _, row in agg.iterrows():
                    r = row["route"]
                    w = round(float(row["weight"]), 4)
                    p = float(row["pax"])
                    pts = r.split("-")
                    orig, dest = pts[0], pts[1]
                    self._route_weights[r] = w
                    self._route_metadata[r] = {"annual_pax": p, "origin": orig, "destination": dest}
                    records.append({
                        "route": r,
                        "origin": orig,
                        "destination": dest,
                        "annual_pax": p,
                        "weight": w,
                        "last_updated": datetime.utcnow().strftime("%Y-%m-%d"),
                    })

                out_df = pd.DataFrame(records)
                out_df.to_csv(self.weights_csv_path, index=False)
                logger.info(f"Computed DGCA weights and saved to {self.weights_csv_path}")
                return
            except Exception as e:
                logger.error(f"Error computing from raw DGCA: {e}. Using empirical defaults.")

        # Fallback to empirical defaults
        records = []
        for r, meta in DEFAULT_ROUTE_WEIGHTS.items():
            self._route_weights[r] = meta["weight"]
            self._route_metadata[r] = meta
            records.append({
                "route": r,
                "origin": meta["origin"],
                "destination": meta["dest"],
                "annual_pax": meta["annual_pax"],
                "weight": meta["weight"],
                "last_updated": datetime.utcnow().strftime("%Y-%m-%d"),
            })
        out_df = pd.DataFrame(records)
        out_df.to_csv(self.weights_csv_path, index=False)

    def get_route_weight(self, route: str) -> float:
        return self._route_weights.get(route, 1.0 / len(BASKET_ROUTES))

    def get_window_weight(self, advance_days: int) -> float:
        return ADVANCE_WINDOW_WEIGHTS.get(advance_days, 0.20)

    def get_composite_weight(self, route: str, advance_days: int) -> float:
        """Composite weight W_{r, tau} = w_r * w_tau"""
        return self.get_route_weight(route) * self.get_window_weight(advance_days)

    def get_all_route_weights(self) -> Dict[str, float]:
        return dict(self._route_weights)

    def get_route_metadata(self, route: str) -> Dict[str, Any]:
        return self._route_metadata.get(route, {})

    def get_all_route_metadata(self) -> Dict[str, Dict]:
        return dict(self._route_metadata)
