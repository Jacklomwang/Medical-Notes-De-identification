from pathlib import Path
from regex_rules import redact_with_regex
from ner_redactor import load_ner_pipeline, redact_with_ner
from io_csv import read_csv, write_csv
from tqdm import tqdm

INPUT_CSV = Path("data/input/letters.csv")
OUTPUT_CSV = Path("data/output/letter_redacted.csv")

def main():
    rows = read_csv(INPUT_CSV)
    nlp = load_ner_pipeline()

    output_rows = []

    for row in tqdm(rows, desc="Redacting"):
        text = row["text"]
        text = redact_with_regex(text)
        text = redact_with_ner(text, nlp)

        output_rows.append({
            "doc_id": row["doc_id"],
            "redacted_text": text
        })

    write_csv(
        OUTPUT_CSV,
        output_rows,
        fieldnames=["doc_id", "redacted_text"]
    )

    print("Redaction complete:", OUTPUT_CSV)

if __name__ == "__main__":
    main()
