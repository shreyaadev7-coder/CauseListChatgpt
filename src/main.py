from __future__ import annotations

import os
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

from .config import load_settings
from .date_utils import target_date
from .excel_writer import write_excel
from .extractor import extract_html_tables, find_cause_table, rows_from_table
from .pdf_extractor import extract_pdf_rows
from .scraper import CauseListScraper


ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "output" / "raw"
OUT_DIR = ROOT / "output"


def main() -> int:
    settings = load_settings()
    tomorrow = target_date(settings.days_ahead)
    output_xlsx = OUT_DIR / f"cause_list_{tomorrow:%Y-%m-%d}.xlsx"

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 1100})
        scraper = CauseListScraper(page, settings.website_url)
        try:
            scraper.open()
            scraper.apply_filters(
                tomorrow,
                settings.advocate_name,
                settings.bench,
                settings.search_by,
            )

            html = scraper.get_details_html()
            (RAW_DIR / f"result_{tomorrow:%Y-%m-%d}.html").parent.mkdir(parents=True, exist_ok=True)
            (RAW_DIR / f"result_{tomorrow:%Y-%m-%d}.html").write_text(html, encoding="utf-8")

            rows = rows_from_table(find_cause_table(extract_html_tables(html)) or [])

            if not rows:
                # Fallback: print/download PDF if Get Details did not expose a parseable table.
                try:
                    pdf_path = scraper.download_print_pdf(RAW_DIR)
                    rows = extract_pdf_rows(pdf_path)
                except Exception as exc:
                    raise RuntimeError(
                        "The result page did not contain a parseable 8-column cause-list table "
                        "and the PRINT LIST PDF could not be downloaded. "
                        "The site selectors/flow need a one-time calibration."
                    ) from exc

            if not rows:
                if settings.no_cases_action == "fail":
                    raise RuntimeError("No cause-list rows found for the target date and advocate.")
                return 0

            write_excel(rows, tomorrow, output_xlsx)
            print(f"Created: {output_xlsx}")
            print(f"Rows: {len(rows)}")
            return 0
        finally:
            browser.close()


if __name__ == "__main__":
    raise SystemExit(main())
