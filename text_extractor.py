import fitz
import os
import re
import json

PAPERS_FOLDER = "papers"
OUTPUT_FOLDER = "analysis_results"

os.makedirs(OUTPUT_FOLDER, exist_ok=True)


# -------- TEXT CLEANING --------
def clean_text(text):

    text = text.replace("\n", " ")
    text = re.sub(r"\s+", " ", text)

    return text.strip()


# -------- TEXT EXTRACTION --------
def extract_text(pdf_path):

    try:
        doc = fitz.open(pdf_path)

        text = ""

        for page in doc:
            text += page.get_text()

        return clean_text(text)

    except Exception as e:

        print("Skipping file:", pdf_path)
        print("Error:", e)

        return None


# -------- SECTION EXTRACTION --------
def extract_sections(text):

    sections = {}

    patterns = {
        "Abstract": r"Abstract(.*?)(Introduction)",
        "Introduction": r"Introduction(.*?)(Method|Methods)",
        "Methods": r"(Method|Methods)(.*?)(Results)",
        "Results": r"Results(.*?)(Conclusion)",
        "Conclusion": r"Conclusion(.*)"
    }

    for section, pattern in patterns.items():

        match = re.search(pattern, text, re.S | re.I)

        if match:
            section_text = match.group(1).strip()

            # keep only first 300 characters
            sections[section] = section_text[:300]

    return sections


# -------- KEY FINDINGS EXTRACTION --------
def extract_key_findings(text):

    sentences = re.split(r"[.!?]", text)

    keywords = ["result", "improve", "performance", "accuracy", "increase"]

    findings = []

    for sentence in sentences:

        sentence = sentence.strip()

        if len(sentence) < 40:
            continue

        for word in keywords:

            if word in sentence.lower():

                findings.append(sentence[:150])
                break

    return findings[:3]


# -------- SAVE JSON --------
def save_json(data, filename):

    json_name = filename.replace(".pdf", ".json")

    path = os.path.join(OUTPUT_FOLDER, json_name)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

    print("Saved JSON:", path)


# -------- CROSS PAPER SUMMARY --------
def compare_papers(stored_papers):

    print("\n==============================")
    print("RESEARCH INSIGHTS SUMMARY")
    print("==============================\n")

    for paper in stored_papers:

        print("Paper:", paper["paper"])

        for finding in paper["findings"]:
            print(" •", finding)

        print()


# -------- MAIN PROCESS --------
def process_all_papers():

    stored_papers = []

    for file in os.listdir(PAPERS_FOLDER):

        if file.endswith(".pdf"):

            path = os.path.join(PAPERS_FOLDER, file)

            print("\nProcessing:", file)

            text = extract_text(path)

            if text:

                sections = extract_sections(text)

                findings = extract_key_findings(text)

                print("\nSections Extracted:")
                for sec in sections:
                    print(" -", sec)

                print("\nKey Findings:")
                for f in findings:
                    print(" •", f)

                paper_data = {
                    "paper": file,
                    "sections": sections,
                    "findings": findings
                }

                stored_papers.append(paper_data)

                save_json(paper_data, file)

    compare_papers(stored_papers)


# -------- RUN PROGRAM --------
if __name__ == "__main__":
    process_all_papers()