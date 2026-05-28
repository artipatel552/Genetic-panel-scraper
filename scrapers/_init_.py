from .invitae import InvitaeScraper
from .ambry import AmbryScraper
from .genedx import GeneDxScraper
from .myriad import MyriadScraper
from .blueprint import BlueprintScraper
from .natera_fulgent import NateraScraper, FulgentScraper

ALL_SCRAPERS = [
    InvitaeScraper,
    AmbryScraper,
    GeneDxScraper,
    MyriadScraper,
    BlueprintScraper,
    NateraScraper,
    FulgentScraper,
]
