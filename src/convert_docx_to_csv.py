import argparse
import csv
from pathlib import Path

from docx import Document

from clinical_filter import filter_clinical_paragraphs


def parse_args():
    parser = argparse.ArgumentParser(
        description="Convert one DOCX clinical note to CSV for de-identification pipeline."
    )
    parser.add_argument(
        "--input-docx",
        type=Path,
        default=Path("data/input/For Jack Test_original.docx"),
        help="Path to input DOCX file",
    )
    parser.add_argument(
        "--output-csv",
        type=Path,
        default=Path("data/input/letters.csv"),
        help="Path to output CSV file",
    )
    parser.add_argument(
        "--doc-id",
        type=int,
        default=1,
        help="Document id to store in the CSV row",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    input_docx = args.input_docx
    output_csv = args.output_csv
    output_csv.parent.mkdir(parents=True, exist_ok=True)

    doc = Document(input_docx)

    # Extract visible text and keep only clinical paragraphs.
    paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
    kept, _removed = filter_clinical_paragraphs(paragraphs)
    full_text = "\n".join(kept)

    with output_csv.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["doc_id", "text"])
        writer.writeheader()
        writer.writerow({"doc_id": args.doc_id, "text": full_text})

    print("Converted DOCX -> CSV:", output_csv)


if __name__ == "__main__":
    main()
