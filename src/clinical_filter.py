import re
from collections import Counter
# Header / form-like metadata (Subject:, DOB:, CC:, etc.)
FIELD_LABELS = [
    "subject:", "dob:", "ramq:", "referring physician:",
    "cc:", "from:", "to:"
]

PAREN_ID_RE = re.compile(r"\(\s*\d{3,}\s*\)")

# Strong admin / metadata signals
ADMIN_KEYWORDS = [
    "tel", "telephone", "fax", "room", "suite",
    "clinic", "department", "département",
    "hospital", "hôpital", "university",
    "document type", "account", "mrn",
    "page", "ref", "cm:",
    "electronically signed", "signed by",
    "address", "post code", "postal", "zip",
]

# Things that often appear in REAL clinical paragraphs (do NOT remove just because of digits)
CLINICAL_CUES = [
    "mmhg", "bpm", "hr", "bp", "mg", "ug", "mcg", "tid", "bid", "prn",
    "tilt", "valsalva", "qsart", "sudomotor", "cardiovagal", "echocardiogram",
    "holter", "mast", "ankle", "upper limb", "distal", "tachycardia",
]

PHONE_RE = re.compile(r"\b(\+?\d{1,2}[\s-]?)?(\(?\d{3}\)?[\s-]?)\d{3}[\s-]?\d{4}\b")
PAGE_RE  = re.compile(r"\bpage\s*\d+\s*(of|/)\s*\d+\b", re.IGNORECASE)

# e.g., MRN 1234567, account # 3004090169
ID_HEAVY_RE = re.compile(r"\b(mrn|account|patient\s*id|id)\b.*\d+", re.IGNORECASE)

# Standalone header-like lines such as:
# "Département de Neurosciences     Department of Neurosciences"
DEPT_HEADER_RE = re.compile(
    r"^\s*(département|department)\b.*\b(neuro|neurosciences|neurology)\b.*$",
    re.IGNORECASE
)

def _digit_ratio(s: str) -> float:
    digits = sum(ch.isdigit() for ch in s)
    nonspace = sum(not ch.isspace() for ch in s)
    return digits / max(nonspace, 1)

def is_non_clinical(paragraph: str, repetition_counter=None) -> bool:
    raw = paragraph.strip()
    p = raw.lower()

    # Empty/trivial lines
    if len(p) < 10:
        return True

    # Repeated boilerplate across document
    if repetition_counter and repetition_counter[p] > 1:
        return True

    # Very strong non-clinical signals
    if PHONE_RE.search(p) or PAGE_RE.search(p) or ID_HEAVY_RE.search(p):
        return True

    # Remove standalone department headers (your specific failure case)
    # Also remove if it's short and looks like a bilingual header line
    if DEPT_HEADER_RE.match(p) or (("département" in p or "department" in p) and len(p) < 120):
        return True

    # Keyword density rule (keep as a general admin detector)
    hits = sum(1 for kw in ADMIN_KEYWORDS if kw in p)
    if hits >= 2 and len(p) < 250:
        return True

    # Digit rule: DO NOT delete clinical paragraphs just because they contain 3-digit numbers
    # Only treat digit-heavy paragraphs as non-clinical if:
    #   - they look admin-ish (keyword hits), AND
    #   - digit ratio is high, AND
    #   - they do NOT have obvious clinical cues
    digit_ratio = _digit_ratio(p)
    
    has_clinical_cue = any(cue in p for cue in CLINICAL_CUES)

    if (digit_ratio > 0.18) and (hits >= 1) and (not has_clinical_cue) and (len(p) < 400):
        return True
        # ---- Header / form-style metadata block ----
    label_hits = sum(1 for lbl in FIELD_LABELS if lbl in p)

    colon_density = p.count(":") / max(len(p), 1)

    if (
        label_hits >= 2 or
        colon_density > 0.03 or
        PAREN_ID_RE.search(p)
    ):
        return True

    return False

def filter_clinical_paragraphs(paragraphs):
    normalized = [p.strip().lower() for p in paragraphs if p.strip()]
    repetition_counter = Counter(normalized)

    kept, removed = [], []
    for para in paragraphs:
        if is_non_clinical(para, repetition_counter):
            removed.append(para)
        else:
            kept.append(para)
    return kept, removed
