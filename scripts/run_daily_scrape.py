"""
Daily Scheduled Scraping & Index Pipeline Execution CLI for APIx
Can be run via cron / Windows Task Scheduler / Airflow DAG.
"""

import sys
import os
import argparse
from datetime import datetime, timedelta

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from apix.database.db import DatabaseManager
from apix.index.weights import WeightManager
from apix.scrapers.scheduler import ScraperScheduler
from apix.pipeline.cleaner import DataCleaningPipeline
from apix.index.engine import IndexEngine

def main():
    parser = argparse.ArgumentParser(description="APIx Daily Airfare Scraping & Index Ingestion")
    parser.add_argument("--date", type=str, default=None, help="Target date YYYY-MM-DD (defaults to today in IST)")
    parser.add_argument("--epoch", type=str, default=None, help="Epoch: 08:00 IST, 14:00 IST, or 20:00 IST")
    args = parser.parse_args()

    # Determine IST date and observation epoch
    ist_now = datetime.utcnow() + timedelta(hours=5, minutes=30)
    target_date = args.date or ist_now.strftime("%Y-%m-%d")

    if args.epoch:
        target_epoch = args.epoch
    else:
        hour = ist_now.hour
        if hour < 11:
            target_epoch = "08:00 IST"
        elif hour < 17:
            target_epoch = "14:00 IST"
        else:
            target_epoch = "20:00 IST"

    print(f"[*] Starting APIx Execution for Date: {target_date} [Epoch: {target_epoch}]")

    db = DatabaseManager()
    weight_mgr = WeightManager()
    scheduler = ScraperScheduler(db)
    cleaner = DataCleaningPipeline()
    index_engine = IndexEngine(db, weight_mgr)

    # 1. Scrape
    scrape_res = scheduler.run_daily_scrape(quote_date_str=target_date, epoch=target_epoch)
    print(f"[+] Scraped {scrape_res['quotes_scraped']} raw quotes across {scrape_res['routes_covered']} routes.")

    # 2. Clean & Decompose
    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM raw_quotes WHERE scraped_at LIKE ?", (f"{target_date}%",))
        raw_rows = [dict(r) for r in cursor.fetchall()]

    clean_quotes = cleaner.clean_quotes(raw_rows, quote_date_str=target_date)
    inserted_clean = db.insert_clean_quotes(clean_quotes)
    print(f"[+] Cleaned & decomposed {inserted_clean} valid quotes.")

    # 3. Calculate Index
    index_res = index_engine.compute_daily_index(quote_date_str=target_date, clean_quotes=clean_quotes)
    print(f"[+] Computed APIx Index for {target_date}:")
    print(f"    * Laspeyres Index : {index_res['laspeyres_index']}")
    print(f"    * Fisher Ideal    : {index_res['fisher_index']}")
    print(f"    * Jevons Geometric: {index_res['jevons_index']}")
    print(f"    * Average Airfare : Rs. {index_res['average_fare']}")
    print(f"[OK] Daily pipeline execution completed successfully.")

if __name__ == "__main__":
    main()
