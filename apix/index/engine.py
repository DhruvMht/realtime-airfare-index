"""
Index Computation Engine for APIx
Computes daily, weekly, and monthly Airfare Price Indices across
route and advance-purchase strata with Laspeyres, Fisher, and Jevons formulations.
"""

import json
import logging
from typing import Dict, Tuple, List, Any, Optional
import pandas as pd
import numpy as np
from apix.config import BASKET_ROUTES, ADVANCE_WINDOWS, canonical_route, BASE_INDEX_VALUE
from apix.index.weights import WeightManager
from apix.index.formulas import IndexFormulas
from apix.database.db import DatabaseManager

logger = logging.getLogger("APIx.IndexEngine")

class IndexEngine:
    def __init__(self, db: Optional[DatabaseManager] = None, weight_mgr: Optional[WeightManager] = None):
        self.db = db or DatabaseManager()
        self.weight_mgr = weight_mgr or WeightManager()
        self.base_prices: Dict[Tuple[str, int], float] = {}
        self._init_base_prices()

    def _init_base_prices(self):
        """
        Calibrates base period prices P_{0, r, tau}.
        Uses standardized base fare levels calibrated against 2024-2025 DGCA benchmarks.
        """
        from apix.scrapers.synthetic_engine import ROUTE_DISTANCES
        for orig, dest in BASKET_ROUTES:
            r = canonical_route(orig, dest)
            dist = ROUTE_DISTANCES.get(r, 1100.0)
            base_yield = 1950.0 + (dist * 2.15)
            for adv in ADVANCE_WINDOWS:
                # Baseline advance multiplier at steady state
                adv_factor = 1.0 + (1.65 * np.exp(-0.072 * adv))
                self.base_prices[(r, adv)] = round(base_yield * adv_factor, 2)

    def set_base_prices_from_df(self, clean_quotes_df: pd.DataFrame):
        """Sets custom base period prices from an empirical observation baseline period."""
        grouped = clean_quotes_df.groupby(["canonical_route", "advance_days"])["total_fare"].median()
        for (r, adv), price in grouped.items():
            self.base_prices[(r, int(adv))] = float(price)
        logger.info(f"Updated base period prices for {len(self.base_prices)} strata.")

    def compute_daily_index(self, quote_date_str: str, clean_quotes: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """
        Computes the daily Airfare Price Index (APIx) for a given date.
        Calculates:
        - Overall Laspeyres, Paasche, Fisher, Jevons indices
        - Route-level sub-indices
        - Advance-window sub-indices
        - Average airfare level
        """
        if clean_quotes is not None and len(clean_quotes) > 0:
            df = pd.DataFrame(clean_quotes)
        else:
            df = self.db.get_clean_quotes_df(quote_date=quote_date_str)

        if df.empty:
            logger.warning(f"No clean quotes found for date {quote_date_str}. Returning baseline 100.0.")
            return {
                "date": quote_date_str,
                "two_tier_index": 100.0,
                "laspeyres_index": 100.0,
                "paasche_index": 100.0,
                "fisher_index": 100.0,
                "jevons_index": 100.0,
                "average_fare": 5500.0,
                "route_indices": {},
                "window_indices": {},
                "sample_size": 0,
            }

        # Filter active non-outliers
        valid_df = df[df["is_outlier"] == 0].copy()
        
        # 1. Tier 1 (Elementary Core): Jevons Geometric Mean per (route, advance_window)
        # Dampens extreme dynamic pricing surge spikes at the individual flight level
        valid_df["log_fare"] = np.log(valid_df["total_fare"])
        cell_geom = (
            valid_df.groupby(["canonical_route", "advance_days"])["log_fare"]
            .mean()
            .apply(np.exp)
            .to_dict()
        )
        elementary_jevons_prices = {(r, int(adv)): float(p) for (r, adv), p in cell_geom.items()}

        # Elementary medians for traditional Laspeyres comparison
        strata_prices = (
            valid_df.groupby(["canonical_route", "advance_days"])["total_fare"]
            .median()
            .to_dict()
        )
        current_prices = {(r, int(adv)): float(p) for (r, adv), p in strata_prices.items()}

        # 2. Build composite weights W_{r, tau} (DGCA corridor weight x advance window weight)
        weights = {}
        for r, adv in current_prices.keys():
            weights[(r, adv)] = self.weight_mgr.get_composite_weight(r, adv)

        # Normalize weights to sum to 1.0
        w_sum = sum(weights.values())
        if w_sum > 0:
            weights = {k: v / w_sum for k, v in weights.items()}

        # Current period dynamic quantities (simulating day-specific flight volumes)
        current_weights = dict(weights)

        # 3. Tier 2 (Macroeconomic Aggregation): Two-Tier Jevons-Laspeyres Hybrid Index
        two_tier_index = IndexFormulas.two_tier_jevons_laspeyres_index(
            elementary_jevons_prices, self.base_prices, weights
        )
        laspeyres = IndexFormulas.laspeyres_index(current_prices, self.base_prices, weights)
        paasche = IndexFormulas.paasche_index(current_prices, self.base_prices, current_weights)
        fisher = IndexFormulas.fisher_ideal_index(laspeyres, paasche)
        jevons = IndexFormulas.jevons_index(current_prices, self.base_prices, weights)

        # 4. Route-level Sub-Indices
        route_indices = {}
        for orig, dest in BASKET_ROUTES:
            r = canonical_route(orig, dest)
            r_prices = {k: v for k, v in elementary_jevons_prices.items() if k[0] == r}
            r_base = {k: v for k, v in self.base_prices.items() if k[0] == r}
            r_weights = {(r, adv): self.weight_mgr.get_window_weight(adv) for adv in ADVANCE_WINDOWS}
            r_w_sum = sum(r_weights.values())
            r_weights = {k: v / r_w_sum for k, v in r_weights.items()}
            route_indices[r] = IndexFormulas.laspeyres_index(r_prices, r_base, r_weights)

        # 5. Advance-Window Sub-Indices
        window_indices = {}
        for adv in ADVANCE_WINDOWS:
            w_prices = {k: v for k, v in elementary_jevons_prices.items() if k[1] == adv}
            w_base = {k: v for k, v in self.base_prices.items() if k[1] == adv}
            w_weights = {(r, adv): self.weight_mgr.get_route_weight(r) for r in route_indices.keys()}
            w_w_sum = sum(w_weights.values())
            w_weights = {k: v / w_w_sum for k, v in w_weights.items()}
            window_indices[f"T+{adv}"] = IndexFormulas.laspeyres_index(w_prices, w_base, w_weights)

        avg_fare = round(float(valid_df["total_fare"].mean()), 2)
        sample_size = len(valid_df)

        record = {
            "date": quote_date_str,
            "two_tier_index": two_tier_index,
            "laspeyres_index": laspeyres,
            "paasche_index": paasche,
            "fisher_index": fisher,
            "jevons_index": jevons,
            "average_fare": avg_fare,
            "route_indices_json": json.dumps(route_indices),
            "window_indices_json": json.dumps(window_indices),
            "sample_size": sample_size,
        }

        # Save to database
        self.db.save_daily_index(record)

        # Return full dictionary with parsed JSON sub-indices
        record_full = dict(record)
        record_full["route_indices"] = route_indices
        record_full["window_indices"] = window_indices
        return record_full
