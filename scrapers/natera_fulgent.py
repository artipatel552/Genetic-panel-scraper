"""
Natera scraper
Catalog: https://www.natera.com/oncology/oncology-test-menu/
"""
import logging
import requests
from bs4 import BeautifulSoup
from typing import List
from .base_scraper import BaseScraper, Panel

logger = logging.getLogger(__name__)


class NateraScraper(BaseScraper):
    LAB_NAME = "Natera"
    BASE_URL = "https://www.natera.com"
    CATALOG_URLS = [
        "https://www.natera.com/oncology/oncology-test-menu/",
        "https://www.natera.com/womens-health/",
        "https://www.natera.com/organ-health/",
    ]

    def scrape(self) -> List[Panel]:
        panels = []
        seen = set()

        for catalog_url in self.CATALOG_URLS:
            specialty = catalog_url.split("/")[-2].replace("-", " ").title()
            try:
                resp = requests.get(catalog_url, headers=self.HEADERS, timeout=30)
                resp.raise_for_status()
                soup = BeautifulSoup(resp.text, "lxml")
            except Exception as e:
                logger.warning(f"[{self.LAB_NAME}] {catalog_url} failed: {e}")
                continue

            for a in soup.select("a[href]"):
                href = a.get("href", "")
                name = a.get_text(strip=True)
                if not name or len(name) < 3:
                    continue
                if not any(kw in href for kw in ["/tests/", "/products/", "/oncology/", "/womens-health/", "/organ-health/"]):
                    continue
                full = href if href.startswith("http") else f"{self.BASE_URL}{href}"
                if full in seen or full == catalog_url:
                    continue
                seen.add(full)

                genes = self._fetch_genes(full)
                self.delay(0.5, 1.5)

                panels.append(Panel(
                    lab=self.LAB_NAME,
                    panel_name=name,
                    specialty=specialty,
                    genes=genes,
                    gene_count=len(genes),
                    url=full,
                ))

            self.delay(1.0, 2.0)

        logger.info(f"[{self.LAB_NAME}] Total panels: {len(panels)}")
        return panels

    def _fetch_genes(self, url: str) -> List[str]:
        try:
            resp = requests.get(url, headers=self.HEADERS, timeout=15)
            soup = BeautifulSoup(resp.text, "lxml")
            for sel in [".gene-list li", ".genes li", "[class*='gene'] li"]:
                items = soup.select(sel)
                if items:
                    return [i.get_text(strip=True) for i in items]
        except Exception:
            pass
        return []


"""
Fulgent Genetics scraper
Catalog: https://www.fulgentgenetics.com/gene-panel-tests
"""


class FulgentScraper(BaseScraper):
    LAB_NAME = "Fulgent Genetics"
    BASE_URL = "https://www.fulgentgenetics.com"
    CATALOG_URL = "https://www.fulgentgenetics.com/gene-panel-tests"
    API_URL = "https://www.fulgentgenetics.com/api/v1/tests"

    def scrape(self) -> List[Panel]:
        panels = self._try_api()
        if not panels:
            panels = self._try_html()
        return panels

    def _try_api(self) -> List[Panel]:
        panels = []
        try:
            resp = requests.get(self.API_URL, headers=self.HEADERS, timeout=20)
            if resp.status_code != 200:
                return []
            data = resp.json()
            items = data if isinstance(data, list) else data.get("tests", data.get("data", []))
            for item in items:
                name = item.get("name", item.get("title", ""))
                genes_raw = item.get("genes", [])
                genes = genes_raw if isinstance(genes_raw, list) else [g.strip() for g in str(genes_raw).split(",")]
                panels.append(Panel(
                    lab=self.LAB_NAME,
                    panel_name=name,
                    panel_id=str(item.get("id", item.get("test_code", ""))),
                    specialty=item.get("category", ""),
                    genes=genes,
                    gene_count=len(genes),
                    url=item.get("url", self.BASE_URL),
                ))
        except Exception as e:
            logger.warning(f"[{self.LAB_NAME}] API failed: {e}")
        return panels

    def _try_html(self) -> List[Panel]:
        panels = []
        try:
            resp = requests.get(self.CATALOG_URL, headers=self.HEADERS, timeout=30)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "lxml")

            for row in soup.select("tr, .test-row, .panel-row"):
                cells = row.select("td, .cell")
                if len(cells) >= 2:
                    name = cells[0].get_text(strip=True)
                    link = row.select_one("a")
                    href = link.get("href", "") if link else ""
                    full_url = href if href.startswith("http") else f"{self.BASE_URL}{href}"

                    if name:
                        panels.append(Panel(
                            lab=self.LAB_NAME,
                            panel_name=name,
                            url=full_url,
                        ))
        except Exception as e:
            logger.error(f"[{self.LAB_NAME}] HTML fallback failed: {e}")
        return panels

