# Genetic Panel Scraper

Automatically scrapes panel and gene data from major genetic testing labs and outputs a formatted Excel workbook.

## Labs Covered

| Lab | Method |
|-----|--------|
| Invitae | JSON API |
| Ambry Genetics | HTML (requests + BS4) |
| GeneDx | JSON API + HTML fallback |
| Myriad Genetics | HTML (requests + BS4) |
| Blueprint Genetics | HTML (requests + BS4) |
| Natera | HTML (requests + BS4) |
| Fulgent Genetics | JSON API + HTML fallback |

## Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Install Playwright browser (needed for JS-heavy sites if upgraded)
playwright install chromium
```

## Usage

### Run once (all labs)
```bash
python main.py
```

### Run specific labs
```bash
python main.py --labs invitae genedx
```

### List available labs
```bash
python main.py --list
```

### Start scheduler
```bash
# Weekly on Monday at 6am (default)
python main.py --schedule

# Daily at 8am
python main.py --schedule --interval daily --hour 8

# Monthly on the 1st at 6am
python main.py --schedule --interval monthly

# Weekly on Friday at 7am
python main.py --schedule --interval weekly --day fri --hour 7
```

## Output

Excel workbook saved to `output/genetic_panels_YYYY-MM-DD.xlsx` with 4 sheets:

- **Summary** — panel/gene counts per lab
- **All Panels** — every panel across all labs
- **[Lab name]** — one tab per lab
- **Gene Cross-Reference** — which genes appear across how many panels/labs

## Scheduling with Cron (alternative to --schedule)

Add to crontab (`crontab -e`):
```
# Every Monday at 6am
0 6 * * 1 /usr/bin/python3 /path/to/genetic_panel_scraper/main.py >> /path/to/logs/cron.log 2>&1
```

## Project Structure

```
genetic_panel_scraper/
├── scrapers/
│   ├── base_scraper.py      # Abstract base class
│   ├── invitae.py
│   ├── ambry.py
│   ├── genedx.py
│   ├── myriad.py
│   ├── blueprint.py
│   └── natera_fulgent.py
├── consolidator.py          # Excel output builder
├── main.py                  # CLI + scheduler
├── requirements.txt
├── output/                  # Generated workbooks
└── logs/                    # Scraper run logs
```

## Adding a New Lab

1. Create `scrapers/newlab.py` extending `BaseScraper`
2. Implement the `scrape()` method returning `List[Panel]`
3. Add to `scrapers/__init__.py` in `ALL_SCRAPERS`

```python
from scrapers.base_scraper import BaseScraper, Panel

class NewLabScraper(BaseScraper):
    LAB_NAME = "New Lab"
    BASE_URL = "https://www.newlab.com"

    def scrape(self):
        panels = []
        # ... your scraping logic ...
        return panels
```

## Notes

- Scrapers include random delays (1–3s) between requests to be respectful
- Each scraper has independent error handling — one failure won't stop others
- If a lab's site structure changes, update the relevant scraper's selectors
- Set `parallel=False` in `run_scrapers()` for sequential execution (easier debugging)
