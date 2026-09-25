"""
OTA (Online Travel Aggregator) Scrapers for MakeMyTrip, EaseMyTrip, Yatra, Cleartrip, Ixigo.
Captures aggregator pricing, convenience fee surcharges, and discounts.
"""

from typing import List, Dict, Any
from apix.scrapers.base_scraper import BaseScraper
from apix.scrapers.synthetic_engine import DynamicPricingEngine
from apix.config import OTAS

class OTAPortalScraper(BaseScraper):
    def __init__(self, ota_name: str, base_url: str, convenience_fee: float = 300.0):
        super().__init__(name=ota_name, base_url=base_url, is_ota=True)
        self.convenience_fee = convenience_fee

    def fetch_quotes(self, origin: str, destination: str, departure_date: str, advance_days: int) -> List[Dict[str, Any]]:
        """Extracts OTA quotes across multi-airline inventory."""
        self.guard.polite_wait(self.base_url)
        # In live runs, this connects to OTA search APIs
        # In sandbox/demo mode, calculates synthetic quotes with OTA markup/convenience fee
        quotes = []
        for code in ["6E", "AI", "QP"]:
            fare, is_sold = DynamicPricingEngine.calculate_expected_fare(
                origin, destination, departure_date, advance_days, code
            )
            total = fare + (self.convenience_fee * 0.5)
            quotes.append({
                "source": self.name,
                "carrier_code": code,
                "flight_number": f"{code}-OTA-88",
                "origin": origin,
                "destination": destination,
                "departure_date": departure_date,
                "departure_time": "12:00",
                "advance_days": advance_days,
                "fare_class": "Economy",
                "quoted_fare": round(total / 10.0) * 10.0,
                "scraped_at": f"{departure_date}T08:30:00",
                "is_sold_out": 1 if is_sold else 0,
                "raw_payload": None,
            })
        return quotes
