"""
DGCA Price Ceiling & Festive Surge Watchdog Engine
Monitors airline dynamic pricing across India's top 6 domestic trunk corridors
against statutory distance-based tariff bands (Rule 135 / MoCA Order AV.29017/26/2020-DT)
and tiered econometric surge benchmarks.
"""

from typing import Dict, List, Any, Optional
import pandas as pd
import numpy as np

from apix.config import (
    DGCA_CORRIDOR_CEILINGS,
    ELEVATED_SURGE_RATIO,
    PREDATORY_SURGE_RATIO,
    REGULATORY_ALERT_TIERS,
    FESTIVE_WINDOWS,
    canonical_route,
)

class DGCAWatchdogManager:
    def __init__(self, ceilings: Optional[Dict[str, Dict[str, Any]]] = None):
        self.ceilings = ceilings or DGCA_CORRIDOR_CEILINGS
        self.elevated_ratio_threshold = ELEVATED_SURGE_RATIO
        self.surge_ratio_threshold = PREDATORY_SURGE_RATIO
        self.alert_tiers = REGULATORY_ALERT_TIERS
        self.festive_windows = FESTIVE_WINDOWS

    def get_corridor_ceilings(self) -> Dict[str, Dict[str, Any]]:
        """Returns statutory price ceiling benchmarks for the 6 trunk corridors."""
        return self.ceilings

    def get_festive_windows(self) -> List[Dict[str, Any]]:
        """Returns registered festive rush windows and affected corridors."""
        return self.festive_windows

    def analyze_quotes(self, quotes_df: pd.DataFrame) -> Dict[str, Any]:
        """
        Performs comprehensive 4-Tier regulatory surveillance on flight quotes:
        - Level 3: Hard ceiling breaches (total_fare > advisory_cap)
        - Level 2: Predatory surge pricing (surge >= 2.5x corridor median)
        - Level 1: Elevated dynamic surge (2.0x <= surge < 2.5x)
        - Level 0: Compliant pricing
        - Computes 95th Percentile (P95) representative fares
        - Prepares corridor-level benchmarks, carrier scorecards, and regulatory audit records
        """
        if quotes_df.empty:
            return {
                "total_flights": 0,
                "total_breaches": 0,
                "statutory_cap_breaches": 0,
                "predatory_surges": 0,
                "elevated_surges": 0,
                "fleet_compliance_pct": 100.0,
                "corridor_summary": pd.DataFrame(),
                "carrier_compliance": pd.DataFrame(),
                "flagged_instances": pd.DataFrame(),
                "all_evaluated": pd.DataFrame(),
            }

        df = quotes_df.copy()
        if "canonical_route" not in df.columns:
            df["canonical_route"] = df.apply(lambda r: canonical_route(r["origin"], r["destination"]), axis=1)

        def get_ceiling(r):
            c_info = self.ceilings.get(r, {})
            return c_info.get("advisory_cap", 15000.0)

        def get_median(r):
            c_info = self.ceilings.get(r, {})
            return c_info.get("historical_median", 5500.0)

        def get_band(r):
            c_info = self.ceilings.get(r, {})
            return c_info.get("band", "Standard Trunk")

        df["advisory_cap"] = df["canonical_route"].map(get_ceiling)
        df["corridor_median"] = df["canonical_route"].map(get_median)
        df["stage_band"] = df["canonical_route"].map(get_band)

        df["surge_ratio"] = (df["total_fare"] / df["corridor_median"]).round(2)
        df["excess_amount"] = (df["total_fare"] - df["advisory_cap"]).clip(lower=0.0)
        
        # Flight-level Tier Classification
        df["is_ceiling_breach"] = df["total_fare"] > df["advisory_cap"]
        df["is_predatory_surge"] = (df["surge_ratio"] >= self.surge_ratio_threshold) & (~df["is_ceiling_breach"])
        df["is_elevated_surge"] = (df["surge_ratio"] >= self.elevated_ratio_threshold) & (df["surge_ratio"] < self.surge_ratio_threshold) & (~df["is_ceiling_breach"])
        
        # Flagged = Actionable anomalies (Level 3 Cap Breaches + Level 2 Predatory Surges)
        df["is_flagged"] = df["is_ceiling_breach"] | (df["surge_ratio"] >= self.surge_ratio_threshold)

        def classify_flight_tier(r):
            if r["is_ceiling_breach"]:
                return "Level 3: Cap Breach", "🚨 Statutory Cap Exceeded"
            elif r["surge_ratio"] >= self.surge_ratio_threshold:
                return "Level 2: Predatory", "⚠️ Predatory Surge (≥2.5x)"
            elif r["is_elevated_surge"]:
                return "Level 1: Elevated", "⚡ Elevated Surge (2.0x–2.5x)"
            return "Level 0: Normal", "🟢 Compliant"

        tier_info = df.apply(classify_flight_tier, axis=1)
        df["alert_tier"] = [t[0] for t in tier_info]
        df["violation_type"] = [t[1] for t in tier_info]

        total_flights = len(df)
        flagged_df = df[df["is_flagged"]].copy()
        total_breaches = len(flagged_df)
        total_cap_breaches = int(df["is_ceiling_breach"].sum())
        total_predatory_surges = int(df["is_predatory_surge"].sum())
        total_elevated_surges = int(df["is_elevated_surge"].sum())
        
        fleet_compliance_pct = round(((total_flights - total_breaches) / total_flights) * 100.0, 2) if total_flights > 0 else 100.0

        corridor_list = []
        for r, c_info in self.ceilings.items():
            r_df = df[df["canonical_route"] == r]
            if not r_df.empty:
                r_max = float(r_df["total_fare"].max())
                r_min = float(r_df["total_fare"].min())
                r_median = float(r_df["total_fare"].median())
                r_mean = float(r_df["total_fare"].mean())
                r_p95 = float(np.percentile(r_df["total_fare"], 95))
                r_cap_breaches = int(r_df["is_ceiling_breach"].sum())
                r_predatory = int(r_df["is_predatory_surge"].sum())
                r_elevated = int(r_df["is_elevated_surge"].sum())
                r_total = len(r_df)
                r_max_surge = float(r_df["surge_ratio"].max())
                r_comp_pct = round(((r_total - (r_cap_breaches + r_predatory)) / r_total) * 100.0, 1)

                # Tiered Corridor Classification
                if r_cap_breaches > 0:
                    c_status = f"🔴 Statutory Cap Violation ({r_cap_breaches})"
                    c_tier = "Level 3: Statutory Breach"
                elif r_predatory > 0:
                    c_status = f"🟠 Predatory Surge Alert ({r_predatory})"
                    c_tier = "Level 2: Predatory Surge"
                elif r_elevated > 0 or r_comp_pct < 98.0:
                    c_status = f"🟡 Elevated Vigil ({r_elevated})"
                    c_tier = "Level 1: Elevated Vigil"
                else:
                    c_status = "🟢 Compliant"
                    c_tier = "Level 0: Compliant"
            else:
                r_max = 0.0
                r_min = 0.0
                r_median = c_info["historical_median"]
                r_mean = c_info["historical_median"]
                r_p95 = c_info["historical_median"]
                r_cap_breaches = 0
                r_predatory = 0
                r_elevated = 0
                r_total = 0
                r_max_surge = 1.0
                r_comp_pct = 100.0
                c_status = "🟢 Compliant"
                c_tier = "Level 0: Compliant"

            corridor_list.append({
                "Corridor": r,
                "Distance": f"{c_info['distance_km']} km",
                "DGCA Band": c_info["band"],
                "Advisory Cap": c_info["advisory_cap"],
                "Historical Median": c_info["historical_median"],
                "Observed Mean": round(r_mean, 2),
                "Observed Median": round(r_median, 2),
                "95th Percentile": round(r_p95, 2),
                "Observed Peak": r_max,
                "Peak Surge Factor": f"{r_max_surge:.1f}x",
                "Total Flights": r_total,
                "Cap Breaches": r_cap_breaches,
                "Surge Alerts": r_predatory,
                "Compliance Rate": f"{r_comp_pct}%",
                "Status": c_status,
                "Alert Tier": c_tier,
            })

        df_corridor_summary = pd.DataFrame(corridor_list)

        carrier_list = []
        for carrier, g in df.groupby("carrier_name"):
            c_total = len(g)
            c_cap = int(g["is_ceiling_breach"].sum())
            c_pred = int(g["is_predatory_surge"].sum())
            c_breaches = c_cap + c_pred
            c_comp_pct = round(((c_total - c_breaches) / c_total) * 100.0, 1)
            
            if c_cap > 0:
                c_stat = f"🔴 Cap Violation ({c_cap})"
            elif c_pred > 0:
                c_stat = f"🟠 Surge Warning ({c_pred})"
            elif c_comp_pct < 98.0:
                c_stat = "🟡 Advisory Vigil"
            else:
                c_stat = "🟢 Fully Compliant"

            carrier_list.append({
                "Airline": carrier,
                "Monitored Flights": c_total,
                "Compliant Flights": c_total - c_breaches,
                "Cap Breaches": c_cap,
                "Surge Alerts": c_pred,
                "Compliance Rate": f"{c_comp_pct}%",
                "Max Quoted Fare": f"₹{g['total_fare'].max():,.0f}",
                "Status": c_stat,
            })
        df_carrier_compliance = pd.DataFrame(carrier_list).sort_values("Monitored Flights", ascending=False) if carrier_list else pd.DataFrame()

        audit_cols = [
            "flight_number", "carrier_name", "canonical_route", "origin", "destination",
            "departure_date", "advance_days", "total_fare", "advisory_cap", "excess_amount",
            "surge_ratio", "is_ceiling_breach", "is_predatory_surge", "is_elevated_surge",
            "alert_tier", "violation_type"
        ]
        available_cols = [c for c in audit_cols if c in flagged_df.columns]
        df_audit = flagged_df[available_cols].copy()
        if not df_audit.empty:
            df_audit["horizon"] = df_audit["advance_days"].map(lambda d: f"T+{d}")
            df_audit["excess_inr"] = df_audit["excess_amount"].map(lambda x: f"₹{x:,.0f}" if x > 0 else "₹0")
            df_audit["fare_inr"] = df_audit["total_fare"].map(lambda x: f"₹{x:,.0f}")
            df_audit["cap_inr"] = df_audit["advisory_cap"].map(lambda x: f"₹{x:,.0f}")
            df_audit = df_audit.sort_values("total_fare", ascending=False)

        return {
            "total_flights": total_flights,
            "total_breaches": total_breaches,
            "statutory_cap_breaches": total_cap_breaches,
            "predatory_surges": total_predatory_surges,
            "elevated_surges": total_elevated_surges,
            "fleet_compliance_pct": fleet_compliance_pct,
            "corridor_summary": df_corridor_summary,
            "carrier_compliance": df_carrier_compliance,
            "flagged_instances": df_audit,
            "all_evaluated": df,
        }