"""
Tests for Data Cleaning, Outlier Detection, and Fare Decomposition
"""

import pytest
from apix.pipeline.decomposer import FareDecomposer
from apix.pipeline.cleaner import DataCleaningPipeline

def test_fare_decomposition_identity():
    """Verify that Base + PSF + UDF + GST + Convenience Fee equals Total Fare."""
    quote = {
        "quoted_fare": 6500.0,
        "origin": "DEL",
        "source": "IndiGo",
    }
    decomp = FareDecomposer.decompose(quote)
    calculated_sum = (
        decomp["base_fare"] + decomp["psf"] + decomp["udf"] +
        decomp["gst"] + decomp["convenience_fee"]
    )
    assert abs(calculated_sum - decomp["total_fare"]) < 0.05
    assert decomp["base_fare"] > 0
    assert decomp["gst"] == pytest.approx(round(decomp["base_fare"] * 0.05, 2), abs=0.02)

def test_ota_convenience_fee_captured():
    """Verify convenience fee is tracked for OTAs but zero for direct airline."""
    indigo_decomp = FareDecomposer.decompose({"quoted_fare": 5000, "origin": "DEL", "source": "IndiGo"})
    mmt_decomp = FareDecomposer.decompose({"quoted_fare": 5000, "origin": "DEL", "source": "MakeMyTrip"})
    assert indigo_decomp["convenience_fee"] == 0.0
    assert mmt_decomp["convenience_fee"] == 349.0

def test_data_cleaner_deduplication():
    """Verify duplicate quotes for identical flight on same route/window are removed."""
    cleaner = DataCleaningPipeline()
    sample_quotes = [
        {
            "source": "IndiGo",
            "carrier_code": "6E",
            "flight_number": "6E-205",
            "origin": "DEL",
            "destination": "BOM",
            "departure_date": "2026-09-10",
            "departure_time": "06:15",
            "advance_days": 7,
            "fare_class": "Economy",
            "quoted_fare": 5200.0,
            "scraped_at": "2026-09-03T08:00:00",
            "is_sold_out": 0,
            "raw_payload": None,
        },
        {
            "source": "MakeMyTrip",
            "carrier_code": "6E",
            "flight_number": "6E-205",
            "origin": "DEL",
            "destination": "BOM",
            "departure_date": "2026-09-10",
            "departure_time": "06:15",
            "advance_days": 7,
            "fare_class": "Economy",
            "quoted_fare": 5350.0,
            "scraped_at": "2026-09-03T08:05:00",
            "is_sold_out": 0,
            "raw_payload": None,
        },
    ]
    cleaned = cleaner.clean_quotes(sample_quotes, quote_date_str="2026-09-03")
    assert len(cleaned) == 1
    assert cleaned[0]["flight_number"] == "6E-205"

def test_sold_out_not_zero_filled():
    """Verify sold-out flights are not zero-filled, but flagged and imputed."""
    cleaner = DataCleaningPipeline()
    quotes = [
        {"source": "IndiGo", "carrier_code": "6E", "flight_number": f"6E-{i}", "origin": "DEL", "destination": "BOM",
         "departure_date": "2026-09-04", "departure_time": "08:00", "advance_days": 1, "fare_class": "Economy",
         "quoted_fare": 9000.0 + i * 200, "scraped_at": "2026-09-03T08:00:00", "is_sold_out": 0, "raw_payload": None}
        for i in range(5)
    ]
    # Add a sold out flight
    quotes.append({
        "source": "IndiGo", "carrier_code": "6E", "flight_number": "6E-999", "origin": "DEL", "destination": "BOM",
        "departure_date": "2026-09-04", "departure_time": "09:00", "advance_days": 1, "fare_class": "Economy",
        "quoted_fare": 0.0, "scraped_at": "2026-09-03T08:00:00", "is_sold_out": 1, "raw_payload": None
    })
    cleaned = cleaner.clean_quotes(quotes, quote_date_str="2026-09-03")
    sold_out_clean = [q for q in cleaned if q["is_sold_out"] == 1]
    assert len(sold_out_clean) == 1
    assert sold_out_clean[0]["total_fare"] > 8000.0  # Imputed with positive peer yield
    assert sold_out_clean[0]["imputed"] == 1
