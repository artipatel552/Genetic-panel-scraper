"""
Invitae scraper
Catalog API: https://www.invitae.com/api/public/test-catalog/v1/panels
Returns JSON — no JS rendering needed.
"""
import logging
import requests
from typing import List
from .base_scraper import BaseScraper, Panel

logger = logging.getLogger(__name__)


class InvitaeScraper(BaseScraper):
    LAB_NAME = "Invitae"
    BASE_URL = "https://www.invitae.com"
    API_URL = "https://www.invitae.com/api/public/test-catalog/v1/panels"
    PANEL_DETAIL_URL = "https://www.invitae.com/api/public/test-catalog/v1/panels/{panel_id}/genes"

    def scrape(self) -> List[Panel]:
        panels = []
        try:
            resp = requests.get(self.API_URL, headers=self.HEADERS, timeout=30)
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            logger.error(f"[{self.LAB_NAME}] Failed to fetch catalog: {e}")
            return panels

        raw_panels = data if isinstance(data, list) else data.get("panels", data.get("data", []))
        logger.info(f"[{self.LAB_NAME}] Found {len(raw_panels)} panels in catalog")

        for item in raw_panels:
            panel_id = str(item.get("id", item.get("panelId", "")))
            panel_name = item.get("name", item.get("title", ""))
            specialty = item.get("specialty", item.get("category", ""))
            panel_url = f"{self.BASE_URL}/en/providers/test-catalog/{panel_id}"

            # Fetch gene list for this panel
            genes = self._fetch_genes(panel_id)
            self.delay(0.5, 1.5)

            panels.append(Panel(
                lab=self.LAB_NAME,
                panel_name=panel_name,
                panel_id=panel_id,
                specialty=specialty,
                genes=genes,
                gene_count=len(genes),
                url=panel_url,
            ))

        return panels

    def _fetch_genes(self, panel_id: str) -> List[str]:
        try:
            url = self.PANEL_DETAIL_URL.format(panel_id=panel_id)
            resp = requests.get(url, headers=self.HEADERS, timeout=20)
            resp.raise_for_status()
            data = resp.json()
            gene_list = data if isinstance(data, list) else data.get("genes", [])
            return [g.get("symbol", g.get("geneSymbol", "")) for g in gene_list if isinstance(g, dict)]
        except Exception as e:
            logger.warning(f"[{self.LAB_NAME}] Could not fetch genes for panel {panel_id}: {e}")
            return []

