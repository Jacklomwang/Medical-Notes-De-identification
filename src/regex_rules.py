import re

PATTERNS = {
    "PHONE": re.compile(r"\b(\+?\d{1,2}[\s-]?)?(\(?\d{3}\)?[\s-]?)\d{3}[\s-]?\d{4}\b"),
    "DATE": re.compile(r"\b\d{4}[-/]\d{2}[-/]\d{2}\b|\b\d{2}[-/]\d{2}[-/]\d{4}\b"),
    "ID": re.compile(r"\b(?:MRN|ID|Patient ID)[:\s]?\d+\b", re.IGNORECASE),
}

def redact_with_regex(text: str) -> str:
    for label, pattern in PATTERNS.items():
        text = pattern.sub(f"[{label}]", text)
    return text
