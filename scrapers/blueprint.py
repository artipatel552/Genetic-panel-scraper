"""
Blueprint Genetics scraper
Catalog: https://blueprintgenetics.com/tests/panels/
Uses requests + BS4 — panel list is server-side rendered.
"""
import logging
import requests
from bs4 import BeautifulSoup
from typing import List
from .base_scraper import BaseScraper, Panel

logger = logging.getLogger(__name__)


class BlueprintScraper(BaseScraper):
    LAB_NAME = "Blueprint Genetics"
    BASE_URL = "https://blueprintgenetics.com"
    CATALOG_URL = "https://blueprintgenetics.com/tests/panels/"

    def scrape(self) -> List[Panel]:
        panels = []
        try:
            resp = requests.get(self.CATALOG_URL, headers=self.HEADERS, timeout=30)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "lxml")
        except Exception as e:
            logger.error(f"[{self.LAB_NAME}] Catalog load failed: {e}")
            return panels

        panel_links = []
        for a in soup.select("a[href*='/tests/panels/']"):
            href = a.get("href", "")
            name = a.get_text(strip=True)
            full = href if href.startswith("http") else f"{self.BASE_URL}{href}"
            if name and full != self.CATALOG_URL and full not in [x[0] for x in panel_links]:
                panel_links.append((full, name))

        # Also check for panel cards
        for card in soup.select(".panel-card, .test-item, article"):
            link = card.select_one("a")
            title = card.select_one("h2, h3, .panel-name, .title")
            if link and title:
                href = link.get("href", "")
                full = href if href.startswith("http") else f"{self.BASE_URL}{href}"
                name = title.get_text(strip=True)
                if name and full not in [x[0] for x in panel_links]:
                    panel_links.append((full, name))

        logger.info(f"[{self.LAB_NAME}] Found {len(panel_links)} panels")

        for url, name in panel_links:
            specialty, genes = self._fetch_panel_detail(url)
            self.delay(0.8, 2.0)
            panels.append(Panel(
                lab=self.LAB_NAME,
                panel_name=name,
                specialty=specialty,
                genes=genes,
                gene_count=len(genes),
                url=url,
            ))

        return panels

    def _fetch_panel_detail(self, url: str):
        specialty = ""
        genes = []
        try:
            resp = requests.get(url, headers=self.HEADERS, timeout=20)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "lxml")

            # Specialty
            spec_el = soup.select_one(".specialty, .category, .panel-specialty, [class*='specialty']")
            if spec_el:
                specialty = spec_el.get_text(strip=True)

            # Gene list — Blueprint typically lists genes in a table or list
            for selector in [
                "table.gene-table td:first-child",
                ".gene-list li",
                ".genes-included li",
                "[class*='gene-list'] li",
                "td.gene",
            ]:
                items = soup.select(selector)
                if items:
                    genes = [i.get_text(strip=True) for i in items if i.get_text(strip=True)]
                    break

            # Fallback: look for JSON-LD or data attributes
            if not genes:
                for script in soup.select("script[type='application/json'], script[type='application/ld+json']"):
                    import json
                    try:
                        data = json.loads(script.string or "")
                        gene_data = data.get("genes", data.get("geneList", []))
                        if gene_data:
                            genes = [g if isinstance(g, str) else g.get("symbol", "") for g in gene_data]
                            break
                    except Exception:
                        pass

        except Exception as e:
            logger.warning(f"[{self.LAB_NAME}] Detail fetch failed {url}: {e}")
        return specialty, genes

