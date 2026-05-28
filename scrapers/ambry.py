"""
Ambry Genetics scraper
Catalog: https://www.ambrygen.com/tests
HTML-based with pagination — uses requests + BeautifulSoup.
"""
import logging
import requests
from bs4 import BeautifulSoup
from typing import List
from .base_scraper import BaseScraper, Panel

logger = logging.getLogger(__name__)


class AmbryScraper(BaseScraper):
    LAB_NAME = "Ambry Genetics"
    BASE_URL = "https://www.ambrygen.com"
    CATALOG_URL = "https://www.ambrygen.com/tests"

    def scrape(self) -> List[Panel]:
        panels = []
        page = 1

        while True:
            url = f"{self.CATALOG_URL}?page={page}" if page > 1 else self.CATALOG_URL
            try:
                resp = requests.get(url, headers=self.HEADERS, timeout=30)
                resp.raise_for_status()
            except Exception as e:
                logger.error(f"[{self.LAB_NAME}] Failed page {page}: {e}")
                break

            soup = BeautifulSoup(resp.text, "lxml")
            panel_cards = soup.select(".test-card, .panel-card, article.test, .tests-list-item")

            if not panel_cards:
                # Try alternate selectors
                panel_cards = soup.select("a[href*='/tests/']")

            if not panel_cards:
                logger.info(f"[{self.LAB_NAME}] No more panels on page {page}")
                break

            logger.info(f"[{self.LAB_NAME}] Page {page}: {len(panel_cards)} panels")

            for card in panel_cards:
                name = ""
                href = ""

                if card.name == "a":
                    name = card.get_text(strip=True)
                    href = card.get("href", "")
                else:
                    name_el = card.select_one("h2, h3, .test-name, .panel-name")
                    name = name_el.get_text(strip=True) if name_el else ""
                    link_el = card.select_one("a")
                    href = link_el.get("href", "") if link_el else ""

                if not name:
                    continue

                full_url = href if href.startswith("http") else f"{self.BASE_URL}{href}"
                specialty = self._extract_specialty(card)
                genes = self._fetch_panel_genes(full_url) if href else []
                self.delay(0.8, 2.0)

                panels.append(Panel(
                    lab=self.LAB_NAME,
                    panel_name=name,
                    specialty=specialty,
                    genes=genes,
                    gene_count=len(genes),
                    url=full_url,
                ))

            # Check for next page
            next_btn = soup.select_one("a[rel='next'], .pagination .next:not(.disabled)")
            if not next_btn:
                break
            page += 1

        return panels

    def _extract_specialty(self, card) -> str:
        tag = card.select_one(".specialty, .category, .test-type")
        return tag.get_text(strip=True) if tag else ""

    def _fetch_panel_genes(self, url: str) -> List[str]:
        try:
            resp = requests.get(url, headers=self.HEADERS, timeout=20)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "lxml")

            # Look for gene list in common patterns
            gene_section = soup.select_one(".genes-list, .gene-list, #genes, [class*='gene']")
            if gene_section:
                items = gene_section.select("li, span.gene, .gene-symbol")
                return [i.get_text(strip=True) for i in items if i.get_text(strip=True)]

            # Fallback: look for comma-separated gene text
            for el in soup.select("p, div"):
                text = el.get_text()
                if "genes:" in text.lower() or "includes:" in text.lower():
                    parts = text.split(":", 1)
                    if len(parts) > 1:
                        return [g.strip() for g in parts[1].split(",") if g.strip()]
        except Exception as e:
            logger.warning(f"[{self.LAB_NAME}] Gene fetch failed for {url}: {e}")
        return []

