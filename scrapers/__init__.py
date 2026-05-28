print("loading scrapers package")

from .invitae import InvitaeScraper
print("invitae ok")

from .ambry import AmbryScraper
print("ambry ok")

from .genedx import GeneDxScraper
print("genedx ok")

from .myriad import MyriadScraper
print("myriad ok")

from .blueprint import BlueprintScraper
print("blueprint ok")

from .natera_fulgent import NateraScraper, FulgentScraper
print("natera_fulgent ok")

ALL_SCRAPERS = [
    InvitaeScraper,
    AmbryScraper,
    GeneDxScraper,
    MyriadScraper,
    BlueprintScraper,
    NateraScraper,
    FulgentScraper,
]
