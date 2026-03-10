import os

import stanza


# Common clinical eponyms that should NOT be redacted as PERSON
CLINICAL_EPONYMS = {
    "holter",
    "beighton",
    "valsava",   # optional if it ever shows up
}

DATE_SKIP_KEYWORDS = {
    "old",
    "year",
    "years",
    "today",
    "yesterday",
    "tomorrow",
    "month",
    "months",
    "week",
    "weeks",
    "day",
    "days",
    "monday",
    "tuesday",
    "wednesday",
    "thursday",
    "friday",
    "saturday",
    "sunday",
}

GENERAL_LABELS = {"PERSON", "GPE", "LOC","DATE","FAC"}
CLINICAL_I2B2_LABELS = {"PROBLEM", "TEST", "TREATMENT"}

# Active labels are set by load_ner_pipeline(); default remains general behavior.
ACTIVE_REDACT_LABELS = set(GENERAL_LABELS)


def _build_pipeline(mode: str, use_gpu: bool):
    if mode == "clinical_i2b2":
        return stanza.Pipeline(
            "en",
            package="mimic",
            processors={"tokenize": "mimic", "ner": "i2b2"},
            use_gpu=use_gpu,
            verbose=False,
        )

    return stanza.Pipeline(
        "en",
        processors="tokenize,ner",
        use_gpu=use_gpu,
        verbose=False,
    )


def load_ner_pipeline(mode: str | None = None):
    """
    mode:
      - general (default)
      - clinical_i2b2
    You can also set env var NER_MODE to one of these values.
    """
    global ACTIVE_REDACT_LABELS
    selected_mode = (mode or os.getenv("NER_MODE", "general")).strip().lower()

    if selected_mode == "clinical_i2b2":
        ACTIVE_REDACT_LABELS = set(CLINICAL_I2B2_LABELS)
    else:
        selected_mode = "general"
        ACTIVE_REDACT_LABELS = set(GENERAL_LABELS)

    try:
        return _build_pipeline(selected_mode, use_gpu=True)
    except Exception:
        return _build_pipeline(selected_mode, use_gpu=False)

def redact_with_ner(text: str, nlp) -> str:
    doc = nlp(text)

    spans = []
    for ent in doc.entities:
        text_lower = ent.text.lower()

        # Suppress false PERSONs like Holter / Beighton
        if ent.type == "PERSON" and text_lower in CLINICAL_EPONYMS:
            continue

        # Keep relative/clinical temporal wording (e.g., "today", "2 weeks").
        if ent.type == "DATE" and any(k in text_lower for k in DATE_SKIP_KEYWORDS):
            continue

        # Keep very short FAC entities (often noisy false positives).
        if ent.type == "FAC" and len(ent.text.strip()) < 5:
            continue

        if ent.type in ACTIVE_REDACT_LABELS:
            spans.append((ent.start_char, ent.end_char, f"[{ent.type}]"))

    # Replace from back to front to preserve offsets
    spans.sort(reverse=True, key=lambda x: x[0])
    for start, end, label in spans:
        text = text[:start] + label + text[end:]

    return text
