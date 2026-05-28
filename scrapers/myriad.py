"""
Myriad Genetics scraper
Catalog: https://myriad.com/providers/
Uses requests + BS4 to walk test listing pages.
"""
import logging
import requests
from bs4 import BeautifulSoup
from typing import List
from .base_scraper import BaseScraper, Panel

logger = logging.getLogger(__name__)


class MyriadScraper(BaseScraper):
    LAB_NAME = "Myriad Genetics"
    BASE_URL = "https://myriad.com"
    CATALOG_URL = "https://myriad.com/providers/"

    def scrape(self) -> List[Panel]:
        panels = []
        try:
            resp = requests.get(self.CATALOG_URL, headers=self.HEADERS, timeout=30)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "lxml")
        except Exception as e:
            logger.error(f"[{self.LAB_NAME}] Failed to load catalog: {e}")
            return panels

        # Collect test links
        test_links = []
        for a in soup.select("a[href]"):
            href = a.get("href", "")
            # Filter to product/test detail pages
            if any(kw in href for kw in ["/products/", "/tests/", "/genetic-tests/"]):
                full = href if href.startswith("http") else f"{self.BASE_URL}{href}"
                text = a.get_text(strip=True)
                if text and full not in [l[0] for l in test_links]:
                    test_links.append((full, text))

        logger.info(f"[{self.LAB_NAME}] Found {len(test_links)} test links")

        for url, name in test_links:
            genes = self._fetch_genes_from_page(url)
            self.delay(1.0, 2.5)
            panels.append(Panel(
                lab=self.LAB_NAME,
                panel_name=name,
                genes=genes,
                gene_count=len(genes),
                url=url,
            ))

        return panels

    def _fetch_genes_from_page(self, url: str) -> List[str]:
        try:
            resp = requests.get(url, headers=self.HEADERS, timeout=20)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "lxml")

            # Common patterns for gene lists on Myriad pages
            for selector in [".gene-list li", ".genes li", "[class*='gene'] li", "ul.genes"]:
                items = soup.select(selector)
                if items:
                    return [i.get_text(strip=True) for i in items if i.get_text(strip=True)]

            # Fallback: text blocks with gene patterns
            for el in soup.find_all(["p", "div", "td"]):
                text = el.get_text()
                if any(kw in text.lower() for kw in ["brca1", "brca2", "genes analyzed", "gene panel"]):
                    genes = [g.strip() for g in text.replace("\n", ",").split(",") if len(g.strip()) <= 20 and g.strip().isupper()]
                    if genes:
                        return genes
        except Exception as e:
            logger.warning(f"[{self.LAB_NAME}] Gene fetch failed {url}: {e}")
        return []

