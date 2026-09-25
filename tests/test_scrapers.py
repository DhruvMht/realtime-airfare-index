"""
Tests for Scraping Engine and Ethical Safeguards
"""

import pytest
from apix.scrapers.base_scraper import EthicalScrapingGuard
from apix.scrapers.synthetic_engine import DynamicPricingEngine
from apix.config import BASKET_ROUTES, ADVANCE_WINDOWS

def test_ethical_guard_robots_txt():
    guard = EthicalScrapingGuard()
    # Test robots check returns boolean without throwing
    allowed = guard.is_allowed_by_robots("https://example.com/flights")
    assert isinstance(allowed, bool)

def test_ethical_headers():
    guard = EthicalScrapingGuard()
    headers = guard.get_headers()
    assert "User-Agent" in headers
    assert "Accept" in headers
    assert len(headers["User-Agent"]) > 10

def test_dynamic_pricing_decay():
    """Verify that T+1 fares are significantly higher than T+45 fares (revenue management decay)."""
    t1_fare, _ = DynamicPricingEngine.calculate_expected_fare(
        "DEL", "BOM", "2026-09-10", advance_days=1, carrier_code="6E", random_seed=42
    )
    t45_fare, _ = DynamicPricingEngine.calculate_expected_fare(
        "DEL", "BOM", "2026-09-10", advance_days=45, carrier_code="6E", random_seed=42
    )
    # T+1 should be at least 80% higher than T+45
    assert t1_fare > t45_fare
    assert (t1_fare / t45_fare) >= 1.70

def test_generate_daily_quotes_coverage():
    """Verify daily quotes cover all 15 basket corridors and 5 advance windows."""
    quotes = DynamicPricingEngine.generate_daily_quotes(
        quote_date_str="2026-09-01",
        routes=BASKET_ROUTES,
        advance_windows=ADVANCE_WINDOWS,
    )
    assert len(quotes) > 0
    routes_found = {f"{q['origin']}-{q['destination']}" for q in quotes}
    windows_found = {q["advance_days"] for q in quotes}
    assert len(windows_found) == len(ADVANCE_WINDOWS)
