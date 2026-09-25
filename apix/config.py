"""
APIx Configuration
Defines representative DGCA routes, booking windows, airport coordinates,
tax structures, and econometric parameters for the Airfare Price Index.
"""

from typing import Dict, List, Tuple, Any

# ---- Core Basket Routes (Top 15 Indian Domestic Corridors · ~38.9M Annual Passenger Volume) ----
BASKET_ROUTES: List[Tuple[str, str]] = [
    ("DEL", "BOM"),  # Delhi - Mumbai (Golden corridor, #1 in India · 6.66M Pax)
    ("DEL", "BLR"),  # Delhi - Bengaluru (Tech & Business, #2 · 4.75M Pax)
    ("BOM", "BLR"),  # Mumbai - Bengaluru (Commercial, #3 · 4.03M Pax)
    ("DEL", "CCU"),  # Delhi - Kolkata (North-East gateway, #4 · 2.83M Pax)
    ("DEL", "MAA"),  # Delhi - Chennai (South-North trunk, #5 · 2.34M Pax)
    ("BLR", "HYD"),  # Bengaluru - Hyderabad (Deccan tech, #6 · 2.29M Pax)
    ("DEL", "GOI"),  # Delhi - Goa (Tourism & Leisure, #7 · 2.08M Pax)
    ("AMD", "DEL"),  # Ahmedabad - Delhi (Western industrial, #8 · 1.98M Pax)
    ("DEL", "HYD"),  # Delhi - Hyderabad (Administrative & IT, #9 · 1.91M Pax)
    ("BOM", "GOI"),  # Mumbai - Goa (High-frequency leisure, #10 · 1.80M Pax)
    ("BOM", "MAA"),  # Mumbai - Chennai (Commercial coastal, #11 · 1.78M Pax)
    ("DEL", "SXR"),  # Delhi - Srinagar (Northern leisure/strategic, #12 · 1.69M Pax)
    ("BOM", "COK"),  # Mumbai - Kochi (Kerala coastal hub, #13 · 1.64M Pax)
    ("BOM", "CCU"),  # Mumbai - Kolkata (West-East trunk, #14 · 1.61M Pax)
    ("BLR", "CCU"),  # Bengaluru - Kolkata (Tech-East migration, #15 · 1.56M Pax)
]

# Canonical undirected route representation
def canonical_route(orig: str, dest: str) -> str:
    """Returns canonical route string e.g. 'BOM-DEL' sorted alphabetically."""
    return "-".join(sorted([orig.upper(), dest.upper()]))

# ---- Advance Purchase Windows (Days before departure) ----
ADVANCE_WINDOWS: List[int] = [1, 7, 15, 30, 45]
WINDOW_LABELS: Dict[int, str] = {
    1: "T+1 (Last Minute)",
    7: "T+7 (Short Term)",
    15: "T+15 (Medium Term)",
    30: "T+30 (Standard Advance)",
    45: "T+45 (Early Bird)",
}

# Empirical weights for advance booking distribution (DGCA / IATA booking curve)
ADVANCE_WINDOW_WEIGHTS: Dict[int, float] = {
    1: 0.10,   # ~10% corporate/urgent bookings
    7: 0.25,   # ~25% short-lead leisure/business
    15: 0.30,  # ~30% peak booking window
    30: 0.25,  # ~25% planned travel
    45: 0.10,  # ~10% holiday/advance bookings
}

# ---- Monitored Airlines & OTAs ----
AIRLINES: List[Dict[str, str]] = [
    {"code": "6E", "name": "IndiGo", "type": "LCC", "market_share": 0.62},
    {"code": "AI", "name": "Air India", "type": "FSC", "market_share": 0.14},
    {"code": "IX", "name": "Air India Express", "type": "LCC", "market_share": 0.08},
    {"code": "QP", "name": "Akasa Air", "type": "LCC", "market_share": 0.05},
    {"code": "SG", "name": "SpiceJet", "type": "LCC", "market_share": 0.04},
]

OTAS: List[Dict[str, str]] = [
    {"name": "MakeMyTrip", "convenience_fee": 349.0},
    {"name": "EaseMyTrip", "convenience_fee": 0.0},  # EMT zero convenience fee USP
    {"name": "Yatra", "convenience_fee": 399.0},
    {"name": "Cleartrip", "convenience_fee": 299.0},
    {"name": "Ixigo", "convenience_fee": 249.0},
]

# ---- Airport Geo-Coordinates & Details ----
AIRPORT_DATA: Dict[str, Dict] = {
    "DEL": {
        "name": "Indira Gandhi International Airport",
        "city": "Delhi",
        "lat": 28.5562,
        "lon": 77.1000,
        "udf_rate": 380.0,
        "psf_rate": 91.0,
    },
    "BOM": {
        "name": "Chhatrapati Shivaji Maharaj International Airport",
        "city": "Mumbai",
        "lat": 19.0896,
        "lon": 72.8656,
        "udf_rate": 425.0,
        "psf_rate": 110.0,
    },
    "BLR": {
        "name": "Kempegowda International Airport",
        "city": "Bengaluru",
        "lat": 13.1986,
        "lon": 77.7066,
        "udf_rate": 480.0,
        "psf_rate": 105.0,
    },
    "CCU": {
        "name": "Netaji Subhash Chandra Bose International Airport",
        "city": "Kolkata",
        "lat": 22.6547,
        "lon": 88.4467,
        "udf_rate": 350.0,
        "psf_rate": 91.0,
    },
    "HYD": {
        "name": "Rajiv Gandhi International Airport",
        "city": "Hyderabad",
        "lat": 17.2403,
        "lon": 78.4294,
        "udf_rate": 410.0,
        "psf_rate": 100.0,
    },
    "MAA": {
        "name": "Chennai International Airport",
        "city": "Chennai",
        "lat": 12.9941,
        "lon": 80.1709,
        "udf_rate": 330.0,
        "psf_rate": 91.0,
    },
    "AMD": {
        "name": "Sardar Vallabhbhai Patel International Airport",
        "city": "Ahmedabad",
        "lat": 23.0772,
        "lon": 72.6347,
        "udf_rate": 340.0,
        "psf_rate": 91.0,
    },
    "GOI": {
        "name": "Goa Dabolim / MOPA International Airport",
        "city": "Goa",
        "lat": 15.3808,
        "lon": 73.8314,
        "udf_rate": 360.0,
        "psf_rate": 91.0,
    },
    "SXR": {
        "name": "Sheikh ul-Alam International Airport",
        "city": "Srinagar",
        "lat": 33.9871,
        "lon": 74.7741,
        "udf_rate": 320.0,
        "psf_rate": 91.0,
    },
    "GAU": {
        "name": "Lokpriya Gopinath Bordoloi International Airport",
        "city": "Guwahati",
        "lat": 26.1061,
        "lon": 91.5859,
        "udf_rate": 310.0,
        "psf_rate": 91.0,
    },
    "COK": {
        "name": "Cochin International Airport",
        "city": "Kochi",
        "lat": 10.1518,
        "lon": 76.3930,
        "udf_rate": 370.0,
        "psf_rate": 91.0,
    },
    "PNQ": {
        "name": "Pune International Airport",
        "city": "Pune",
        "lat": 18.5822,
        "lon": 73.9197,
        "udf_rate": 330.0,
        "psf_rate": 91.0,
    },
    "LKO": {
        "name": "Chaudhary Charan Singh International Airport",
        "city": "Lucknow",
        "lat": 26.7606,
        "lon": 80.8893,
        "udf_rate": 340.0,
        "psf_rate": 91.0,
    },
    "PAT": {
        "name": "Jayprakash Narayan Airport",
        "city": "Patna",
        "lat": 25.5913,
        "lon": 85.0880,
        "udf_rate": 310.0,
        "psf_rate": 91.0,
    },
    "BBI": {
        "name": "Biju Patnaik International Airport",
        "city": "Bhubaneswar",
        "lat": 20.2444,
        "lon": 85.8178,
        "udf_rate": 320.0,
        "psf_rate": 91.0,
    },
    "IXC": {
        "name": "Shaheed Bhagat Singh International Airport",
        "city": "Chandigarh",
        "lat": 30.6735,
        "lon": 76.7885,
        "udf_rate": 300.0,
        "psf_rate": 91.0,
    },
    "JAI": {
        "name": "Jaipur International Airport",
        "city": "Jaipur",
        "lat": 26.8242,
        "lon": 75.8122,
        "udf_rate": 310.0,
        "psf_rate": 91.0,
    },
    "VNS": {
        "name": "Lal Bahadur Shastri International Airport",
        "city": "Varanasi",
        "lat": 25.4523,
        "lon": 82.8593,
        "udf_rate": 310.0,
        "psf_rate": 91.0,
    },
}

# ---- Tax & Outlier Rules ----
ECONOMY_GST_RATE: float = 0.05       # 5% GST on domestic economy air travel
BUSINESS_GST_RATE: float = 0.12      # 12% GST on domestic business air travel
OUTLIER_IQR_MULTIPLIER: float = 1.75 # Tukey multiplier for route-window outlier filter
BASE_INDEX_VALUE: float = 100.0      # Base index level P_0
DB_PATH: str = "data/apix.db"
DGCA_WEIGHTS_PATH: str = "data/dgca_route_weights.csv"

# ---- DGCA Stage-Length Statutory Price Ceilings (Rule 135 / Order AV.29017/26/2020-DT) ----
DGCA_CORRIDOR_CEILINGS: Dict[str, Dict[str, Any]] = {
    "AMD-BLR": {
        "distance_km": 1230,
        "flight_duration_min": 125,
        "band": "Band D (1000-1300 km)",
        "advisory_cap": 15000.0,
        "historical_median": 5200.0,
    },
    "AMD-BOM": {
        "distance_km": 440,
        "flight_duration_min": 65,
        "band": "Band A (<500 km)",
        "advisory_cap": 8000.0,
        "historical_median": 2900.0,
    },
    "AMD-DEL": {
        "distance_km": 775,
        "flight_duration_min": 95,
        "band": "Band C (750-1000 km)",
        "advisory_cap": 12000.0,
        "historical_median": 4200.0,
    },
    "BBI-DEL": {
        "distance_km": 1270,
        "flight_duration_min": 130,
        "band": "Band D (1000-1300 km)",
        "advisory_cap": 15000.0,
        "historical_median": 5300.0,
    },
    "BLR-BOM": {
        "distance_km": 842,
        "flight_duration_min": 100,
        "band": "Band C (750-1000 km)",
        "advisory_cap": 12000.0,
        "historical_median": 4500.0,
    },
    "BLR-CCU": {
        "distance_km": 1560,
        "flight_duration_min": 150,
        "band": "Band E (1300-1600 km)",
        "advisory_cap": 16000.0,
        "historical_median": 6300.0,
    },
    "BLR-DEL": {
        "distance_km": 1740,
        "flight_duration_min": 165,
        "band": "Band F (1600-2100 km)",
        "advisory_cap": 18000.0,
        "historical_median": 7200.0,
    },
    "BLR-HYD": {
        "distance_km": 500,
        "flight_duration_min": 65,
        "band": "Band A (<500 km)",
        "advisory_cap": 8000.0,
        "historical_median": 3200.0,
    },
    "BLR-MAA": {
        "distance_km": 270,
        "flight_duration_min": 50,
        "band": "Band A (<500 km)",
        "advisory_cap": 8000.0,
        "historical_median": 2800.0,
    },
    "BLR-PNQ": {
        "distance_km": 730,
        "flight_duration_min": 90,
        "band": "Band B (500-750 km)",
        "advisory_cap": 10000.0,
        "historical_median": 4100.0,
    },
    "BOM-CCU": {
        "distance_km": 1660,
        "flight_duration_min": 160,
        "band": "Band F (1600-2100 km)",
        "advisory_cap": 18000.0,
        "historical_median": 6800.0,
    },
    "BOM-COK": {
        "distance_km": 1065,
        "flight_duration_min": 115,
        "band": "Band D (1000-1300 km)",
        "advisory_cap": 15000.0,
        "historical_median": 5200.0,
    },
    "BOM-DEL": {
        "distance_km": 1148,
        "flight_duration_min": 130,
        "band": "Band D (1000-1300 km)",
        "advisory_cap": 15000.0,
        "historical_median": 5800.0,
    },
    "BOM-GOI": {
        "distance_km": 435,
        "flight_duration_min": 60,
        "band": "Band A (<500 km)",
        "advisory_cap": 8000.0,
        "historical_median": 3100.0,
    },
    "BOM-HYD": {
        "distance_km": 620,
        "flight_duration_min": 80,
        "band": "Band B (500-750 km)",
        "advisory_cap": 10000.0,
        "historical_median": 3600.0,
    },
    "BOM-JAI": {
        "distance_km": 915,
        "flight_duration_min": 105,
        "band": "Band C (750-1000 km)",
        "advisory_cap": 12000.0,
        "historical_median": 4600.0,
    },
    "BOM-MAA": {
        "distance_km": 1030,
        "flight_duration_min": 115,
        "band": "Band D (1000-1300 km)",
        "advisory_cap": 15000.0,
        "historical_median": 4900.0,
    },
    "CCU-DEL": {
        "distance_km": 1305,
        "flight_duration_min": 140,
        "band": "Band E (1300-1600 km)",
        "advisory_cap": 16000.0,
        "historical_median": 6200.0,
    },
    "CCU-GAU": {
        "distance_km": 510,
        "flight_duration_min": 70,
        "band": "Band B (500-750 km)",
        "advisory_cap": 10000.0,
        "historical_median": 3400.0,
    },
    "COK-DEL": {
        "distance_km": 2050,
        "flight_duration_min": 190,
        "band": "Band F (1600-2100 km)",
        "advisory_cap": 18000.0,
        "historical_median": 7500.0,
    },
    "DEL-GAU": {
        "distance_km": 1460,
        "flight_duration_min": 145,
        "band": "Band E (1300-1600 km)",
        "advisory_cap": 16000.0,
        "historical_median": 6100.0,
    },
    "DEL-GOI": {
        "distance_km": 1510,
        "flight_duration_min": 150,
        "band": "Band E (1300-1600 km)",
        "advisory_cap": 16000.0,
        "historical_median": 6400.0,
    },
    "DEL-HYD": {
        "distance_km": 1260,
        "flight_duration_min": 130,
        "band": "Band D (1000-1300 km)",
        "advisory_cap": 15000.0,
        "historical_median": 5400.0,
    },
    "DEL-IXC": {
        "distance_km": 240,
        "flight_duration_min": 50,
        "band": "Band A (<500 km)",
        "advisory_cap": 8000.0,
        "historical_median": 2600.0,
    },
    "DEL-LKO": {
        "distance_km": 420,
        "flight_duration_min": 60,
        "band": "Band A (<500 km)",
        "advisory_cap": 8000.0,
        "historical_median": 2950.0,
    },
    "DEL-MAA": {
        "distance_km": 1760,
        "flight_duration_min": 170,
        "band": "Band F (1600-2100 km)",
        "advisory_cap": 18000.0,
        "historical_median": 6900.0,
    },
    "DEL-PAT": {
        "distance_km": 850,
        "flight_duration_min": 95,
        "band": "Band C (750-1000 km)",
        "advisory_cap": 12000.0,
        "historical_median": 4400.0,
    },
    "DEL-PNQ": {
        "distance_km": 1170,
        "flight_duration_min": 125,
        "band": "Band D (1000-1300 km)",
        "advisory_cap": 15000.0,
        "historical_median": 5100.0,
    },
    "DEL-SXR": {
        "distance_km": 645,
        "flight_duration_min": 85,
        "band": "Band B (500-750 km)",
        "advisory_cap": 10000.0,
        "historical_median": 4800.0,
    },
    "DEL-VNS": {
        "distance_km": 670,
        "flight_duration_min": 80,
        "band": "Band B (500-750 km)",
        "advisory_cap": 10000.0,
        "historical_median": 3900.0,
    },
}

# Filter DGCA_CORRIDOR_CEILINGS to match active Top 15 basket corridors
DGCA_CORRIDOR_CEILINGS = {
    k: v for k, v in DGCA_CORRIDOR_CEILINGS.items()
    if k in {canonical_route(o, d) for o, d in BASKET_ROUTES}
}

ELEVATED_SURGE_RATIO: float = 2.0   # Level 1 Vigil trigger for dynamic pricing multiples
PREDATORY_SURGE_RATIO: float = 2.5  # Level 2 Predatory Surge trigger (DGCA TMU review threshold)

# 4-Tier DGCA Regulatory Surveillance Classifications
REGULATORY_ALERT_TIERS: Dict[str, Dict[str, Any]] = {
    "LEVEL_0": {
        "level": 0,
        "name": "Compliant",
        "badge": "🟢 Compliant",
        "severity": "NORMAL",
        "description": "Fares within normal yield bounds (surge < 2.0x, fares <= advisory cap).",
    },
    "LEVEL_1": {
        "level": 1,
        "name": "Elevated Vigil",
        "badge": "🟡 Elevated Vigil",
        "severity": "MODERATE",
        "description": "Dynamic pricing elevated (2.0x - 2.5x baseline) or isolated peak ticket.",
    },
    "LEVEL_2": {
        "level": 2,
        "name": "Predatory Surge Alert",
        "badge": "🟠 Predatory Surge Alert",
        "severity": "HIGH",
        "description": "Excessive dynamic surge (>= 2.5x baseline median), TMU review warranted.",
    },
    "LEVEL_3": {
        "level": 3,
        "name": "Statutory Cap Violation",
        "badge": "🔴 Statutory Cap Violation",
        "severity": "CRITICAL",
        "description": "Ticket fare strictly exceeds MoCA distance-band statutory price ceiling.",
    },
}

FESTIVE_WINDOWS: List[Dict[str, Any]] = [
    {
        "name": "Durga Puja & Navratri Rush",
        "dates": "12 Oct 2026 – 22 Oct 2026",
        "peak_days": "Maha Saptami to Vijaya Dashami",
        "affected_corridors": ["CCU-DEL", "BLR-CCU", "BOM-CCU", "CCU-GAU", "DEL-PAT"],
        "description": "High-intensity festive migration into Eastern India (Kolkata & Patna hubs).",
        "surge_risk": "HIGH",
    },
    {
        "name": "Diwali & Chhath Exodus",
        "dates": "01 Nov 2026 – 16 Nov 2026",
        "peak_days": "Dhanteras, Deepavali & Chhath Puja",
        "affected_corridors": ["BOM-DEL", "BLR-DEL", "CCU-DEL", "DEL-PAT", "DEL-LKO", "DEL-VNS", "DEL-HYD"],
        "description": "Peak national holiday travel from corporate hubs to North/East India.",
        "surge_risk": "CRITICAL",
    },
    {
        "name": "Pongal & Sankranti Rush",
        "dates": "10 Jan 2026 – 18 Jan 2026",
        "peak_days": "Bhogi, Surya Pongal & Kanum Pongal",
        "affected_corridors": ["DEL-MAA", "BLR-HYD", "BLR-MAA", "BOM-COK", "COK-DEL", "BOM-MAA"],
        "description": "Southern corridor festive demand across Chennai, Hyderabad, and Kerala.",
        "surge_risk": "HIGH",
    },
    {
        "name": "Year-End & Winter Peak",
        "dates": "20 Dec 2026 – 05 Jan 2027",
        "peak_days": "Christmas to New Year Holiday Window",
        "affected_corridors": ["DEL-GOI", "BOM-GOI", "DEL-SXR", "BOM-DEL", "BLR-BOM"],
        "description": "Peak leisure travel to Goa, Kashmir, and corporate holiday hubs.",
        "surge_risk": "HIGH",
    },
]

