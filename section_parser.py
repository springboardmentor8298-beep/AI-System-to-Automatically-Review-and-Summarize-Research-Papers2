import re

SECTION_NAMES = [
    "abstract",
    "introduction",
    "method",
    "methodology",
    "experiment",
    "results",
    "discussion",
    "conclusion"
]

def get_sections_from_text(text):

    sections = {}

    for section in SECTION_NAMES:
        pattern = rf"{section}(.+?)(?=\n[A-Z][A-Za-z ]+\n)"
        match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)

        if match:
            sections[section] = match.group(1).strip()

    return sections