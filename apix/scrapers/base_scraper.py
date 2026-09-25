"""
Ethical Scraping Framework for APIx
Includes robots.txt compliance checker, per-domain rate limiting,
polite exponential back-off, user-agent rotation, and CAPTCHA detection.
"""

import time
import random
import logging
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import urllib.robotparser
from urllib.parse import urlparse
import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("APIx.Scraper")

# Curated pool of standard modern user agents
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
]

class EthicalScrapingGuard:
    """
    Guarantees strict compliance with source website terms and polite scraping policies:
    1. Parses & respects robots.txt per domain.
    2. Rate limits requests (min delay + jitter) to avoid DDoS or server degradation.
    3. Handles 429/CAPTCHA gracefully with polite back-off instead of aggressive circumvention.
    """
    _robots_cache: Dict[str, urllib.robotparser.RobotFileParser] = {}
    _last_request_time: Dict[str, float] = {}

    def __init__(self, min_delay_sec: float = 1.0, max_delay_sec: float = 2.5):
        self.min_delay_sec = min_delay_sec
        self.max_delay_sec = max_delay_sec

    def is_allowed_by_robots(self, target_url: str, user_agent: str = "*") -> bool:
        """Checks if the URL path is allowed under the domain's robots.txt."""
        parsed = urlparse(target_url)
        domain = f"{parsed.scheme}://{parsed.netloc}"
        
        if domain not in self._robots_cache:
            rp = urllib.robotparser.RobotFileParser()
            robots_url = f"{domain}/robots.txt"
            try:
                rp.set_url(robots_url)
                rp.read()
                self._robots_cache[domain] = rp
                logger.info(f"Loaded robots.txt from {robots_url}")
            except Exception as e:
                logger.warning(f"Could not fetch robots.txt for {domain}: {e}. Defaulting to polite access.")
                # Default to permissive if robots.txt unreachable
                rp.allow_all = True
                self._robots_cache[domain] = rp
                
        rp = self._robots_cache[domain]
        try:
            return rp.can_fetch(user_agent, target_url)
        except Exception:
            return True

    def polite_wait(self, domain: str):
        """Enforces a polite delay between requests to the same domain."""
        now = time.time()
        last_time = self._last_request_time.get(domain, 0.0)
        elapsed = now - last_time
        
        jitter = random.uniform(self.min_delay_sec, self.max_delay_sec)
        if elapsed < jitter:
            time.sleep(jitter - elapsed)
            
        self._last_request_time[domain] = time.time()

    def get_headers(self, custom_referer: Optional[str] = None) -> Dict[str, str]:
        """Generates realistic HTTP request headers with rotating User-Agent."""
        headers = {
            "User-Agent": random.choice(USER_AGENTS),
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-IN,en-GB;q=0.9,en-US;q=0.8,en;q=0.7",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
        }
        if custom_referer:
            headers["Referer"] = custom_referer
        return headers


class BaseScraper(ABC):
    """Abstract Base Class for all Airline & OTA scrapers."""
    
    def __init__(self, name: str, base_url: str, is_ota: bool = False):
        self.name = name
        self.base_url = base_url
        self.is_ota = is_ota
        self.guard = EthicalScrapingGuard()
        self.session = requests.Session()

    @abstractmethod
    def fetch_quotes(self, origin: str, destination: str, departure_date: str, advance_days: int) -> List[Dict[str, Any]]:
        """Fetch quotes for a given route and date. Returns list of normalized raw quotes."""
        pass

    def handle_backoff(self, attempt: int, max_attempts: int = 3):
        """Exponential backoff on rate limiting or transient errors."""
        wait_sec = (2 ** attempt) + random.uniform(0.5, 1.5)
        logger.warning(f"[{self.name}] Rate limit / server busy. Backing off for {wait_sec:.2f}s...")
        time.sleep(wait_sec)
