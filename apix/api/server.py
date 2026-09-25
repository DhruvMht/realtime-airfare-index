"""
FastAPI Microservice for APIx (Real-time Airfare Price Index for India)
Official programmatic data delivery endpoints for:
- National Statistical Office (NSO / MoSPI) for CPI Integration
- Reserve Bank of India (RBI) Monetary Policy & Research
"""

import json
from typing import Optional, List, Dict, Any
import pandas as pd
from fastapi import FastAPI, Query, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from apix.database.db import DatabaseManager
from apix.index.weights import WeightManager
from apix.backtest.backtester import DGCABacktester
from apix.scrapers.scheduler import ScraperScheduler
from apix.pipeline.cleaner import DataCleaningPipeline
from apix.index.engine import IndexEngine
from apix.index.esankhyiki import ESankhyikiManager
from apix.index.watchdog import DGCAWatchdogManager
from apix.config import BASKET_ROUTES, ADVANCE_WINDOWS, canonical_route, AIRPORT_DATA

app = FastAPI(
    title="APIx: Real-time Airfare Price Index for India",
    description="High-frequency automated airfare data and econometric index engine for CPI Transport augmentation (MoSPI/NSO & RBI).",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Enable CORS for external research dashboards and cross-origin tools
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

db = DatabaseManager()
weight_mgr = WeightManager()
backtester = DGCABacktester(db)
scheduler = ScraperScheduler(db)
cleaner = DataCleaningPipeline()
index_engine = IndexEngine(db, weight_mgr)
esankhyiki_mgr = ESankhyikiManager()
watchdog_mgr = DGCAWatchdogManager()

@app.get("/", tags=["System"])
def root():
    return {
        "platform": "APIx - Real-time Airfare Price Index for India",
        "agency_consumers": ["NSO (MoSPI)", "Monetary Policy Committee (RBI)"],
        "version": "1.0.0",
        "documentation": "/docs",
        "status": "OPERATIONAL",
    }

@app.get("/api/v1/health", tags=["System"])
def health():
    """System health check and database statistics."""
    with db.get_connection() as conn:
        cursor = conn.cursor()
        raw_c = cursor.execute("SELECT COUNT(*) FROM raw_quotes").fetchone()[0]
        clean_c = cursor.execute("SELECT COUNT(*) FROM clean_quotes").fetchone()[0]
        index_c = cursor.execute("SELECT COUNT(*) FROM daily_index").fetchone()[0]
    return {
        "status": "HEALTHY",
        "database": "CONNECTED",
        "records": {
            "raw_quotes": raw_c,
            "clean_quotes": clean_c,
            "daily_index_records": index_c,
        },
    }

@app.get("/api/v1/index/latest", tags=["Airfare Price Index"])
def get_latest_index():
    """Returns the most recent daily Airfare Price Index (APIx) values."""
    df = db.get_daily_indices()
    if df.empty:
        raise HTTPException(status_code=404, detail="No index data calculated yet.")
    latest = df.iloc[-1].to_dict()
    latest["route_indices"] = json.loads(latest.get("route_indices_json", "{}"))
    latest["window_indices"] = json.loads(latest.get("window_indices_json", "{}"))
    return latest

@app.get("/api/v1/index/history", tags=["Airfare Price Index"])
def get_index_history(
    start_date: Optional[str] = Query(None, description="Start date YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="End date YYYY-MM-DD"),
    frequency: str = Query("daily", enum=["daily", "weekly", "monthly"]),
):
    """Fetches historical APIx time-series with frequency aggregation."""
    df = db.get_daily_indices(start_date=start_date, end_date=end_date)
    if df.empty:
        return []

    # Frequency resampling
    if frequency == "weekly":
        df["week"] = pd.to_datetime(df["date"]).dt.to_period("W").astype(str)
        agg_df = df.groupby("week").agg({
            "laspeyres_index": "mean",
            "fisher_index": "mean",
            "jevons_index": "mean",
            "average_fare": "mean",
            "sample_size": "sum",
        }).reset_index().rename(columns={"week": "date"})
        return agg_df.round(2).to_dict(orient="records")

    elif frequency == "monthly":
        df["month"] = pd.to_datetime(df["date"]).dt.to_period("M").astype(str)
        agg_df = df.groupby("month").agg({
            "laspeyres_index": "mean",
            "fisher_index": "mean",
            "jevons_index": "mean",
            "average_fare": "mean",
            "sample_size": "sum",
        }).reset_index().rename(columns={"month": "date"})
        return agg_df.round(2).to_dict(orient="records")

    records = []
    for _, row in df.iterrows():
        item = row.to_dict()
        item["route_indices"] = json.loads(item.get("route_indices_json", "{}"))
        item["window_indices"] = json.loads(item.get("window_indices_json", "{}"))
        records.append(item)
    return records

@app.get("/api/v1/routes", tags=["Metadata & Weights"])
def get_routes_metadata():
    """Returns the 6 representative DGCA routes, airport coordinates, and passenger weights."""
    weights = weight_mgr.get_all_route_weights()
    meta = weight_mgr.get_all_route_metadata()
    res = []
    for orig, dest in BASKET_ROUTES:
        r = canonical_route(orig, dest)
        orig_data = AIRPORT_DATA.get(orig, {})
        dest_data = AIRPORT_DATA.get(dest, {})
        r_meta = meta.get(r, {})
        pax = r_meta.get("annual_pax", 0)
        res.append({
            "route": r,
            "origin": orig,
            "origin_city": orig_data.get("city", orig),
            "destination": dest,
            "dest_city": dest_data.get("city", dest),
            "annual_passengers": pax,
            "dgca_passenger_weight": weights.get(r, 0.166),
            "coordinates": {
                "origin": [orig_data.get("lat"), orig_data.get("lon")],
                "destination": [dest_data.get("lat"), dest_data.get("lon")],
            }
        })
    return res

@app.get("/api/v1/lead-time-curve", tags=["Analytics"])
def get_lead_time_curve(route: Optional[str] = Query(None, description="e.g. BOM-DEL")):
    """Returns the advance-booking dynamic pricing elasticity curve (T+1 to T+45)."""
    quotes_df = db.get_clean_quotes_df(route=route)
    if quotes_df.empty:
        raise HTTPException(status_code=404, detail="No quote data available for curve.")
    
    curve = (
        quotes_df.groupby("advance_days")
        .agg(
            median_fare=("total_fare", "median"),
            base_fare=("base_fare", "median"),
            min_fare=("total_fare", "min"),
            max_fare=("total_fare", "max"),
            sample_count=("total_fare", "count"),
        )
        .reset_index()
    )
    return curve.round(2).to_dict(orient="records")

@app.get("/api/v1/decomposition", tags=["Analytics"])
def get_fare_decomposition(route: Optional[str] = None):
    """Returns breakdown of average fare into Base Fare, PSF, UDF, GST, and Convenience fee."""
    quotes_df = db.get_clean_quotes_df(route=route)
    if quotes_df.empty:
        raise HTTPException(status_code=404, detail="No data available.")
    
    return {
        "base_fare_avg": round(float(quotes_df["base_fare"].mean()), 2),
        "psf_avg": round(float(quotes_df["psf"].mean()), 2),
        "udf_avg": round(float(quotes_df["udf"].mean()), 2),
        "gst_avg": round(float(quotes_df["gst"].mean()), 2),
        "convenience_fee_avg": round(float(quotes_df["convenience_fee"].mean()), 2),
        "total_fare_avg": round(float(quotes_df["total_fare"].mean()), 2),
        "base_fare_pct": round(float(quotes_df["base_fare"].mean() / quotes_df["total_fare"].mean()) * 100.0, 1),
        "taxes_fees_pct": round(float((quotes_df["total_fare"].mean() - quotes_df["base_fare"].mean()) / quotes_df["total_fare"].mean()) * 100.0, 1),
    }

@app.get("/api/v1/backtest", tags=["Econometric Validation"])
def get_backtest_metrics():
    """Returns 90-day backtesting and correlation against DGCA benchmarks."""
    return backtester.evaluate_90day_backtest()

@app.get("/api/v1/esankhyiki/augmentation", tags=["eSankhyiki Integration"])
def get_esankhyiki_augmentation():
    """
    Returns monthly comparison between official lagged eSankhyiki CPI Transport Index
    and APIx Augmented Transport Index, demonstrating the captured dynamic pricing inflation gap.
    """
    df = db.get_daily_indices()
    return esankhyiki_mgr.compute_cpi_augmentation(df)

@app.get("/api/v1/esankhyiki/export", tags=["eSankhyiki Integration"])
def get_esankhyiki_export():
    """
    Outputs official eSankhyiki batch ingestion feed formatted according to
    MoSPI Price Statistics Division (PSD) standards.
    """
    df = db.get_daily_indices()
    return esankhyiki_mgr.generate_esankhyiki_feed(df)

class ScrapeTriggerRequest(BaseModel):
    quote_date: Optional[str] = None

@app.post("/api/v1/scraper/trigger", tags=["Scraping Engine"])
def trigger_scraping(req: ScrapeTriggerRequest, background_tasks: BackgroundTasks):
    """Triggers an ethical multi-source scrape run for the requested date."""
    target_date = req.quote_date or pd.Timestamp.now().strftime("%Y-%m-%d")
    
    def _execute_pipeline():
        scrape_res = scheduler.run_daily_scrape(quote_date_str=target_date)
        raw_quotes = db.get_connection().execute(
            "SELECT * FROM raw_quotes WHERE scraped_at LIKE ?", (f"{target_date}%",)
        ).fetchall()
        clean_records = cleaner.clean_quotes([dict(r) for r in raw_quotes], quote_date_str=target_date)
        db.insert_clean_quotes(clean_records)
        index_engine.compute_daily_index(quote_date_str=target_date, clean_quotes=clean_records)

    background_tasks.add_task(_execute_pipeline)
    return {
        "message": f"Scraper and index pipeline scheduled for {target_date}.",
        "ethical_guards": ["robots.txt check", "domain rate limiter", "jitter delay"],
    }

@app.get("/api/v1/watchdog/summary", tags=["DGCA Price Ceiling Watchdog"])
def get_watchdog_summary():
    """
    Returns automated surveillance status across India's top 6 domestic trunk corridors
    against DGCA statutory distance-based price ceilings and festive surge thresholds.
    """
    with db.get_connection() as conn:
        quotes_df = pd.read_sql("SELECT * FROM clean_quotes WHERE is_outlier = 0", conn)
    res = watchdog_mgr.analyze_quotes(quotes_df)
    
    flagged_preview = []
    if not res["flagged_instances"].empty:
        for _, row in res["flagged_instances"].head(10).iterrows():
            flagged_preview.append({
                "flight_number": row.get("flight_number"),
                "carrier": row.get("carrier_name"),
                "corridor": row.get("canonical_route"),
                "departure_date": row.get("departure_date"),
                "advance_horizon": row.get("horizon", f"T+{row.get('advance_days')}"),
                "quoted_fare": float(row.get("total_fare", 0.0)),
                "advisory_cap": float(row.get("advisory_cap", 0.0)),
                "excess_amount": float(row.get("excess_amount", 0.0)),
                "surge_ratio": float(row.get("surge_ratio", 1.0)),
                "is_ceiling_breach": bool(row.get("is_ceiling_breach", False)),
                "alert_tier": row.get("alert_tier", "Level 2: Predatory"),
                "violation_type": row.get("violation_type", "⚠️ Predatory Surge (≥2.5x)"),
            })

    return {
        "status": "ACTIVE_SURVEILLANCE",
        "regulatory_authority": "Directorate General of Civil Aviation (DGCA) & MoCA",
        "rule_basis": "Rule 135, Aircraft Rules 1937 & MoCA Order AV.29017/26/2020-DT",
        "monitored_corridors_count": len(watchdog_mgr.get_corridor_ceilings()),
        "total_flights_analyzed": res["total_flights"],
        "total_flagged_breaches": res["total_breaches"],
        "statutory_cap_breaches": res["statutory_cap_breaches"],
        "predatory_surges": res["predatory_surges"],
        "elevated_surges": res["elevated_surges"],
        "fleet_compliance_pct": res["fleet_compliance_pct"],
        "corridor_benchmarks": res["corridor_summary"].to_dict(orient="records") if not res["corridor_summary"].empty else [],
        "carrier_compliance": res["carrier_compliance"].to_dict(orient="records") if not res["carrier_compliance"].empty else [],
        "top_flagged_instances": flagged_preview,
    }

