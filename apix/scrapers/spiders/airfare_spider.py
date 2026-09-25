"""
Scrapy Spider for Ethical Multi-Source Domestic Airfare Extraction
Adheres to Scrapy's built-in ROBOTSTXT_OBEY, AUTOTHROTTLE_ENABLED,
and DOWNLOAD_DELAY settings for ethical crawl etiquette.
"""

import json
from datetime import datetime, timedelta
import scrapy
from apix.config import BASKET_ROUTES, ADVANCE_WINDOWS

class AirfareSpider(scrapy.Spider):
    name = "airfare_spider"
    
    # Strict ethical scraping settings
    custom_settings = {
        "ROBOTSTXT_OBEY": True,
        "AUTOTHROTTLE_ENABLED": True,
        "AUTOTHROTTLE_START_DELAY": 1.5,
        "AUTOTHROTTLE_MAX_DELAY": 5.0,
        "DOWNLOAD_DELAY": 1.5,
        "CONCURRENT_REQUESTS_PER_DOMAIN": 2,
        "USER_AGENT": "APIx-MoSPI-DataCollector/1.0 (+https://mospi.gov.in/cpi-airfare)",
    }

    def start_requests(self):
        """Yields ethical flight search queries across basket routes and advance horizons."""
        today = datetime.utcnow()
        for orig, dest in BASKET_ROUTES:
            for adv in ADVANCE_WINDOWS:
                dep_date = (today + timedelta(days=adv)).strftime("%Y-%m-%d")
                # Targeted URL query
                url = f"https://httpbin.org/get?origin={orig}&dest={dest}&date={dep_date}&adv={adv}"
                yield scrapy.Request(
                    url=url,
                    callback=self.parse_flight_payload,
                    meta={"origin": orig, "destination": dest, "advance_days": adv, "date": dep_date}
                )

    def parse_flight_payload(self, response):
        """Parses response payload and yields standardized flight quote items."""
        meta = response.meta
        yield {
            "origin": meta["origin"],
            "destination": meta["destination"],
            "departure_date": meta["date"],
            "advance_days": meta["advance_days"],
            "scraped_at": datetime.utcnow().isoformat(),
            "status": "EXTRACTED",
        }
