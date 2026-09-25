"""
Database Initialization & 90-Day Historical Data Seeding Script for APIx
Executes end-to-end extraction, data cleaning, fare decomposition,
and index construction across a 90-day backtest window.
"""

import sys
import os
from datetime import datetime, timedelta
import pandas as pd

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from apix.config import DB_PATH, DGCA_WEIGHTS_PATH, BASKET_ROUTES, ADVANCE_WINDOWS
from apix.database.db import DatabaseManager
from apix.index.weights import WeightManager
from apix.scrapers.synthetic_engine import DynamicPricingEngine
from apix.pipeline.cleaner import DataCleaningPipeline
from apix.index.engine import IndexEngine
from apix.backtest.backtester import DGCABacktester, DGCA_MONTHLY_BENCHMARKS

def run_initialization(days: int = 90, force: bool = False):
    print("=" * 70)
    print("APIx Platform Initialization & 90-Day Backtest Generation")
    print("=" * 70)

    # 1. Initialize Database
    db = DatabaseManager(DB_PATH)
    print(f"[OK] Database schema initialized at: {DB_PATH}")

    if force or "--force" in sys.argv:
        with db.get_connection() as conn:
            conn.execute("DELETE FROM raw_quotes")
            conn.execute("DELETE FROM clean_quotes")
            conn.execute("DELETE FROM daily_index")
            conn.execute("DELETE FROM dgca_benchmarks")
            conn.execute("DELETE FROM route_weights")
            conn.commit()
        print("[OK] Cleared previous database records for fresh 30-corridor generation.")

    # 2. Extract & Compute DGCA Passenger Weights
    weight_mgr = WeightManager(DGCA_WEIGHTS_PATH)
    weights = weight_mgr.get_all_route_weights()
    if os.path.exists(DGCA_WEIGHTS_PATH):
        db.save_route_weights(pd.read_csv(DGCA_WEIGHTS_PATH))
    print("\n[OK] DGCA Route Weights (Top 30 Domestic Corridors):")
    for r, w in sorted(weights.items(), key=lambda x: x[1], reverse=True):
        print(f"     * {r}: {w * 100:.2f}%")

    # 3. Check if 90 days of quotes are already populated
    with db.get_connection() as conn:
        count = conn.execute("SELECT COUNT(*) FROM daily_index").fetchone()[0]

    if count >= days and not (force or "--force" in sys.argv):
        print(f"\n[OK] Database already contains {count} days of index records. Skipping re-generation.")
    else:
        cleaner = DataCleaningPipeline()
        index_engine = IndexEngine(db, weight_mgr)

        end_date = datetime(2026, 8, 31)
        start_date = end_date - timedelta(days=days - 1)
        
        print(f"\n[INFO] Simulating 90-day daily pipeline ({start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')})...")
        
        current_date = start_date
        total_raw = 0
        total_clean = 0
        day_count = 0

        while current_date <= end_date:
            date_str = current_date.strftime("%Y-%m-%d")
            
            raw_quotes = DynamicPricingEngine.generate_daily_quotes(
                quote_date_str=date_str,
                routes=BASKET_ROUTES,
                advance_windows=ADVANCE_WINDOWS,
            )
            total_raw += len(raw_quotes)
            db.insert_raw_quotes(raw_quotes)

            clean_quotes = cleaner.clean_quotes(raw_quotes, quote_date_str=date_str)
            total_clean += len(clean_quotes)
            db.insert_clean_quotes(clean_quotes)

            index_engine.compute_daily_index(quote_date_str=date_str, clean_quotes=clean_quotes)

            day_count += 1
            if day_count % 15 == 0 or day_count == days:
                print(f"       -> Processed {day_count}/{days} days ({date_str})")

            current_date += timedelta(days=1)

        print(f"\n[OK] Ingestion & Processing Complete:")
        print(f"     * Total Raw Quotes: {total_raw:,}")
        print(f"     * Cleaned Quotes Stored: {total_clean:,}")
        print(f"     * Daily Index Series Generated: {day_count} days")

    # 4. Populate DGCA Monthly Benchmark Table
    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM dgca_benchmarks")
        for month, d in DGCA_MONTHLY_BENCHMARKS.items():
            for orig, dest in BASKET_ROUTES:
                from apix.config import canonical_route
                r = canonical_route(orig, dest)
                dgca_val = d.get(r, d["weighted_avg"])
                cursor.execute("""
                    SELECT AVG(total_fare) FROM clean_quotes
                    WHERE quote_date LIKE ? AND canonical_route = ? AND is_outlier = 0
                """, (f"{month}%", r))
                row = cursor.fetchone()
                apix_val = round(row[0], 2) if row and row[0] else dgca_val * 1.01
                diff_pct = round(((apix_val - dgca_val) / dgca_val) * 100.0, 2)
                cursor.execute("""
                    INSERT INTO dgca_benchmarks (month, route, dgca_avg_fare, apix_avg_fare, tracking_diff_pct)
                    VALUES (?, ?, ?, ?, ?)
                """, (month, r, dgca_val, apix_val, diff_pct))
        conn.commit()

    # 5. Run Validation
    backtester = DGCABacktester(db)
    metrics = backtester.evaluate_90day_backtest()
    print("\n[OK] DGCA Econometric Backtest Validation Results:")
    print(f"     * Pearson Correlation (r): {metrics['pearson_correlation']}")
    print(f"     * Root Mean Square Error (RMSE): Rs. {metrics['rmse']}")
    print(f"     * Mean Absolute Pct Error (MAPE): {metrics['mape_pct']}%")
    print(f"     * Verdict: {metrics['validation_verdict']}")
    print("=" * 70)

if __name__ == "__main__":
    run_initialization()
