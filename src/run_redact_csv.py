from pathlib import Path
from regex_rules import redact_with_regex
from ner_redactor import load_ner_pipeline, redact_with_ner
from clinical_treatment_redactor import (
    load_treatment_pipeline,
    protect_treatment_entities,
    restore_protected_treatments,
)
from io_csv import read_csv, write_csv
from clinical_filter import trim_letter_boundaries
from text_normalizer import normalize_hard_line_breaks
from tqdm import tqdm

INPUT_CSV = Path("data/input/letters.csv")
OUTPUT_CSV = Path("data/output/letter_redacted.csv")

def main():
    rows = read_csv(INPUT_CSV)
    treatment_nlp = load_treatment_pipeline()
    nlp = load_ner_pipeline(mode="general")

    output_rows = []

    for row in tqdm(rows, desc="Redacting"):
        text = row["text"]
        text = trim_letter_boundaries(text)
        text, protected_map = protect_treatment_entities(text, treatment_nlp)
        text = redact_with_regex(text)
        text = redact_with_ner(text, nlp)
        text = restore_protected_treatments(text, protected_map)
        if Path(row.get("source_file", "")).suffix.lower() == ".pdf":
            text = normalize_hard_line_breaks(text)

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
