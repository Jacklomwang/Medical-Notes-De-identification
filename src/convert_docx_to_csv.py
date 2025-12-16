from docx import Document
import csv
from pathlib import Path
from clinical_filter import filter_clinical_paragraphs

INPUT_DOCX = Path("data/input/For Jack Test_original.docx")
OUTPUT_CSV = Path("data/input/letters.csv")

doc = Document(INPUT_DOCX)

# Extract visible text only
paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
kept, removed = filter_clinical_paragraphs(paragraphs)
full_text = "\n".join(kept)


with OUTPUT_CSV.open("w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=["doc_id", "text"])
    writer.writeheader()
    writer.writerow({
        "doc_id": 1,
        "text": full_text
    })

print("Converted DOCX → CSV:", OUTPUT_CSV)
