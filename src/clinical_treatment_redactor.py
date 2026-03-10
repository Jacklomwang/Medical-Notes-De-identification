import stanza


def load_treatment_pipeline():
    """
    Load Stanza biomedical NER for i2b2 entities.
    This layer is used only to mask TREATMENT mentions.
    """
    # Keep this strictly to tokenize+ner to avoid loading syntactic processors
    # (lemma/pos/depparse), which can fail for some biomedical package combos.
    configs = [
        {
            "lang": "en",
            "package": None,
            "processors": {"tokenize": "default", "ner": "i2b2"},
        },
        {
            "lang": "en",
            "package": "mimic",
            "processors": {"tokenize": "mimic", "ner": "i2b2"},
        },
    ]

    last_error = None
    for cfg in configs:
        for use_gpu in (True, False):
            try:
                return stanza.Pipeline(
                    cfg["lang"],
                    package=cfg["package"],
                    processors=cfg["processors"],
                    use_gpu=use_gpu,
                    verbose=False,
                )
            except Exception as exc:
                last_error = exc

    raise RuntimeError(f"Could not initialize i2b2 treatment pipeline: {last_error}")


def protect_treatment_entities(text: str, nlp):
    doc = nlp(text)

    spans = []
    for ent in doc.entities:
        if ent.type == "TREATMENT":
            spans.append((ent.start_char, ent.end_char, ent.text))

    protected_map = []

    # Replace from back to front to preserve offsets.
    # Tokens are restored after later regex/general-NER passes.
    spans.sort(reverse=True, key=lambda x: x[0])
    for idx, (start, end, original_text) in enumerate(spans, start=1):
        token = f"__TRT_{idx:06d}__"
        text = text[:start] + token + text[end:]
        protected_map.append((token, original_text))

    return text, protected_map


def restore_protected_treatments(text: str, protected_map) -> str:
    for token, original_text in protected_map:
        text = text.replace(token, original_text)
    return text
