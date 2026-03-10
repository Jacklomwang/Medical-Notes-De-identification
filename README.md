# Medical Notes De-identification

This repository contains a research-only pipeline for de-identifying clinical narrative text from DOCX letters.

No real patient data is included in this repository.

## Current Pipeline (Exact Order)

For each input letter, the pipeline runs in this order:

1. Letter boundary trimming (`clinical_filter.py`)
- Remove everything before the first `Dear` (if `Dear` exists).
- Remove everything from closing lines onward (e.g., `Best regards`, `Sincerely`, `Yours truly`, etc.).

2. Clinical paragraph filtering (`clinical_filter.py`)
- Remove administrative/header-like content using rule-based filters.

3. i2b2 treatment detection and protection (`clinical_treatment_redactor.py`)
- Detect `TREATMENT` entities using Stanza biomedical model (`i2b2`).
- Do not redact treatment text.
- Temporarily protect treatment spans with internal tokens so later regex/general NER cannot change them.
- Restore original treatment text after later stages.

4. Regex-based redaction (`regex_rules.py`)
- Replace:
  - Phone -> `[PHONE]`
  - Date patterns (`YYYY-MM-DD`, `DD/MM/YYYY`, etc.) -> `[DATE]`
  - ID labels (`MRN`, `ID`, `Patient ID`) -> `[ID]`
- Remove:
  - `LETTER+digits, UPPERCASE, UPPERCASE` patterns (example: `U-1234567, ODINSSON, ODIN`)
  - Letter-prefixed ID-like tokens with 5+ digits (examples: `R23212`, `U23112`, `U-1234567`)

5. General NER redaction (`ner_redactor.py`)
- Uses Stanza English general NER.
- Active labels currently include: `PERSON`, `GPE`, `LOC`, `DATE`, `FAC`.
- Known clinical eponyms are protected from `PERSON` false positives: `holter`, `beighton`, `valsava`.
- `DATE` entities are skipped (not redacted) if they include temporal words such as:
  - `old`, `year(s)`, `today`, `yesterday`, `tomorrow`, `month(s)`, `week(s)`, `day(s)`, weekdays.
- `FAC` entities with fewer than 3 characters are skipped.

6. Output writing
- `letter_redacted.csv` is produced.
- Optional separate redacted DOCX files are produced (one per source file).

## Project Files

Core scripts:
- `src/run_batch.py` - one-command full batch pipeline
- `src/run_redact_csv.py` - run redaction on existing `data/input/letters.csv`
- `src/export_redacted_separate.py` - export one redacted DOCX per row/file

Core modules:
- `src/clinical_filter.py` - boundary trimming + paragraph filtering
- `src/clinical_treatment_redactor.py` - i2b2 treatment detection/protection
- `src/regex_rules.py` - regex replacement/removal rules
- `src/ner_redactor.py` - general NER redaction rules/exceptions
- `src/io_csv.py` - CSV I/O helpers

Utilities:
- `src/convert_docx_to_csv.py` - single-file DOCX -> CSV helper
- `src/convert_csv_to_docx.py` - CSV -> DOCX helper
- `app_streamlit.py` - optional visual demo app

## Setup

From project root:

```powershell
cd deid_project
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

If Stanza resources are missing, first run may download them automatically.

## One-Command Batch Run (Recommended)

```powershell
.\.venv\Scripts\python src\run_batch.py
```

This command will:
- Rebuild `data/input/letters.csv` from all `data/input/*.docx`
- Run full de-identification
- Write `data/output/letter_redacted.csv`
- Create separate files in `data/output/separate_YYYYMMDD_HHMMSS/`

## Manual Run (Step-by-Step)

1. Run redaction from existing CSV:

```powershell
.\.venv\Scripts\python src\run_redact_csv.py
```

2. Export separate DOCX files:

```powershell
$ts=Get-Date -Format 'yyyyMMdd_HHmmss'
.\.venv\Scripts\python src\export_redacted_separate.py --redacted-csv data/output/letter_redacted.csv --input-dir data/input --output-dir "data/output/separate_$ts"
```

## Streamlit Demo (Optional)

```powershell
streamlit run app_streamlit.py
```

Use this for interactive walkthrough of stages for presentation/demo purposes.

## Notes

- This code is for research/prototyping workflows and should be validated before production PHI handling.
- NER outputs are model-dependent and can vary by document style.
