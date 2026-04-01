import re

def clean_text(text):
    text = re.sub(r"\$.*?\$", "", text)   # remove LaTeX
    text = re.sub(r"\[[0-9]+\]", "", text)  # remove citations
    text = re.sub(r"\s+", " ", text)     # normalize spaces
    return text.strip()