import argparse
import csv
from pathlib import Path

from docx import Document


def parse_args():
    parser = argparse.ArgumentParser(
        description="Export one redacted DOCX per row using source DOCX filenames."
    )
    parser.add_argument(
        "--redacted-csv",
        type=Path,
        default=Path("data/output/letter_redacted.csv"),
        help="CSV with columns: doc_id, redacted_text",
    )
    parser.add_argument(
        "--input-dir",
        type=Path,
        default=Path("data/input"),
        help="Directory containing original DOCX files used for doc_id mapping",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("data/output/separate"),
        help="Directory to write separate redacted DOCX files",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    source_docx_files = sorted(args.input_dir.glob("*.docx"))
    if not source_docx_files:
        raise FileNotFoundError(f"No DOCX files found in: {args.input_dir}")

    with args.redacted_csv.open("r", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    if not rows:
        raise ValueError(f"No rows found in: {args.redacted_csv}")

    for row in rows:
        doc_id = int(row["doc_id"])
        if doc_id < 1 or doc_id > len(source_docx_files):
            raise IndexError(
                f"doc_id {doc_id} is out of range for {len(source_docx_files)} source files."
            )

        source_name = source_docx_files[doc_id - 1].stem
        output_path = args.output_dir / f"{source_name}_redacted.docx"

        doc = Document()
        text = row.get("redacted_text", "")
        for para in text.split("\n"):
            doc.add_paragraph(para)
        doc.save(output_path)
        print(f"Wrote: {output_path}")


if __name__ == "__main__":
    main()
