"""
Data Cleaning and Normalization Pipeline for APIx
Handles:
1. Multi-source deduplication across airline direct & OTA quotes
2. Stratified outlier detection (Tukey's IQR per route and advance window)
3. Missing values and sold-out flight imputation without downward bias
4. Integration with fare decomposition
"""

import logging
from typing import List, Dict, Any, Tuple
from datetime import datetime
import pandas as pd
import numpy as np
from apix.config import canonical_route, AIRLINES, OUTLIER_IQR_MULTIPLIER
from apix.pipeline.decomposer import FareDecomposer

logger = logging.getLogger("APIx.Cleaner")

CARRIER_NAMES = {a["code"]: a["name"] for a in AIRLINES}

class DataCleaningPipeline:
    def __init__(self, iqr_multiplier: float = OUTLIER_IQR_MULTIPLIER):
        self.iqr_multiplier = iqr_multiplier

    def clean_quotes(self, raw_quotes: List[Dict[str, Any]], quote_date_str: str) -> List[Dict[str, Any]]:
        """
        Executes end-to-end data cleaning workflow:
        Raw Quotes -> Deduplication -> Fare Decomposition -> Outlier Tagging -> Imputation -> Clean Quotes
        """
        if not raw_quotes:
            return []

        df = pd.DataFrame(raw_quotes)

        # 1. Canonical route tagging
        df["canonical_route"] = df.apply(
            lambda r: canonical_route(r["origin"], r["destination"]), axis=1
        )
        df["carrier_name"] = df["carrier_code"].map(lambda c: CARRIER_NAMES.get(c, c))
        df["quote_date"] = quote_date_str

        # 2. Multi-source Deduplication
        # If the same flight is scraped from both the airline website and an OTA,
        # explicitly prioritize the direct airline portal quote
        ota_names = {"MakeMyTrip", "EaseMyTrip", "Yatra", "Cleartrip", "Ixigo"}
        df["is_ota_source"] = df["source"].map(lambda s: 1 if s in ota_names else 0)
        df = df.sort_values(by=["is_ota_source", "source"], ascending=[True, True])
        initial_count = len(df)
        df = df.drop_duplicates(
            subset=["canonical_route", "flight_number", "departure_date", "advance_days"],
            keep="first"
        ).drop(columns=["is_ota_source"]).copy()
        dedup_dropped = initial_count - len(df)
        logger.info(f"Deduplication removed {dedup_dropped} duplicate quotes.")

        # 3. Stratified Outlier Detection (per route and advance-purchase window)
        df["is_outlier"] = 0
        for (c_route, adv), group in df.groupby(["canonical_route", "advance_days"]):
            valid_fares = group[group["is_sold_out"] == 0]["quoted_fare"]
            if len(valid_fares) >= 4:
                q25 = valid_fares.quantile(0.25)
                q75 = valid_fares.quantile(0.75)
                iqr = q75 - q25
                lower_bound = max(1000.0, q25 - self.iqr_multiplier * iqr)
                upper_bound = q75 + self.iqr_multiplier * iqr

                outlier_indices = group[
                    (group["quoted_fare"] < lower_bound) | (group["quoted_fare"] > upper_bound)
                ].index
                df.loc[outlier_indices, "is_outlier"] = 1

        outlier_count = int(df["is_outlier"].sum())
        logger.info(f"Outlier filter flagged {outlier_count} anomalous price quotes.")

        # 4. Sold-out flights imputation
        # If a flight is sold out, we do NOT zero-fill or drop blindly (which understates capacity/inflation).
        # We impute using the 85th percentile of operating flights on that sector/window (last seat yield).
        df["imputed"] = 0
        sold_out_mask = (df["is_sold_out"] == 1)
        if sold_out_mask.any():
            for idx in df[sold_out_mask].index:
                row = df.loc[idx]
                peers = df[
                    (df["canonical_route"] == row["canonical_route"]) &
                    (df["advance_days"] == row["advance_days"]) &
                    (df["is_sold_out"] == 0) &
                    (df["is_outlier"] == 0)
                ]
                if not peers.empty:
                    imputed_fare = peers["quoted_fare"].quantile(0.85)
                    df.loc[idx, "quoted_fare"] = imputed_fare
                    df.loc[idx, "imputed"] = 1
                else:
                    df.loc[idx, "is_outlier"] = 1  # drop if no peers

        # 5. Fare Decomposition (Base, PSF, UDF, GST, Convenience Fee)
        decomposed_rows = []
        created_at_str = datetime.utcnow().isoformat()
        for _, row in df.iterrows():
            comp = FareDecomposer.decompose(row.to_dict())
            decomposed_rows.append({
                "source": row["source"],
                "carrier_code": row["carrier_code"],
                "carrier_name": row["carrier_name"],
                "flight_number": row["flight_number"],
                "origin": row["origin"],
                "destination": row["destination"],
                "canonical_route": row["canonical_route"],
                "departure_date": row["departure_date"],
                "advance_days": int(row["advance_days"]),
                "quote_date": quote_date_str,
                "fare_class": row.get("fare_class", "Economy"),
                "base_fare": comp["base_fare"],
                "psf": comp["psf"],
                "udf": comp["udf"],
                "gst": comp["gst"],
                "convenience_fee": comp["convenience_fee"],
                "total_fare": comp["total_fare"],
                "is_outlier": int(row["is_outlier"]),
                "is_sold_out": int(row["is_sold_out"]),
                "imputed": int(row["imputed"]),
                "created_at": created_at_str,
            })

        logger.info(f"Cleaned pipeline produced {len(decomposed_rows)} valid normalized records.")
        return decomposed_rows
