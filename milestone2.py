import os
import fitz
import re
import json

# ==============================
# CONFIG
# ==============================

# Change this path if milestone1 is in another folder
PDF_FOLDER = "papers"

OUTPUT_FILE = "analysis_results.json"

SECTION_HEADERS = [
    "abstract",
    "introduction",
    "method",
    "methodology",
    "methods",
    "results",
    "discussion",
    "conclusion",
]


# ==============================
# PDF TEXT EXTRACTION
# ==============================


def extract_pdf_text(pdf_path):

    doc = fitz.open(pdf_path)

    text = ""

    for page in doc:
        text += page.get_text()

    doc.close()

    return text


# ==============================
# SECTION SEGMENTATION
# ==============================


def segment_sections(text):

    sections = {}

    text_lower = text.lower()

    for header in SECTION_HEADERS:
        pattern = r"\b" + header + r"\b"

        match = re.search(pattern, text_lower)

        if match:
            start = match.start()

            next_start = len(text)

            for other in SECTION_HEADERS:
                if other == header:
                    continue

                next_match = re.search(r"\b" + other + r"\b", text_lower[start + 1 :])

                if next_match:
                    next_start = start + next_match.start()

                    break

            section_text = text[start:next_start]

            sections[header] = section_text.strip()

    return sections


# ==============================
# KEY FINDING EXTRACTION
# ==============================


def extract_key_findings(results_text):

    sentences = re.split(r"\.|\n", results_text)

    key_sentences = []

    keywords = ["improve", "increase", "outperform", "better", "result", "achieve"]

    for s in sentences:
        if len(s.strip()) > 40:
            if any(k in s.lower() for k in keywords):
                key_sentences.append(s.strip())

    return key_sentences[:5]


# ==============================
# ANALYZE SINGLE PAPER
# ==============================


def analyze_paper(pdf_path):

    print("Processing:", pdf_path)

    text = extract_pdf_text(pdf_path)

    sections = segment_sections(text)

    results_text = sections.get("results", "")

    findings = extract_key_findings(results_text)

    return {"pdf": pdf_path, "sections": sections, "key_findings": findings}


# ==============================
# CROSS PAPER COMPARISON
# ==============================


def compare_papers(papers):

    comparison = []

    for p in papers:
        methods = p["sections"].get("method", "")[:200]

        results = p["sections"].get("results", "")[:200]

        comparison.append(
            {"paper": p["pdf"], "method_summary": methods, "result_summary": results}
        )

    return comparison


# ==============================
# GET ALL PDF FILES (SUBFOLDERS)
# ==============================


def get_all_pdfs(folder):

    pdf_files = []

    for root, dirs, files in os.walk(folder):
        for file in files:
            if file.endswith(".pdf"):
                pdf_files.append(os.path.join(root, file))

    return pdf_files


# ==============================
# MAIN PIPELINE
# ==============================


def main():

    pdf_files = get_all_pdfs(PDF_FOLDER)

    if len(pdf_files) == 0:
        print("No PDF files found in folder:", PDF_FOLDER)
        return

    print("Found", len(pdf_files), "PDF files\n")

    papers_analysis = []

    for pdf in pdf_files:
        paper_data = analyze_paper(pdf)

        papers_analysis.append(paper_data)

    comparison = compare_papers(papers_analysis)

    final_data = {"papers": papers_analysis, "comparison": comparison}

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(final_data, f, indent=4)

    print("\nAnalysis complete")
    print("Saved to:", OUTPUT_FILE)


# ==============================
# PROGRAM START
# ==============================

if __name__ == "__main__":
    main()
