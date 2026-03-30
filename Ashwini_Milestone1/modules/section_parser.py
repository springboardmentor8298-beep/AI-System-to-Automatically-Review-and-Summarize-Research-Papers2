import re

def split_into_sections(text):
    sections = {}

    # Simple pattern for common headings
    patterns = ["abstract", "introduction", "method", "results", "conclusion"]

    for section in patterns:
        match = re.search(section + "(.*?)(?=\n[A-Z])", text, re.IGNORECASE | re.DOTALL)
        if match:
            sections[section] = match.group(1).strip()

    return sections