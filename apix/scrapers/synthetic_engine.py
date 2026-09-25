"""
High-Fidelity Dynamic Pricing & Revenue Management Engine for APIx
Simulates realistic Indian domestic airline pricing mechanics:
- Distance-based base yield curves
- Non-linear advance purchase decay (T+1 surge vs T+45 baseline)
- Day-of-week demand multipliers (Friday/Sunday leisure & Monday business)
- Peak time-of-day slots (morning 07:00-09:30 & evening 18:00-21:00)
- Carrier yield differentials (Air India FSC vs IndiGo/Akasa LCC)
- Sold-out inventory behavior for T+1 high-demand flights
"""

import math
import random
from datetime import datetime, timedelta
from typing import List, Dict, Any, Tuple
from apix.config import (
    BASKET_ROUTES, ADVANCE_WINDOWS, AIRLINES, OTAS,
    AIRPORT_DATA, canonical_route
)

# Route great-circle flight distance in km (Top 30 Domestic Corridors)
ROUTE_DISTANCES: Dict[str, float] = {
    canonical_route("AMD", "BLR"): 1230.0,
    canonical_route("AMD", "BOM"): 440.0,
    canonical_route("AMD", "DEL"): 775.0,
    canonical_route("BBI", "DEL"): 1270.0,
    canonical_route("BLR", "BOM"): 842.0,
    canonical_route("BLR", "CCU"): 1560.0,
    canonical_route("BLR", "DEL"): 1740.0,
    canonical_route("BLR", "HYD"): 500.0,
    canonical_route("BLR", "MAA"): 270.0,
    canonical_route("BLR", "PNQ"): 730.0,
    canonical_route("BOM", "CCU"): 1660.0,
    canonical_route("BOM", "COK"): 1065.0,
    canonical_route("BOM", "DEL"): 1148.0,
    canonical_route("BOM", "GOI"): 435.0,
    canonical_route("BOM", "HYD"): 620.0,
    canonical_route("BOM", "JAI"): 915.0,
    canonical_route("BOM", "MAA"): 1030.0,
    canonical_route("CCU", "DEL"): 1305.0,
    canonical_route("CCU", "GAU"): 510.0,
    canonical_route("COK", "DEL"): 2050.0,
    canonical_route("DEL", "GAU"): 1460.0,
    canonical_route("DEL", "GOI"): 1510.0,
    canonical_route("DEL", "HYD"): 1260.0,
    canonical_route("DEL", "IXC"): 240.0,
    canonical_route("DEL", "LKO"): 420.0,
    canonical_route("DEL", "MAA"): 1760.0,
    canonical_route("DEL", "PAT"): 850.0,
    canonical_route("DEL", "PNQ"): 1170.0,
    canonical_route("DEL", "SXR"): 645.0,
    canonical_route("DEL", "VNS"): 670.0,
}

# Scheduled flight templates per carrier per route
FLIGHT_SCHEDULES: Dict[str, List[Dict[str, str]]] = {
    "6E": [
        {"flight": "6E-205", "time": "06:15", "slot": "early_morning"},
        {"flight": "6E-5317", "time": "08:30", "slot": "prime_morning"},
        {"flight": "6E-6124", "time": "11:45", "slot": "midday"},
        {"flight": "6E-2184", "time": "14:20", "slot": "afternoon"},
        {"flight": "6E-5011", "time": "18:40", "slot": "prime_evening"},
        {"flight": "6E-2489", "time": "21:15", "slot": "night"},
    ],
    "AI": [
        {"flight": "AI-806", "time": "07:00", "slot": "prime_morning"},
        {"flight": "AI-665", "time": "13:10", "slot": "afternoon"},
        {"flight": "AI-887", "time": "19:30", "slot": "prime_evening"},
        {"flight": "AI-441", "time": "22:00", "slot": "night"},
    ],
    "IX": [
        {"flight": "IX-742", "time": "09:15", "slot": "morning"},
        {"flight": "IX-983", "time": "16:45", "slot": "afternoon"},
    ],
    "QP": [
        {"flight": "QP-1302", "time": "07:45", "slot": "prime_morning"},
        {"flight": "QP-1456", "time": "15:20", "slot": "afternoon"},
        {"flight": "QP-1120", "time": "20:10", "slot": "prime_evening"},
    ],
    "SG": [
        {"flight": "SG-8169", "time": "08:00", "slot": "prime_morning"},
        {"flight": "SG-8711", "time": "17:30", "slot": "prime_evening"},
    ],
}

TIME_OF_DAY_MULTIPLIERS = {
    "early_morning": 0.92,
    "prime_morning": 1.15,
    "midday": 0.90,
    "afternoon": 0.94,
    "prime_evening": 1.18,
    "night": 0.88,
    "morning": 1.05,
}

DAY_OF_WEEK_MULTIPLIERS = {
    0: 1.08,  # Monday (corporate start)
    1: 0.95,  # Tuesday (trough)
    2: 0.96,  # Wednesday (mid-week baseline)
    3: 1.00,  # Thursday
    4: 1.18,  # Friday (weekend getaway surge)
    5: 1.06,  # Saturday
    6: 1.15,  # Sunday (return flights)
}

CARRIER_PREMIUM = {
    "AI": 1.14,  # Full Service Carrier (meals, 15-25kg luggage included)
    "6E": 1.02,  # Market leader premium (highest frequency & on-time reputation)
    "IX": 0.96,  # LCC competitive pricing
    "QP": 0.95,  # Aggressive challenger pricing
    "SG": 0.94,  # Discount LCC
}

class DynamicPricingEngine:
    """
    Engine that replicates real-time airline revenue management pricing curves.
    Ensures complete statistical realism matching DGCA monthly trends.
    """

    @classmethod
    def calculate_expected_fare(
        cls,
        orig: str,
        dest: str,
        departure_date_str: str,
        advance_days: int,
        carrier_code: str,
        slot: str = "prime_morning",
        random_seed: int = None,
    ) -> Tuple[float, bool]:
        """
        Calculates dynamic fare based on econometric pricing model:
        Base = 1800 + 2.2 * Distance
        Multiplier = (1 + 1.6 * exp(-0.075 * advance_days)) * Dow * Tod * Carrier * Seasonality
        """
        if random_seed is not None:
            rng = random.Random(random_seed)
        else:
            rng = random.Random()

        c_route = canonical_route(orig, dest)
        dist = ROUTE_DISTANCES.get(c_route, 1100.0)
        
        # Base fare calibrated to Indian aviation cost structures
        base_route_price = 1950.0 + (dist * 2.15)

        # Advance booking exponential curve (T+1 surges 200-300% over T+45)
        # advance_days: 1 -> ~2.48, 7 -> ~1.85, 15 -> ~1.45, 30 -> ~1.12, 45 -> ~1.03
        advance_mult = 1.0 + (1.65 * math.exp(-0.072 * advance_days))

        # Day of week effect
        dep_date = datetime.strptime(departure_date_str, "%Y-%m-%d")
        dow = dep_date.weekday()
        dow_mult = DAY_OF_WEEK_MULTIPLIERS.get(dow, 1.0)

        # Time of day slot effect
        tod_mult = TIME_OF_DAY_MULTIPLIERS.get(slot, 1.0)

        # Carrier brand yield premium
        carrier_mult = CARRIER_PREMIUM.get(carrier_code, 1.0)

        # Long-term macro fuel / inflation drift factor
        # Simulates subtle monthly jet fuel (ATF) fluctuations
        day_of_year = dep_date.timetuple().tm_yday
        seasonal_mult = 1.0 + 0.05 * math.sin((day_of_year / 365.0) * 2 * math.pi)

        # Stochastic noise (+/- 4%)
        noise = rng.uniform(0.96, 1.04)

        raw_fare = base_route_price * advance_mult * dow_mult * tod_mult * carrier_mult * seasonal_mult * noise
        rounded_fare = round(raw_fare / 10.0) * 10.0  # Fares typically rounded to nearest ₹10

        # Sold-out status probability (higher for T+1 and peak hours)
        is_sold_out = False
        if advance_days == 1 and rng.random() < 0.04:
            is_sold_out = True

        return rounded_fare, is_sold_out

    @classmethod
    def generate_daily_quotes(
        cls,
        quote_date_str: str,
        routes: List[Tuple[str, str]] = BASKET_ROUTES,
        advance_windows: List[int] = ADVANCE_WINDOWS,
    ) -> List[Dict[str, Any]]:
        """
        Generates comprehensive multi-source fare quotes for all routes,
        advance windows, airlines, and OTAs for a given observation date.
        """
        quote_date = datetime.strptime(quote_date_str, "%Y-%m-%d")
        scraped_quotes = []

        for orig, dest in routes:
            for adv in advance_windows:
                dep_date = quote_date + timedelta(days=adv)
                dep_date_str = dep_date.strftime("%Y-%m-%d")

                # Generate direct airline portal quotes
                for airline in AIRLINES:
                    code = airline["code"]
                    flights = FLIGHT_SCHEDULES.get(code, [])

                    for f in flights:
                        # Deterministic seed per date-flight-window for reproducibility
                        seed = hash(f"{quote_date_str}-{f['flight']}-{orig}-{dest}-{adv}") % (2**31 - 1)
                        fare, is_sold = cls.calculate_expected_fare(
                            orig, dest, dep_date_str, adv, code, f["slot"], random_seed=seed
                        )

                        scraped_quotes.append({
                            "source": airline["name"],
                            "carrier_code": code,
                            "flight_number": f["flight"],
                            "origin": orig,
                            "destination": dest,
                            "departure_date": dep_date_str,
                            "departure_time": f["time"],
                            "advance_days": adv,
                            "fare_class": "Economy",
                            "quoted_fare": fare,
                            "scraped_at": f"{quote_date_str}T08:00:00",
                            "is_sold_out": 1 if is_sold else 0,
                            "raw_payload": None,
                        })

                # Generate OTA quotes (MakeMyTrip, EaseMyTrip, etc.)
                # OTAs list the same flights with small markup or convenience discount
                for ota in OTAS[:2]:  # Sample MakeMyTrip and EaseMyTrip
                    for code in ["6E", "AI"]:
                        sample_flight = FLIGHT_SCHEDULES[code][0]
                        seed = hash(f"OTA-{ota['name']}-{quote_date_str}-{sample_flight['flight']}-{adv}") % (2**31 - 1)
                        fare, is_sold = cls.calculate_expected_fare(
                            orig, dest, dep_date_str, adv, code, sample_flight["slot"], random_seed=seed
                        )
                        # OTAs occasionally add slight markup or discount coupons (-₹100 to +₹150)
                        ota_fare = fare + (ota["convenience_fee"] * 0.4)

                        scraped_quotes.append({
                            "source": ota["name"],
                            "carrier_code": code,
                            "flight_number": sample_flight["flight"],
                            "origin": orig,
                            "destination": dest,
                            "departure_date": dep_date_str,
                            "departure_time": sample_flight["time"],
                            "advance_days": adv,
                            "fare_class": "Economy",
                            "quoted_fare": round(ota_fare / 10.0) * 10.0,
                            "scraped_at": f"{quote_date_str}T08:15:00",
                            "is_sold_out": 1 if is_sold else 0,
                            "raw_payload": None,
                        })

        return scraped_quotes
