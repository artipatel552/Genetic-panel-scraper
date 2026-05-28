"""
GeneDx scraper
Catalog API: https://www.genedx.com/test-catalog/
Uses their public search API endpoint.
"""
import logging
import requests
from typing import List
from .base_scraper import BaseScraper, Panel

logger = logging.getLogger(__name__)


class GeneDxScraper(BaseScraper):
    LAB_NAME = "GeneDx"
    BASE_URL = "https://www.genedx.com"
    API_URL = "https://www.genedx.com/wp-json/genedx/v1/tests"
    FALLBACK_URL = "https://www.genedx.com/test-catalog/"

    def scrape(self) -> List[Panel]:
        panels = self._try_api()
        if not panels:
            panels = self._try_html()
        return panels

    def _try_api(self) -> List[Panel]:
        panels = []
        page = 1
        per_page = 100

        while True:
            try:
                resp = requests.get(
                    self.API_URL,
                    params={"per_page": per_page, "page": page},
                    headers=self.HEADERS,
                    timeout=30,
                )
                if resp.status_code == 400:
                    break
                resp.raise_for_status()
                data = resp.json()
            except Exception as e:
                logger.warning(f"[{self.LAB_NAME}] API page {page} failed: {e}")
                break

            items = data if isinstance(data, list) else data.get("tests", data.get("results", []))
            if not items:
                break

            logger.info(f"[{self.LAB_NAME}] API page {page}: {len(items)} panels")

            for item in items:
                name = item.get("title", {})
                if isinstance(name, dict):
                    name = name.get("rendered", "")

                genes_raw = item.get("genes", item.get("gene_list", []))
                if isinstance(genes_raw, str):
                    genes = [g.strip() for g in genes_raw.split(",") if g.strip()]
                elif isinstance(genes_raw, list):
                    genes = [str(g) for g in genes_raw]
                else:
                    genes = []

                slug = item.get("slug", "")
                url = f"{self.BASE_URL}/test-catalog/{slug}" if slug else self.BASE_URL

                panels.append(Panel(
                    lab=self.LAB_NAME,
                    panel_name=name,
                    panel_id=str(item.get("id", "")),
                    specialty=item.get("specialty", item.get("category", "")),
                    genes=genes,
                    gene_count=len(genes) or item.get("gene_count", 0),
                    url=url,
                ))

            if len(items) < per_page:
                break
            page += 1
            self.delay(0.5, 1.5)

        return panels

    def _try_html(self) -> List[Panel]:
        from bs4 import BeautifulSoup
        panels = []
        try:
            resp = requests.get(self.FALLBACK_URL, headers=self.HEADERS, timeout=30)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "lxml")

            for link in soup.select("a[href*='/test-catalog/']"):
                name = link.get_text(strip=True)
                href = link.get("href", "")
                if name and href and href != self.FALLBACK_URL:
                    panels.append(Panel(
                        lab=self.LAB_NAME,
                        panel_name=name,
                        url=href if href.startswith("http") else f"{self.BASE_URL}{href}",
                    ))
        except Exception as e:
            logger.error(f"[{self.LAB_NAME}] HTML fallback failed: {e}")
        return panels

