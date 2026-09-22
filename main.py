import os
import re
import pdfplumber

from reportlab.platypus import (
    SimpleDocTemplate,
    Table,
    TableStyle,
    Paragraph,
)

from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet

INPUT_FOLDER = "input"
OUTPUT_PDF = "Consolidated_Cause_List.pdf"

styles = getSampleStyleSheet()

all_records = []


def clean(txt):
    if not txt:
        return ""

    txt = txt.replace("\n", " ")
    txt = re.sub(r"\s+", " ", txt)
    return txt.strip()


def get_advocate_name(filename):
    return (
        filename.upper()
        .replace(".PDF", "")
        .replace("_", " ")
        .strip()
    )


def extract_pdf_text(pdf_path):
    full_text = ""

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()

            if text:
                full_text += text + "\n"

    return full_text


def extract_cases(text, advocate):

    records = []

    judge = ""
    ch = ""
    list_no = ""
    status = ""

    current = None

    lines = text.split("\n")

    for line in lines:

        line = clean(line)

        if not line:
            continue

        if "THE HON" in line:
            judge = line

        hall_match = re.search(
            r"COURT HALL NO\s*:\s*(\d+)\s*Cause List No\.?\s*(\d+)",
            line,
            re.I
        )

        if hall_match:
            ch = hall_match.group(1)
            list_no = hall_match.group(2)

        if any(x in line.upper() for x in [
            "PRELIMINARY HEARING",
            "HEARING -",
            "ADMISSION",
            "ORDERS",
            "FURTHER HEARING"
        ]):
            status = line

        case_match = re.search(
            r'^\s*(\d+)\s+(WP\s+\d+/\d+|CRL\.?P\s+\d+/\d+)',
            line,
            re.I
        )

        if case_match:

            if current:
                records.append(current)

            current = {
                "item_sl": case_match.group(1),
                "case_no": case_match.group(2),
                "pet": "",
                "res": "",
                "bold_side": "",
                "judge": judge,
                "ch": ch,
                "list": list_no,
                "status": status,
            }

            continue

        if current is None:
            continue

        if "PET:" in line:

            pet_text = line.split("PET:")[1]

            if advocate in pet_text.upper():
                current["bold_side"] = "PET"

            pet_text = pet_text.split(advocate)[0]

            current["pet"] = clean(pet_text)

        if "RES:" in line:

            res_text = line.split("RES:")[1]

            if advocate in res_text.upper():
                current["bold_side"] = "RES"

            res_text = res_text.split(advocate)[0]

            current["res"] = clean(res_text)

    if current:
        records.append(current)

    return records


def build_case_name(r):

    pet = r["pet"]
    res = r["res"]

    if r["bold_side"] == "PET":
        pet = f"<b>{pet}</b>"

    if r["bold_side"] == "RES":
        res = f"<b>{res}</b>"

    return Paragraph(
        f"{pet}<br/>vs<br/>{res}",
        styles["BodyText"]
    )


def generate_pdf(records):

    doc = SimpleDocTemplate(
        OUTPUT_PDF,
        leftMargin=10,
        rightMargin=10,
        topMargin=10,
        bottomMargin=10,
    )

    data = [[
        "SL NO",
        "CASE NUMBER",
        "CASE NAME",
        "CH",
        "LIST",
        "SL NO",
        "STATUS",
        "JUDGES",
    ]]

    for i, r in enumerate(records, start=1):

        data.append([
            str(i),
            Paragraph(
                f"<b>{r['case_no']}</b>",
                styles["BodyText"]
            ),
            build_case_name(r),
            r["ch"],
            r["list"],
            r["item_sl"],
            r["status"],
            r["judge"],
        ])

    table = Table(
        data,
        colWidths=[
            35,
            80,
            220,
            35,
            35,
            35,
            150,
            180,
        ]
    )

    table.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
        ("BACKGROUND", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))

    doc.build([table])


def main():

    for file in os.listdir(INPUT_FOLDER):

        if not file.lower().endswith(".pdf"):
            continue

        advocate = get_advocate_name(file)

        pdf_path = os.path.join(INPUT_FOLDER, file)

        text = extract_pdf_text(pdf_path)

        records = extract_cases(text, advocate)

        all_records.extend(records)

        print(
            f"Processed: {file} -> {len(records)} records"
        )

    generate_pdf(all_records)

    print(
        f"Done. Total records: {len(all_records)}"
    )


if __name__ == "__main__":
    main()
