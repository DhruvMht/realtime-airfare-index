import pytest
import pandas as pd
from apix.index.watchdog import DGCAWatchdogManager

def test_watchdog_empty():
    watchdog = DGCAWatchdogManager()
    res = watchdog.analyze_quotes(pd.DataFrame())
    assert res["total_flights"] == 0
    assert res["total_breaches"] == 0
    assert res["statutory_cap_breaches"] == 0
    assert res["predatory_surges"] == 0
    assert res["fleet_compliance_pct"] == 100.0

def test_watchdog_breach_detection():
    watchdog = DGCAWatchdogManager()
    quotes = [
        # CCU-DEL cap is 16,000, median is 6,200 (19,500 > 16,000 => Level 3 Cap Breach)
        {"origin": "CCU", "destination": "DEL", "carrier_name": "IndiGo", "flight_number": "6E-204", "total_fare": 19500.0, "departure_date": "2026-10-20", "advance_days": 1},
        # BLR-HYD cap is 8,000, median is 3,200 (3,200 <= 8,000, surge = 1.0 => Level 0 Compliant)
        {"origin": "BLR", "destination": "HYD", "carrier_name": "Air India", "flight_number": "AI-502", "total_fare": 3200.0, "departure_date": "2026-10-20", "advance_days": 15},
    ]
    df = pd.DataFrame(quotes)
    res = watchdog.analyze_quotes(df)
    assert res["total_flights"] == 2
    assert res["total_breaches"] == 1
    assert res["statutory_cap_breaches"] == 1
    assert res["fleet_compliance_pct"] == 50.0
    assert len(res["flagged_instances"]) == 1
    flagged = res["flagged_instances"].iloc[0]
    assert flagged["flight_number"] == "6E-204"
    assert flagged["alert_tier"] == "Level 3: Cap Breach"
    assert "Statutory Cap" in flagged["violation_type"]

def test_watchdog_tiered_classification():
    watchdog = DGCAWatchdogManager()
    # BLR-BOM: Cap 12,000, Median 4,500
    quotes = [
        # Flight 1: 14,000 > 12,000 -> Level 3 (Hard Cap Breach)
        {"origin": "BLR", "destination": "BOM", "carrier_name": "IndiGo", "flight_number": "6E-101", "total_fare": 14000.0, "departure_date": "2026-10-20", "advance_days": 1},
        # Flight 2: 11,500 <= 12,000, surge = 11,500 / 4,500 = 2.56x >= 2.5x -> Level 2 (Predatory Surge)
        {"origin": "BLR", "destination": "BOM", "carrier_name": "Akasa", "flight_number": "QP-102", "total_fare": 11500.0, "departure_date": "2026-10-20", "advance_days": 2},
        # Flight 3: 9,500 <= 12,000, surge = 9,500 / 4,500 = 2.11x (2.0x <= s < 2.5x) -> Level 1 (Elevated Vigil)
        {"origin": "BLR", "destination": "BOM", "carrier_name": "SpiceJet", "flight_number": "SG-103", "total_fare": 9500.0, "departure_date": "2026-10-20", "advance_days": 7},
        # Flight 4: 4,500, surge = 1.0x -> Level 0 (Compliant)
        {"origin": "BLR", "destination": "BOM", "carrier_name": "Air India", "flight_number": "AI-104", "total_fare": 4500.0, "departure_date": "2026-10-20", "advance_days": 30},
    ]
    df = pd.DataFrame(quotes)
    res = watchdog.analyze_quotes(df)
    assert res["total_flights"] == 4
    assert res["statutory_cap_breaches"] == 1
    assert res["predatory_surges"] == 1
    assert res["elevated_surges"] == 1
    
    evaluated = res["all_evaluated"]
    f1 = evaluated[evaluated["flight_number"] == "6E-101"].iloc[0]
    assert f1["alert_tier"] == "Level 3: Cap Breach"
    f2 = evaluated[evaluated["flight_number"] == "QP-102"].iloc[0]
    assert f2["alert_tier"] == "Level 2: Predatory"
    f3 = evaluated[evaluated["flight_number"] == "SG-103"].iloc[0]
    assert f3["alert_tier"] == "Level 1: Elevated"
    f4 = evaluated[evaluated["flight_number"] == "AI-104"].iloc[0]
    assert f4["alert_tier"] == "Level 0: Normal"

def test_watchdog_corridor_summary():
    watchdog = DGCAWatchdogManager()
    ceilings = watchdog.get_corridor_ceilings()
    assert len(ceilings) == 15
    assert "BOM-DEL" in ceilings
    assert "CCU-DEL" in ceilings
    assert "BLR-HYD" in ceilings
    assert "DEL-GOI" in ceilings
    assert "DEL-SXR" in ceilings
