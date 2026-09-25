"""
Database models and Pydantic schemas for APIx
"""

from typing import Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field

class RawQuote(BaseModel):
    id: Optional[int] = None
    source: str
    carrier_code: str
    flight_number: str
    origin: str
    destination: str
    departure_date: str
    departure_time: str
    advance_days: int
    fare_class: str = "Economy"
    quoted_fare: float
    scraped_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    is_sold_out: int = 0
    raw_payload: Optional[str] = None

class CleanQuote(BaseModel):
    id: Optional[int] = None
    source: str
    carrier_code: str
    carrier_name: str
    flight_number: str
    origin: str
    destination: str
    canonical_route: str
    departure_date: str
    advance_days: int
    quote_date: str
    fare_class: str = "Economy"
    base_fare: float
    psf: float
    udf: float
    gst: float
    convenience_fee: float
    total_fare: float
    is_outlier: int = 0
    is_sold_out: int = 0
    imputed: int = 0
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())

class RouteWeight(BaseModel):
    route: str
    origin: str
    destination: str
    annual_pax: float
    weight: float
    last_updated: str

class DailyIndexRecord(BaseModel):
    date: str
    two_tier_index: float = 100.0
    laspeyres_index: float
    paasche_index: float
    fisher_index: float
    jevons_index: float
    average_fare: float
    route_indices_json: str
    window_indices_json: str
    sample_size: int

class DGCABenchmark(BaseModel):
    month: str
    route: str
    dgca_avg_fare: float
    apix_avg_fare: float
    tracking_diff_pct: float
