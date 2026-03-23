import os
import json
import fitz  # PyMuPDF


# -------------------------------
# Configuration
# -------------------------------
BASE_DIR = os.path.dirname(__file__)
METADATA_FILE = os.path.normpath(os.path.join(BASE_DIR, "../data/papers_metadata.json"))
OUTPUT_FILE = os.path.normpath(os.path.join(BASE_DIR, "../data/extracted_text.json"))
COMPARISON_FILE = os.path.normpath(os.path.join(BASE_DIR, "../data/comparison.json"))


# -------------------------------
# Utility Functions
# -------------------------------
def load_metadata():
    """Load metadata safely"""
    if os.path.exists(METADATA_FILE):
        with open(METADATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def extract_text_from_pdf(pdf_path):
    """Extract full text from PDF"""
    try:
        doc = fitz.open(pdf_path)
        text = ""
        for page in doc:
            text += page.get_text()
        return text
    except Exception as e:
        print(f"Error reading {pdf_path}: {e}")
        return ""


def split_into_sections(text):
    """Basic section extraction using keyword matching"""
    sections = {
        "abstract": "",
        "introduction": "",
        "methods": "",
        "results": "",
        "conclusion": ""
    }

    lower_text = text.lower()

    for key in sections.keys():
        if key in lower_text:
            start = lower_text.find(key)
            sections[key] = text[start:start + 2000]

    return sections


def extract_key_findings(text):
    """Extract important sentences using keyword heuristics"""
    sentences = text.split(".")
    key_sentences = []

    keywords = [
        "propose", "proposed", "result", "results",
        "achieve", "achieved", "improve", "improved",
        "demonstrate", "demonstrated", "outperform",
        "significant", "conclude", "concluded"
    ]

    for sentence in sentences:
        for word in keywords:
            if word in sentence.lower():
                cleaned = sentence.strip()
                if len(cleaned) > 20:
                    key_sentences.append(cleaned)
                break

    return key_sentences[:5]


def compare_papers(papers):
    """Simple cross-paper comparison"""
    comparison = []

    for paper in papers:
        comparison.append({
            "title": paper["title"],
            "topic": paper["topic"],
            "num_key_findings": len(paper.get("key_findings", [])),
            "sections_detected": [
                sec for sec, content in paper["sections"].items() if content
            ]
        })

    return comparison


# -------------------------------
# Main
# -------------------------------
def main():
    metadata = load_metadata()

    if not metadata:
        print("No metadata found.")
        return

    extracted_data = []

    for paper in metadata:
        raw_path = paper.get("pdf_path")
        if not raw_path:
            continue

        pdf_path = os.path.normpath(os.path.join(BASE_DIR, raw_path))
      
        if not os.path.exists(pdf_path):
            print(f"Skipping (file missing): {pdf_path}")
            continue

        print(f"Extracting text from: {pdf_path}")

        full_text = extract_text_from_pdf(pdf_path)

        if not full_text.strip():
            print(f"Skipping (no extractable text): {pdf_path}")
            continue

        sections = split_into_sections(full_text)
        key_findings = extract_key_findings(full_text)

        extracted_data.append({
            "title": paper.get("title", "Unknown Title"),
            "topic": paper.get("topic", "Unknown Topic"),
            "sections": sections,
            "key_findings": key_findings
        })

    # Save extracted text
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(extracted_data, f, indent=4)

    # Generate comparison
    comparison = compare_papers(extracted_data)

    with open(COMPARISON_FILE, "w", encoding="utf-8") as f:
        json.dump(comparison, f, indent=4)

    print("Milestone 2 completed successfully!")


if __name__ == "__main__":
    main()
