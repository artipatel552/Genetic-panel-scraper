import logging
import time
import random
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Optional
from datetime import date

logger = logging.getLogger(__name__)


@dataclass
class Gene:
    symbol: str
    name: str = ""


@dataclass
class Panel:
    lab: str
    panel_name: str
    panel_id: str = ""
    specialty: str = ""
    genes: List[str] = field(default_factory=list)
    gene_count: int = 0
    url: str = ""
    scraped_date: str = field(default_factory=lambda: date.today().isoformat())

    def __post_init__(self):
        if self.genes and not self.gene_count:
            self.gene_count = len(self.genes)


class BaseScraper(ABC):
    LAB_NAME: str = ""
    BASE_URL: str = ""

    HEADERS = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "en-US,en;q=0.9",
    }

    def __init__(self):
        self.panels: List[Panel] = []
        self.errors: List[str] = []

    def delay(self, min_s=1.0, max_s=3.0):
        time.sleep(random.uniform(min_s, max_s))

    @abstractmethod
    def scrape(self) -> List[Panel]:
        """Scrape all panels from the lab. Returns list of Panel objects."""
        pass

    def run(self) -> List[Panel]:
        logger.info(f"[{self.LAB_NAME}] Starting scrape...")
        try:
            self.panels = self.scrape()
            logger.info(f"[{self.LAB_NAME}] Done — {len(self.panels)} panels found.")
        except Exception as e:
            msg = f"[{self.LAB_NAME}] Fatal error: {e}"
            logger.error(msg)
            self.errors.append(msg)
        return self.panels

