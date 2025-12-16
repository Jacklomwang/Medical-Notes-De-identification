import stanza


# Common clinical eponyms that should NOT be redacted as PERSON
CLINICAL_EPONYMS = {
    "holter",
    "beighton",
    "valsava",   # optional if it ever shows up
}

def load_ner_pipeline():
    return stanza.Pipeline(
        "en",
        processors="tokenize,ner",
        use_gpu=True,
        verbose=False
    )

def redact_with_ner(text: str, nlp) -> str:
    doc = nlp(text)

    spans = []
    for ent in doc.entities:
        text_lower = ent.text.lower()

        # Suppress false PERSONs like Holter / Beighton
        if ent.type == "PERSON" and text_lower in CLINICAL_EPONYMS:
            continue

        if ent.type in {"PERSON", "GPE", "LOC"}:
            spans.append((ent.start_char, ent.end_char, f"[{ent.type}]"))

    # Replace from back to front to preserve offsets
    spans.sort(reverse=True, key=lambda x: x[0])
    for start, end, label in spans:
        text = text[:start] + label + text[end:]

    return text
