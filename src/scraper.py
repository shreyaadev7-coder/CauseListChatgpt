from __future__ import annotations

from datetime import date
from pathlib import Path

from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError


class CauseListScraper:
    def __init__(self, page: Page, base_url: str):
        self.page = page
        self.base_url = base_url

    def open(self) -> None:
        self.page.goto(self.base_url, wait_until="domcontentloaded", timeout=60_000)
        self.page.wait_for_load_state("networkidle", timeout=30_000)

    def _select_by_label_or_text(self, label: str, value: str) -> None:
        # First try real <select> labels, then fall back to visible option text.
        try:
            self.page.get_by_label(label, exact=False).select_option(label=value)
            return
        except Exception:
            pass
        selects = self.page.locator("select")
        for i in range(selects.count()):
            sel = selects.nth(i)
            try:
                sel.select_option(label=value)
                return
            except Exception:
                continue
        raise RuntimeError(f"Could not find a select control for {label!r} with value {value!r}")

    def _fill_date(self, target: date) -> None:
        candidates = [
            self.page.get_by_label("Causelist Date", exact=False),
            self.page.locator('input[type="date"]'),
            self.page.locator('input[name*="date" i]'),
            self.page.locator('input[id*="date" i]'),
        ]
        date_string = target.strftime("%d/%m/%Y")
        for locator in candidates:
            try:
                if locator.count() == 0:
                    continue
                loc = locator.first
                loc.fill(date_string)
                return
            except Exception:
                continue
        raise RuntimeError("Could not locate the cause-list date input")

    def apply_filters(self, target: date, advocate_name: str, bench: str, search_by: str) -> None:
        self._select_by_label_or_text("Bench", bench)
        self._fill_date(target)
        self._select_by_label_or_text("Search By", search_by)

        # Advocate input may be labelled "Advocate Name" or simply "Advocate".
        for label in ["Advocate Name", "Advocate"]:
            try:
                loc = self.page.get_by_label(label, exact=False)
                if loc.count():
                    loc.first.fill(advocate_name)
                    return
            except Exception:
                pass
        for selector in ['input[name*="advocate" i]', 'input[id*="advocate" i]']:
            loc = self.page.locator(selector)
            if loc.count():
                loc.first.fill(advocate_name)
                return
        raise RuntimeError("Could not locate Advocate Name input")

    def get_details_html(self) -> str:
        buttons = [
            self.page.get_by_role("button", name="GET DETAILS", exact=False),
            self.page.get_by_text("GET DETAILS", exact=False),
            self.page.locator('input[type="submit"]'),
        ]
        for loc in buttons:
            try:
                if loc.count() == 0:
                    continue
                loc.first.click()
                self.page.wait_for_load_state("networkidle", timeout=30_000)
                return self.page.content()
            except PlaywrightTimeoutError:
                return self.page.content()
            except Exception:
                continue
        raise RuntimeError("Could not locate the GET DETAILS action")

    def download_print_pdf(self, output_dir: Path) -> Path:
        output_dir.mkdir(parents=True, exist_ok=True)
        # Try link/button text commonly used by the site.
        candidates = [
            self.page.get_by_text("PRINT LIST", exact=False),
            self.page.get_by_role("button", name="PRINT LIST", exact=False),
            self.page.get_by_role("link", name="PRINT LIST", exact=False),
        ]
        for loc in candidates:
            try:
                if loc.count() == 0:
                    continue
                with self.page.expect_download(timeout=15_000) as dl_info:
                    loc.first.click()
                download = dl_info.value
                target = output_dir / "cause_list.pdf"
                download.save_as(str(target))
                return target
            except Exception:
                continue
        raise RuntimeError("PRINT LIST did not expose a downloadable PDF")
