from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from bs4 import BeautifulSoup


EXPECTED_HEADERS = [
    "SL NO",
    "CASE NUMBER",
    "CASE NAME",
    "CH",
    "LIST NO",
    "SL NO",
    "STATUS",
    "JUDGES",
]


@dataclass
class CauseRow:
    values: list[str]


def _clean(value: str) -> str:
    return " ".join(value.replace("\xa0", " ").split())


def extract_html_tables(html: str) -> list[list[str]]:
    soup = BeautifulSoup(html, "lxml")
    tables: list[list[str]] = []
    for table in soup.find_all("table"):
        rows = []
        for tr in table.find_all("tr"):
            cells = tr.find_all(["th", "td"])
            if not cells:
                continue
            rows.append([_clean(c.get_text(" ", strip=True)) for c in cells])
        if rows:
            tables.append(rows)
    return tables


def find_cause_table(tables: Iterable[list[list[str]]]) -> list[list[str]] | None:
    expected = [h.upper() for h in EXPECTED_HEADERS]
    for rows in tables:
        for i, row in enumerate(rows):
            normalized = [c.upper() for c in row]
            # The site may wrap or split header text, so compare the sequence loosely.
            if len(normalized) >= 8 and normalized[:8] == expected:
                return rows[i:]
            joined = " | ".join(normalized)
            if all(h in joined for h in expected):
                return rows[i:]
    return None


def rows_from_table(table_rows: list[list[str]]) -> list[CauseRow]:
    if not table_rows:
        return []
    data: list[CauseRow] = []
    header_index = None
    for i, row in enumerate(table_rows):
        if len(row) >= 8:
            u = [c.upper() for c in row]
            if u[:8] == [h.upper() for h in EXPECTED_HEADERS]:
                header_index = i
                break
            joined = " | ".join(u)
            if all(h in joined for h in ["CASE NUMBER", "CASE NAME", "STATUS", "JUDGES"]):
                header_index = i
                break
    if header_index is None:
        return []

    for row in table_rows[header_index + 1 :]:
        if not any(row):
            continue
        if len(row) < 8:
            row = row + [""] * (8 - len(row))
        elif len(row) > 8:
            # Keep the first 8 table columns; this is intentionally strict because
            # the requested output schema must not gain new columns.
            row = row[:8]
        # Ignore obvious repeated headers.
        if row[0].strip().upper() == "SL NO":
            continue
        data.append(CauseRow([_clean(c) for c in row]))
    return data
