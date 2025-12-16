
import csv
from pathlib import Path
from docx import Document

INPUT_CSV = Path("data/output/letter_redacted.csv")
OUTPUT_DOCX = Path("data/output/letter_redacted.docx")

def main():
    doc = Document()

    with INPUT_CSV.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        for row in reader:
            text = row["redacted_text"]

            # Preserve paragraph structure if present
            for para in text.split("\n"):
                doc.add_paragraph(para)

            # Optional page break between documents
            doc.add_page_break()

    doc.save(OUTPUT_DOCX)
    print("DOCX written to:", OUTPUT_DOCX)

if __name__ == "__main__":
    main()
