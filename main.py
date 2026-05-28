"""
main.py — run scrapers manually or start the scheduler.

Usage:
  python main.py                  # Run all scrapers once now
  python main.py --schedule       # Start scheduler (weekly by default)
  python main.py --labs invitae genedx  # Run specific labs only
  python main.py --list           # List available labs
"""
import argparse
import logging
import sys
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

from scrapers import ALL_SCRAPERS
from scrapers.base_scraper import Panel
from consolidator import build_workbook

# ── Logging ──────────────────────────────────────────────────────
LOG_DIR = Path(__file__).parent / "logs"
LOG_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(LOG_DIR / "scraper.log", encoding="utf-8"),
    ],
)
logger = logging.getLogger(__name__)

LAB_MAP = {s.LAB_NAME.lower().replace(" ", ""): s for s in ALL_SCRAPERS}


# ── Core run logic ────────────────────────────────────────────────
def run_scrapers(labs: list = None, parallel: bool = True) -> list[Panel]:
    scrapers_to_run = ALL_SCRAPERS
    if labs:
        keys = [l.lower().replace(" ", "") for l in labs]
        scrapers_to_run = [s for s in ALL_SCRAPERS if s.LAB_NAME.lower().replace(" ", "") in keys]
        if not scrapers_to_run:
            logger.error(f"No matching labs found for: {labs}")
            return []

    all_panels: list[Panel] = []
    errors = []

    if parallel and len(scrapers_to_run) > 1:
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = {executor.submit(s().run): s.LAB_NAME for s in scrapers_to_run}
            for future in as_completed(futures):
                lab = futures[future]
                try:
                    panels = future.result()
                    all_panels.extend(panels)
                    logger.info(f"✓ {lab}: {len(panels)} panels")
                except Exception as e:
                    msg = f"✗ {lab}: {e}"
                    logger.error(msg)
                    errors.append(msg)
    else:
        for scraper_cls in scrapers_to_run:
            s = scraper_cls()
            panels = s.run()
            all_panels.extend(panels)

    logger.info(f"\n{'='*50}")
    logger.info(f"Total panels collected: {len(all_panels)}")
    logger.info(f"Errors: {len(errors)}")
    if errors:
        for e in errors:
            logger.warning(e)

    return all_panels


def run_and_export(labs=None):
    logger.info("=" * 50)
    logger.info("Starting genetic panel scrape run")
    logger.info("=" * 50)

    panels = run_scrapers(labs=labs)

    if not panels:
        logger.warning("No panels collected — skipping export.")
        return None

    # Sanity check: warn if a lab returned 0 results
    lab_counts = {}
    for p in panels:
        lab_counts[p.lab] = lab_counts.get(p.lab, 0) + 1
    for lab, count in lab_counts.items():
        if count == 0:
            logger.warning(f"⚠️  {lab} returned 0 panels — check scraper or site structure")

    output_path = build_workbook(panels)
    logger.info(f"Output: {output_path}")
    return output_path


# ── Scheduler ────────────────────────────────────────────────────
def start_scheduler(interval: str = "weekly", day: str = "mon", hour: int = 6):
    try:
        from apscheduler.schedulers.blocking import BlockingScheduler
    except ImportError:
        logger.error("apscheduler not installed. Run: pip install apscheduler")
        sys.exit(1)

    scheduler = BlockingScheduler(timezone="America/Chicago")

    if interval == "weekly":
        scheduler.add_job(run_and_export, "cron", day_of_week=day, hour=hour, minute=0)
        logger.info(f"Scheduler started — runs every {day.upper()} at {hour:02d}:00")
    elif interval == "daily":
        scheduler.add_job(run_and_export, "cron", hour=hour, minute=0)
        logger.info(f"Scheduler started — runs daily at {hour:02d}:00")
    elif interval == "monthly":
        scheduler.add_job(run_and_export, "cron", day=1, hour=hour, minute=0)
        logger.info(f"Scheduler started — runs on the 1st of each month at {hour:02d}:00")

    logger.info("Press Ctrl+C to stop.\n")
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Scheduler stopped.")


# ── CLI ───────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="Genetic panel scraper")
    parser.add_argument("--schedule", action="store_true", help="Start scheduler")
    parser.add_argument("--interval", choices=["weekly", "daily", "monthly"], default="weekly")
    parser.add_argument("--day", default="mon", help="Day of week for weekly schedule (mon-sun)")
    parser.add_argument("--hour", type=int, default=6, help="Hour to run (24h, default 6)")
    parser.add_argument("--labs", nargs="+", help="Specific labs to scrape")
    parser.add_argument("--list", action="store_true", help="List available labs")
    args = parser.parse_args()

    if args.list:
        print("\nAvailable labs:")
        for s in ALL_SCRAPERS:
            print(f"  • {s.LAB_NAME}")
        return

    if args.schedule:
        start_scheduler(interval=args.interval, day=args.day, hour=args.hour)
    else:
        path = run_and_export(labs=args.labs)
        if path:
            print(f"\n✅ Done. Output: {path}")


if __name__ == "__main__":
    main()
