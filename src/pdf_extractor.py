from __future__ import annotations

from pathlib import Path

import pdfplumber

from .extractor import EXPECTED_HEADERS, CauseRow


def extract_pdf_rows(pdf_path: Path) -> list[CauseRow]:
    rows: list[list[str]] = []
    with pdfplumber.open(str(pdf_path)) as pdf:
        for page in pdf.pages:
            extracted = page.extract_tables()
            for table in extracted:
                for row in table:
                    if row:
                        rows.append([(cell or "").strip().replace("\n", " ") for cell in row])

    # Locate the header and then normalize subsequent rows to the exact 8-column schema.
    header_idx = None
    for i, row in enumerate(rows):
        joined = " | ".join(c.upper() for c in row)
        if all(x in joined for x in ["CASE NUMBER", "CASE NAME", "STATUS", "JUDGES"]):
            header_idx = i
            break

    if header_idx is None:
        return []

    out: list[CauseRow] = []
    for row in rows[header_idx + 1 :]:
        if not any(row):
            continue
        # PDF extraction can split one logical row across columns; keep the fixed schema.
        if len(row) < 8:
            row = row + [""] * (8 - len(row))
        if len(row) > 8:
            row = row[:8]
        if row[0].strip().upper() == "SL NO":
            continue
        out.append(CauseRow(row))
    return out
