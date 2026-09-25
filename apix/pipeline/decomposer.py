"""
Fare Decomposition Engine for APIx
Deconstructs all-inclusive airfare quotes into economic components:
- Base Fare (Aviation core yield)
- Passenger Service Fee (PSF / Aviation Security Fee)
- User Development Fee (UDF - airport infrastructure charges)
- Goods and Services Tax (GST - 5% on Economy)
- OTA Convenience Fees
"""

from typing import Dict, Any
from apix.config import AIRPORT_DATA, ECONOMY_GST_RATE

class FareDecomposer:
    @staticmethod
    def decompose(quote: Dict[str, Any]) -> Dict[str, float]:
        """
        Decomposes total fare into statutory and commercial line items.
        Total = Base + PSF + UDF + GST + Convenience
        where GST = Base * 0.05
        => Base * 1.05 = Total - PSF - UDF - Convenience
        => Base = (Total - PSF - UDF - Convenience) / 1.05
        """
        total_fare = float(quote.get("quoted_fare", 0.0))
        origin = quote.get("origin", "DEL")
        source = quote.get("source", "")
        
        # Look up origin airport fees
        origin_meta = AIRPORT_DATA.get(origin, AIRPORT_DATA["DEL"])
        udf = float(origin_meta.get("udf_rate", 380.0))
        psf = float(origin_meta.get("psf_rate", 91.0))

        # Convenience fee is charged by OTAs, typically ₹250 to ₹350
        convenience_fee = 0.0
        if "MakeMyTrip" in source:
            convenience_fee = 349.0
        elif "EaseMyTrip" in source:
            convenience_fee = 0.0
        elif "Yatra" in source:
            convenience_fee = 399.0
        elif "Cleartrip" in source:
            convenience_fee = 299.0
        elif "Ixigo" in source:
            convenience_fee = 249.0

        # Protect against negative base if fare is artificially low
        fixed_fees = psf + udf + convenience_fee
        net_for_base_and_gst = max(500.0, total_fare - fixed_fees)
        
        base_fare = round(net_for_base_and_gst / (1.0 + ECONOMY_GST_RATE), 2)
        gst = round(base_fare * ECONOMY_GST_RATE, 2)
        
        # Round components
        return {
            "base_fare": base_fare,
            "psf": psf,
            "udf": udf,
            "gst": gst,
            "convenience_fee": convenience_fee,
            "total_fare": round(base_fare + psf + udf + gst + convenience_fee, 2),
        }
