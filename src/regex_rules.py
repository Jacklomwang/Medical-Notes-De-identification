import re

# Remove ID + uppercase surname/name blocks such as:
# "U-1234567, ODINSSON, ODIN"
REMOVE_PATTERNS = [
    re.compile(
        r"\b[A-Za-z]-?\d{5,}\s*,\s*[A-Z]{2,}\s*,\s*[A-Z]{2,}\b"
    ),
    # Remove ID-like tokens such as R23212, U23112, U-1234567.
    re.compile(r"\b[A-Za-z]-?\d{5,}\b"),
]

PATTERNS = {
    "PHONE": re.compile(r"\b(\+?\d{1,2}[\s-]?)?(\(?\d{3}\)?[\s-]?)\d{3}[\s-]?\d{4}\b"),
    "DATE": re.compile(r"\b\d{4}[-/]\d{2}[-/]\d{2}\b|\b\d{2}[-/]\d{2}[-/]\d{4}\b"),
    "ID": re.compile(r"\b(?:MRN|ID|Patient ID)[:\s]?\d+\b", re.IGNORECASE),
}

def redact_with_regex(text: str) -> str:
    for pattern in REMOVE_PATTERNS:
        text = pattern.sub("", text)

    for label, pattern in PATTERNS.items():
        text = pattern.sub(f"[{label}]", text)

    # Light cleanup after removals.
    text = re.sub(r"[ \t]{2,}", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"\s+,", ",", text)

    return text
