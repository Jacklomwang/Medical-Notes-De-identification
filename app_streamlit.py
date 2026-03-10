from __future__ import annotations

import csv
import io
import re
from pathlib import Path

import streamlit as st
from docx import Document

from src.clinical_filter import filter_clinical_paragraphs
from src.ner_redactor import load_ner_pipeline, redact_with_ner
from src.regex_rules import redact_with_regex

TAG_RE = re.compile(r"\[(PHONE|DATE|ID|PERSON|GPE|LOC|ORG)\]")
DEFAULT_SAMPLE_PATH = Path("data/input/letters.csv")


def count_tags(text: str) -> dict[str, int]:
    counts = {k: 0 for k in ["PHONE", "DATE", "ID", "PERSON", "GPE", "LOC", "ORG"]}
    for tag in TAG_RE.findall(text):
        counts[tag] += 1
    return counts


def parse_docx_bytes(raw: bytes) -> str:
    doc = Document(io.BytesIO(raw))
    paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
    return "\n".join(paragraphs)


def parse_csv_bytes(raw: bytes) -> str:
    stream = io.StringIO(raw.decode("utf-8"))
    reader = csv.DictReader(stream)
    rows = list(reader)
    if not rows:
        return ""
    first = rows[0]
    if "text" in first:
        return first["text"]
    return next(iter(first.values()), "")


def load_sample_text() -> str:
    if not DEFAULT_SAMPLE_PATH.exists():
        return ""
    with DEFAULT_SAMPLE_PATH.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        row = next(reader, None)
        if not row:
            return ""
        return row.get("text", "")


@st.cache_resource
def get_nlp():
    return load_ner_pipeline()


st.set_page_config(page_title="Clinical De-identification Demo", layout="wide")
st.title("Clinical Notes De-identification Demo")
st.caption("Research-only visual walkthrough for doctor-facing pipeline demonstration")

with st.sidebar:
    st.header("Pipeline Controls")
    use_filter = st.checkbox("Apply Clinical Paragraph Filter", value=True)
    use_regex = st.checkbox("Apply Regex Redaction", value=True)
    use_ner = st.checkbox("Apply NER Redaction", value=True)
    use_sample = st.checkbox("Use sample from data/input/letters.csv", value=False)
    st.divider()
    st.write(
        "Tip: Start with a short letter to keep the demo fast and easy to explain live."
    )

text = ""
if use_sample:
    text = load_sample_text()

uploaded_docx = st.file_uploader("Upload DOCX note", type=["docx"])
uploaded_csv = st.file_uploader("Upload CSV note", type=["csv"])

if uploaded_docx is not None:
    text = parse_docx_bytes(uploaded_docx.getvalue())
elif uploaded_csv is not None:
    text = parse_csv_bytes(uploaded_csv.getvalue())

text = st.text_area(
    "Or paste clinical text directly",
    value=text,
    height=220,
    placeholder="Paste raw clinical narrative here...",
)

if not text.strip():
    st.info("Provide text (paste/upload/sample) to run the visualization.")
    st.stop()

stage_input = text
stage_filter = stage_input
removed = []

if use_filter:
    paragraphs = [p for p in stage_input.split("\n") if p.strip()]
    kept, removed = filter_clinical_paragraphs(paragraphs)
    stage_filter = "\n".join(kept)

stage_regex = redact_with_regex(stage_filter) if use_regex else stage_filter

if use_ner:
    with st.spinner("Loading NER model and redacting..."):
        nlp = get_nlp()
        stage_final = redact_with_ner(stage_regex, nlp)
else:
    stage_final = stage_regex

count_input = count_tags(stage_input)
count_final = count_tags(stage_final)

col1, col2, col3 = st.columns(3)
col1.metric("Input Characters", len(stage_input))
col2.metric("Output Characters", len(stage_final))
col3.metric("Removed Paragraphs", len(removed) if use_filter else 0)

st.subheader("Stage-by-Stage View")
t1, t2, t3, t4 = st.tabs(
    ["1) Raw Input", "2) After Clinical Filter", "3) After Regex", "4) Final Output"]
)

with t1:
    st.text_area("Raw", value=stage_input, height=350, disabled=True)

with t2:
    st.text_area("Filtered", value=stage_filter, height=350, disabled=True)
    if removed:
        with st.expander("Show removed paragraphs"):
            for item in removed:
                st.write(f"- {item}")

with t3:
    st.text_area("Regex", value=stage_regex, height=350, disabled=True)

with t4:
    st.text_area("Final", value=stage_final, height=350, disabled=True)

st.subheader("Detected Placeholder Counts")
metric_cols = st.columns(7)
labels = ["PHONE", "DATE", "ID", "PERSON", "GPE", "LOC", "ORG"]
for idx, label in enumerate(labels):
    delta = count_final[label] - count_input[label]
    metric_cols[idx].metric(label, count_final[label], delta=delta)

st.download_button(
    "Download Redacted Text",
    data=stage_final.encode("utf-8"),
    file_name="redacted_note.txt",
    mime="text/plain",
)
