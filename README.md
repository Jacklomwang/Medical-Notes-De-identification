# Medical Notes De-identification

This repository contains a **research-only pipeline** for de-identifying clinical narrative text.
The goal is to remove personal identifiers while preserving clinically meaningful information.

⚠️ **No real patient data is included in this repository.**

---

## Overview

The pipeline is designed for medical letters, clinic notes, and reports (DOCX / PDF → text),
and follows a multi-stage de-identification strategy combining rule-based filtering and
machine learning.

---

## De-identification Pipeline

1. **Header and Footer Removal**
   - Administrative content such as subject lines, timestamps, IDs, referral blocks,
     and institutional headers are removed prior to AI processing.
   - Only clinically relevant narrative paragraphs are retained.

2. **Named Entity Recognition (NER)**
   - A pretrained Named Entity Recognition model is applied to detect:
     - Personal names
     - Geographic locations
   - Detected entities are replaced with standardized placeholders
     (e.g. `[PERSON]`, `[GPE]`).

3. **Rule-based Corrections**
   - Domain-specific rules correct known NER errors.
   - Clinical terms and tests (e.g. *Holter*, *Beighton score*) are explicitly preserved.
   - This reduces false-positive redactions while maintaining medical meaning.

---

## Project Structure

deid_project/
│
├── src/
│ ├── run_redact_csv.py # Main entry point
│ ├── ner_redactor.py # NER-based redaction logic
│ ├── regex_rules.py # Rule-based patterns (IDs, phones, dates, etc.)
│ ├── io_csv.py # CSV input/output helpers
│ └── config.py # Configuration and constants
│
├── requirements.txt
├── README.md
└── .gitignore



---

## Usage (Example)

```bash
python src/run_redact_csv.py \
    --input letter.csv \
    --output letter_redacted.csv
