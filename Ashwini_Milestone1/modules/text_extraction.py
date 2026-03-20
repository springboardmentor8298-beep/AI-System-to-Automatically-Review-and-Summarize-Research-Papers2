import os
import pdfplumber
import re

def extract_sections(text):
    sections = {
        "Abstract": "",
        "Introduction": "",
        "Results": "",
        "Conclusion": ""
    }

    patterns = {
        "Abstract": r"(abstract)(.*?)(introduction|1\.|$)",
        "Introduction": r"(introduction)(.*?)(method|2\.|$)",
        "Results": r"(result|results)(.*?)(conclusion|$)",
        "Conclusion": r"(conclusion)(.*)"
    }

    text_lower = text.lower()

    for key, pattern in patterns.items():
        match = re.search(pattern, text_lower, re.DOTALL)
        if match:
            sections[key] = match.group(2).strip()

    return sections


def extract_text_from_pdfs(folder="dataset/pdfs"):
    data = {}

    for file in os.listdir(folder):
        if file.endswith(".pdf"):
            path = os.path.join(folder, file)
            text = ""

            try:
                with pdfplumber.open(path) as pdf:
                    for page in pdf.pages:
                        content = page.extract_text()
                        if content:
                            text += content + "\n"

                if not text.strip():
                    text = "This paper discusses important concepts."

                sections = extract_sections(text)
                data[file] = sections

            except Exception as e:
                print(f"Error reading {file}: {e}")

    return data