def normalize_hard_line_breaks(text: str) -> str:
    """
    Collapse visual line wraps into paragraph text while preserving likely
    paragraph boundaries. Intended for post-redaction cleanup of PDF-derived text.
    """
    paragraphs = []
    current = []
    lines = text.splitlines()

    def starts_new_paragraph(current_line: str, next_line: str) -> bool:
        if not current_line:
            return False

        # Treat completed sentence endings as paragraph boundaries in the
        # PDF cleanup stage, per current project rule.
        if current_line.endswith((".", "!", "?", ":")):
            return True

        if next_line and next_line.startswith(("-", "*")):
            return True

        return False

    for idx, raw_line in enumerate(lines):
        line = raw_line.strip()
        if not line:
            if current:
                paragraphs.append(" ".join(current))
                current = []
            continue

        if current and current[-1].endswith("-"):
            current[-1] = current[-1][:-1] + line
        else:
            current.append(line)

        next_line = ""
        for future in lines[idx + 1 :]:
            stripped = future.strip()
            if stripped:
                next_line = stripped
                break
            next_line = ""
            break

        if next_line and starts_new_paragraph(current[-1], next_line):
            paragraphs.append(" ".join(current))
            current = []

    if current:
        paragraphs.append(" ".join(current))

    return "\n\n".join(paragraphs)
