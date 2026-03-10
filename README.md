# Medical Notes De-identification

This repository contains a research-only pipeline for de-identifying clinical narrative text from mixed document inputs and exporting redacted DOCX outputs.

No real patient data is included in this repository.

## Supported Input Formats

The batch pipeline currently accepts files placed in `data/input/` with these extensions:

- `.docx`
- `.pdf`
- `.doc`
- `.wpd`
- `.let`
- `.ltr`

Behavior by format:

- `.docx`: used directly
- `.pdf`: converted to working `.docx`
- `.doc` / `.wpd`: converted through LibreOffice if available
- `.let` / `.ltr`: treated as text-like files and wrapped into `.docx`

Converted working files are written to:

- `data/input/_converted_docx/`

If a file cannot be converted, the batch runner skips it and prints the reason instead of aborting the entire run.

## Current Pipeline (Exact Order)

For each successfully ingested document, the pipeline runs in this order:

1. Input conversion (`input_converter.py`)
- Convert supported input formats into working `.docx` files.
- For PDFs, prefer LibreOffice conversion first.
- If LibreOffice PDF conversion fails, fall back to `pdfplumber`.
- `pdfplumber` PDF handling reconstructs paragraphs using layout heuristics from extracted word positions.

2. Text extraction from DOCX (`run_batch.py`)
- Read visible DOCX paragraphs into internal text rows.

3. Boundary trimming (`clinical_filter.py`)
- Remove everything before the first `Dear`, if present.
- Also remove everything before `*LABORATORY RESULTS` or `**LABORATORY RESULTS`, if present.
- If both a `Dear` marker and a starred `LABORATORY RESULTS` marker exist, trimming starts from the earlier one.
- Remove everything from the first closing line onward.

Closing lines currently include forms such as:
- `Best regards`
- `Kind regards`
- `Regards`
- `Sincerely`
- `Sincerely yours`
- `Yours sincerely`
- `Yours truly`
- `Warm regards`
- `Respectfully`
- `Thank you`

4. Clinical paragraph filtering (`clinical_filter.py`)
- Remove administrative/header-like paragraphs using rule-based filters.
- Examples of filtering signals:
  - phone numbers
  - page markers
  - ID-heavy lines
  - department-style headers
  - field labels such as `subject:`, `dob:`, `re:`

5. i2b2 treatment protection (`clinical_treatment_redactor.py`)
- Use Stanza biomedical `i2b2` NER to detect `TREATMENT` entities.
- Do not replace treatment text with a placeholder.
- Temporarily protect treatment spans with internal tokens.
- Run the later redaction stages.
- Restore the original treatment text unchanged afterward.

6. Regex redaction and removal (`regex_rules.py`)
- Replace:
  - phone numbers -> `[PHONE]`
  - explicit date formats -> `[DATE]`
  - labeled IDs such as `MRN`, `ID`, `Patient ID` -> `[ID]`
- Remove:
  - patterns like `U-1234567, ODINSSON, ODIN`
  - letter-prefixed ID-like tokens with 5+ digits, such as:
    - `R23212`
    - `U23112`
    - `U-1234567`

7. General NER redaction (`ner_redactor.py`)
- Uses Stanza English general NER.
- Active labels currently include:
  - `PERSON`
  - `GPE`
  - `LOC`
  - `DATE`
  - `FAC`
- Known clinical eponyms protected from `PERSON` false positives:
  - `holter`
  - `beighton`
  - `valsava`
- `DATE` entities are skipped and left unchanged if the detected text contains temporal/relative words such as:
  - `old`
  - `year`, `years`
  - `today`, `yesterday`, `tomorrow`
  - `month`, `months`
  - `week`, `weeks`
  - `day`, `days`
  - weekday names
- `FAC` entities with fewer than 3 characters are skipped and left unchanged.

8. PDF post-processing (`text_normalizer.py`)
- For rows whose original source file was a PDF, hard line breaks are normalized after redaction.
- The goal is to reduce visual line-wrap artifacts while preserving likely paragraph structure.

9. Output writing
- Combined CSV:
  - `data/output/letter_redacted.csv`
- Separate DOCX outputs:
  - `data/output/separate_YYYYMMDD_HHMMSS/`

## Project Files

Core scripts:
- `src/run_batch.py` - full batch pipeline from mixed input formats to redacted outputs
- `src/run_redact_csv.py` - run redaction on an existing `data/input/letters.csv`
- `src/export_redacted_separate.py` - export one redacted DOCX per row/file

Core modules:
- `src/input_converter.py` - mixed-format ingestion and conversion to working DOCX
- `src/clinical_filter.py` - boundary trimming and paragraph filtering
- `src/clinical_treatment_redactor.py` - Stanza `i2b2` treatment protection layer
- `src/regex_rules.py` - regex replacement/removal rules
- `src/ner_redactor.py` - general NER redaction rules and exceptions
- `src/text_normalizer.py` - post-redaction normalization for PDF-derived text
- `src/io_csv.py` - CSV I/O helpers

Utilities:
- `src/convert_docx_to_csv.py` - single-file DOCX to CSV helper
- `src/convert_csv_to_docx.py` - CSV to DOCX helper
- `app_streamlit.py` - optional visual demo app

## Setup

From the project root:

```powershell
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

If PowerShell blocks activation:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

If Stanza resources are missing, first run may download them automatically.

For `.doc` / `.wpd` conversion, LibreOffice is recommended.

## One-Command Batch Run

```powershell
.\.venv\Scripts\python src\run_batch.py
```

This command will:

- discover supported input files in `data/input/`
- convert them to working `.docx` where needed
- skip unconvertible files and print the reason
- rebuild `data/input/letters.csv`
- run the full de-identification pipeline
- write `data/output/letter_redacted.csv`
- export separate redacted DOCX outputs

## Manual Run

Redact an existing `data/input/letters.csv`:

```powershell
.\.venv\Scripts\python src\run_redact_csv.py
```

Export separate DOCX outputs from an existing redacted CSV:

```powershell
$ts=Get-Date -Format 'yyyyMMdd_HHmmss'
.\.venv\Scripts\python src\export_redacted_separate.py --redacted-csv data/output/letter_redacted.csv --input-dir data/input --output-dir "data/output/separate_$ts"
```

## Streamlit Demo (Optional)

```powershell
streamlit run app_streamlit.py
```

Use this for an interactive walkthrough of the pipeline stages.

## Notes and Limitations

- This code is for research/prototyping workflows and should be validated before production PHI handling.
- PDF paragraph reconstruction is heuristic. It improves layout preservation but does not recover true original authoring structure perfectly.
- Some legacy `.doc`, `.wpd`, `.let`, or `.ltr` files may still fail depending on encoding, corruption, or converter support.
- NER outputs are model-dependent and can vary by document style.
