import re
from collections import Counter

# Header / form-like metadata (Subject:, DOB:, CC:, etc.)
FIELD_LABELS = [
    "subject:",
    "dob:",
    "ramq:",
    "referring physician:",
    "cc:",
    "from:",
    "to:",
    "re:",
]

PAREN_ID_RE = re.compile(r"\(\s*\d{3,}\s*\)")

# Strong admin / metadata signals
ADMIN_KEYWORDS = [
    "tel",
    "telephone",
    "fax",
    "room",
    "suite",
    "clinic",
    "department",
    "departement",
    "hospital",
    "hopital",
    "university",
    "document type",
    "account",
    "mrn",
    "page",
    "ref",
    "cm:",
    "electronically signed",
    "signed by",
    "address",
    "post code",
    "postal",
    "zip",
]

# Things that often appear in REAL clinical paragraphs
CLINICAL_CUES = [
    "mmhg",
    "bpm",
    "hr",
    "bp",
    "mg",
    "ug",
    "mcg",
    "tid",
    "bid",
    "prn",
    "tilt",
    "valsalva",
    "qsart",
    "sudomotor",
    "cardiovagal",
    "echocardiogram",
    "holter",
    "mast",
    "ankle",
    "upper limb",
    "distal",
    "tachycardia",
]

PHONE_RE = re.compile(r"\b(\+?\d{1,2}[\s-]?)?(\(?\d{3}\)?[\s-]?)\d{3}[\s-]?\d{4}\b")
PAGE_RE = re.compile(r"\bpage\s*\d+\s*(of|/)\s*\d+\b", re.IGNORECASE)
ID_HEAVY_RE = re.compile(r"\b(mrn|account|patient\s*id|id)\b.*\d+", re.IGNORECASE)
DEPT_HEADER_RE = re.compile(
    r"^\s*(departement|department)\b.*\b(neuro|neurosciences|neurology)\b.*$",
    re.IGNORECASE,
)

# Letter boundary rules requested by user:
# 1) remove anything before first "Dear" occurrence
# 2) remove anything from closing line onward.
GREETING_RE = re.compile(r"(?i)\bdear\b")
CLOSING_RE = re.compile(
    r"(?im)^\s*(best regards|kind regards|regards|sincerely|yours sincerely|"
    r"yours truly|warm regards|respectfully|thank you|Sincerely yours)[\s,!.]*$"
)
GREETING_LINE_RE = re.compile(r"(?im)^\s*dear\b")


def _digit_ratio(s: str) -> float:
    digits = sum(ch.isdigit() for ch in s)
    nonspace = sum(not ch.isspace() for ch in s)
    return digits / max(nonspace, 1)


def trim_letter_boundaries(text: str) -> str:
    """
    Remove content outside letter body boundaries:
    - drop everything before the first "Dear"
    - drop everything from a closing line onward
    """
    if not text:
        return text

    trimmed = text

    greeting = GREETING_RE.search(trimmed)
    if greeting:
        trimmed = trimmed[greeting.start() :]

    closing = CLOSING_RE.search(trimmed)
    if closing:
        trimmed = trimmed[: closing.start()]

    return trimmed.strip()


def is_non_clinical(paragraph: str, repetition_counter=None) -> bool:
    raw = paragraph.strip()
    p = raw.lower()

    # Keep greeting/closing lines so boundary trimming can use them later.
    if GREETING_LINE_RE.match(raw) or CLOSING_RE.match(raw):
        return False

    if len(p) < 10:
        return True

    if repetition_counter and repetition_counter[p] > 1:
        return True

    if PHONE_RE.search(p) or PAGE_RE.search(p) or ID_HEAVY_RE.search(p):
        return True

    if DEPT_HEADER_RE.match(p) or (("departement" in p or "department" in p) and len(p) < 120):
        return True

    hits = sum(1 for kw in ADMIN_KEYWORDS if kw in p)
    if hits >= 2 and len(p) < 250:
        return True

    digit_ratio = _digit_ratio(p)
    has_clinical_cue = any(cue in p for cue in CLINICAL_CUES)
    if (digit_ratio > 0.18) and (hits >= 1) and (not has_clinical_cue) and (len(p) < 400):
        return True

    label_hits = sum(1 for lbl in FIELD_LABELS if lbl in p)
    colon_density = p.count(":") / max(len(p), 1)
    if label_hits >= 1 or colon_density > 0.03 or PAREN_ID_RE.search(p):
        return True

    return False


def filter_clinical_paragraphs(paragraphs):
    # First rule: always trim by Dear/closing boundaries before any other filtering.
    body_text = trim_letter_boundaries("\n".join(paragraphs))
    working_paragraphs = [p for p in body_text.split("\n") if p.strip()]

    normalized = [p.strip().lower() for p in working_paragraphs if p.strip()]
    repetition_counter = Counter(normalized)

    kept, removed = [], []
    for para in working_paragraphs:
        if is_non_clinical(para, repetition_counter):
            removed.append(para)
        else:
            kept.append(para)
    return kept, removed
