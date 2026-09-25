"""
SQLite Database Manager for APIx
Handles schema migrations, bulk inserts, and analytical queries.
"""

import os
import sqlite3
from typing import List, Dict, Any, Optional
import pandas as pd
from apix.config import DB_PATH

class DatabaseManager:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self.init_schema()

    def get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA synchronous=NORMAL;")
        return conn

    def init_schema(self):
        """Initializes tables and indexes for high-frequency queries."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # 1. Raw Quotes Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS raw_quotes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source TEXT NOT NULL,
                    carrier_code TEXT NOT NULL,
                    flight_number TEXT NOT NULL,
                    origin TEXT NOT NULL,
                    destination TEXT NOT NULL,
                    departure_date TEXT NOT NULL,
                    departure_time TEXT NOT NULL,
                    advance_days INTEGER NOT NULL,
                    fare_class TEXT DEFAULT 'Economy',
                    quoted_fare REAL NOT NULL,
                    scraped_at TEXT NOT NULL,
                    is_sold_out INTEGER DEFAULT 0,
                    raw_payload TEXT
                );
            """)

            # 2. Clean Quotes Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS clean_quotes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source TEXT NOT NULL,
                    carrier_code TEXT NOT NULL,
                    carrier_name TEXT NOT NULL,
                    flight_number TEXT NOT NULL,
                    origin TEXT NOT NULL,
                    destination TEXT NOT NULL,
                    canonical_route TEXT NOT NULL,
                    departure_date TEXT NOT NULL,
                    advance_days INTEGER NOT NULL,
                    quote_date TEXT NOT NULL,
                    fare_class TEXT DEFAULT 'Economy',
                    base_fare REAL NOT NULL,
                    psf REAL NOT NULL,
                    udf REAL NOT NULL,
                    gst REAL NOT NULL,
                    convenience_fee REAL NOT NULL,
                    total_fare REAL NOT NULL,
                    is_outlier INTEGER DEFAULT 0,
                    is_sold_out INTEGER DEFAULT 0,
                    imputed INTEGER DEFAULT 0,
                    created_at TEXT NOT NULL
                );
            """)

            # 3. Route Weights Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS route_weights (
                    route TEXT PRIMARY KEY,
                    origin TEXT NOT NULL,
                    destination TEXT NOT NULL,
                    annual_pax REAL NOT NULL,
                    weight REAL NOT NULL,
                    last_updated TEXT NOT NULL
                );
            """)

            # 4. Daily Index Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS daily_index (
                    date TEXT PRIMARY KEY,
                    two_tier_index REAL DEFAULT 100.0,
                    laspeyres_index REAL NOT NULL,
                    paasche_index REAL NOT NULL,
                    fisher_index REAL NOT NULL,
                    jevons_index REAL NOT NULL,
                    average_fare REAL NOT NULL,
                    route_indices_json TEXT,
                    window_indices_json TEXT,
                    sample_size INTEGER NOT NULL
                );
            """)

            # Migration: ensure two_tier_index column exists
            cursor.execute("PRAGMA table_info(daily_index)")
            existing_cols = [c[1] for c in cursor.fetchall()]
            if existing_cols and "two_tier_index" not in existing_cols:
                cursor.execute("ALTER TABLE daily_index ADD COLUMN two_tier_index REAL DEFAULT 100.0")

            # 5. DGCA Benchmark Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS dgca_benchmarks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    month TEXT NOT NULL,
                    route TEXT NOT NULL,
                    dgca_avg_fare REAL NOT NULL,
                    apix_avg_fare REAL NOT NULL,
                    tracking_diff_pct REAL NOT NULL
                );
            """)

            # Fast query indexes
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_clean_quote_date ON clean_quotes(quote_date);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_clean_route ON clean_quotes(canonical_route);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_clean_advance ON clean_quotes(advance_days);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_clean_carrier ON clean_quotes(carrier_code);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_daily_index_date ON daily_index(date);")
            
            conn.commit()

    def insert_raw_quotes(self, quotes: List[Dict[str, Any]]) -> int:
        if not quotes:
            return 0
        with self.get_connection() as conn:
            cursor = conn.cursor()
            query = """
                INSERT INTO raw_quotes (
                    source, carrier_code, flight_number, origin, destination,
                    departure_date, departure_time, advance_days, fare_class,
                    quoted_fare, scraped_at, is_sold_out, raw_payload
                ) VALUES (
                    :source, :carrier_code, :flight_number, :origin, :destination,
                    :departure_date, :departure_time, :advance_days, :fare_class,
                    :quoted_fare, :scraped_at, :is_sold_out, :raw_payload
                )
            """
            cursor.executemany(query, quotes)
            conn.commit()
            return len(quotes)

    def insert_clean_quotes(self, quotes: List[Dict[str, Any]]) -> int:
        if not quotes:
            return 0
        with self.get_connection() as conn:
            cursor = conn.cursor()
            query = """
                INSERT INTO clean_quotes (
                    source, carrier_code, carrier_name, flight_number, origin, destination,
                    canonical_route, departure_date, advance_days, quote_date, fare_class,
                    base_fare, psf, udf, gst, convenience_fee, total_fare,
                    is_outlier, is_sold_out, imputed, created_at
                ) VALUES (
                    :source, :carrier_code, :carrier_name, :flight_number, :origin, :destination,
                    :canonical_route, :departure_date, :advance_days, :quote_date, :fare_class,
                    :base_fare, :psf, :udf, :gst, :convenience_fee, :total_fare,
                    :is_outlier, :is_sold_out, :imputed, :created_at
                )
            """
            cursor.executemany(query, quotes)
            conn.commit()
            return len(quotes)

    def save_route_weights(self, weights_df: pd.DataFrame):
        with self.get_connection() as conn:
            weights_df.to_sql("route_weights", conn, if_exists="replace", index=False)

    def get_route_weights(self) -> pd.DataFrame:
        with self.get_connection() as conn:
            return pd.read_sql_query("SELECT * FROM route_weights ORDER BY weight DESC", conn)

    def save_daily_index(self, index_record: Dict[str, Any]):
        rec = dict(index_record)
        rec.setdefault("two_tier_index", rec.get("laspeyres_index", 100.0))
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO daily_index (
                    date, two_tier_index, laspeyres_index, paasche_index, fisher_index,
                    jevons_index, average_fare, route_indices_json,
                    window_indices_json, sample_size
                ) VALUES (
                    :date, :two_tier_index, :laspeyres_index, :paasche_index, :fisher_index,
                    :jevons_index, :average_fare, :route_indices_json,
                    :window_indices_json, :sample_size
                )
            """, rec)
            conn.commit()

    def get_daily_indices(self, start_date: Optional[str] = None, end_date: Optional[str] = None) -> pd.DataFrame:
        query = "SELECT * FROM daily_index"
        params = []
        if start_date and end_date:
            query += " WHERE date BETWEEN ? AND ?"
            params = [start_date, end_date]
        elif start_date:
            query += " WHERE date >= ?"
            params = [start_date]
        query += " ORDER BY date ASC"
        
        with self.get_connection() as conn:
            return pd.read_sql_query(query, conn, params=params)

    def get_clean_quotes_df(self, quote_date: Optional[str] = None, route: Optional[str] = None, carrier: Optional[str] = None) -> pd.DataFrame:
        query = "SELECT * FROM clean_quotes WHERE is_outlier = 0"
        params = []
        if quote_date:
            query += " AND quote_date = ?"
            params.append(quote_date)
        if route:
            query += " AND canonical_route = ?"
            params.append(route)
        if carrier:
            query += " AND carrier_code = ?"
            params.append(carrier)
        with self.get_connection() as conn:
            return pd.read_sql_query(query, conn, params=params)
