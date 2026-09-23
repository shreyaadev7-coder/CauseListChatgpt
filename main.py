import pdfplumber

pdf_file = "Mahesh_Chowdhary.pdf"

with pdfplumber.open(pdf_file) as pdf:
    for i, page in enumerate(pdf.pages):
        print("=" * 80)
        print("PAGE", i + 1)
        print("=" * 80)

        text = page.extract_text()

        if text:
            print(text[:5000])
