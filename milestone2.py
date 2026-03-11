import fitz
import os

PAPERS_FOLDER = "papers"
OUTPUT_FOLDER = "outputs"

os.makedirs(OUTPUT_FOLDER, exist_ok=True)


def extract_text_from_pdf(pdf_path):
    """Extract full text from a PDF file."""
    doc = fitz.open(pdf_path)
    text = ""

    for page in doc:
        text += page.get_text()

    return text


def extract_title(text):
    """Assume first non-empty line is the paper title."""
    lines = text.split("\n")
    for line in lines:
        if line.strip():
            return line.strip()
    return "Unknown Title"


def extract_sections(text):
    """Extract abstract and introduction."""
    abstract = ""
    introduction = ""

    upper_text = text.upper()

    try:
        if "ABSTRACT" in upper_text and "INTRODUCTION" in upper_text:
            abstract = upper_text.split("ABSTRACT")[1].split("INTRODUCTION")[0]
    except:
        abstract = "Abstract not found."

    try:
        if "INTRODUCTION" in upper_text:
            introduction = upper_text.split("INTRODUCTION")[1][:1500]
    except:
        introduction = "Introduction not found."

    return abstract, introduction


def extract_key_findings(text):
    """Extract important sentences using keywords."""
    sentences = text.split(".")
    keywords = [
        "machine learning",
        "deep learning",
        "algorithm",
        "model",
        "data",
        "prediction",
        "accuracy",
        "results"
    ]

    findings = []

    for s in sentences:
        for k in keywords:
            if k in s.lower():
                findings.append(s.strip())
                break

    return findings


def process_paper(pdf_file):
    """Process a single research paper."""
    pdf_path = os.path.join(PAPERS_FOLDER, pdf_file)
    text = extract_text_from_pdf(pdf_path)

    title = extract_title(text)
    abstract, introduction = extract_sections(text)
    findings = extract_key_findings(text)

    paper_name = os.path.splitext(pdf_file)[0]
    paper_folder = os.path.join(OUTPUT_FOLDER, paper_name)

    os.makedirs(paper_folder, exist_ok=True)

    # Save outputs
    with open(os.path.join(paper_folder, "full_text.txt"), "w", encoding="utf-8") as f:
        f.write(text)

    with open(os.path.join(paper_folder, "abstract.txt"), "w", encoding="utf-8") as f:
        f.write(abstract)

    with open(os.path.join(paper_folder, "introduction.txt"), "w", encoding="utf-8") as f:
        f.write(introduction)

    with open(os.path.join(paper_folder, "key_findings.txt"), "w", encoding="utf-8") as f:
        for point in findings:
            f.write("• " + point + "\n\n")

    # Print nice console output
    print("\n===================================")
    print("Paper Title :", title)
    print("File Name   :", pdf_file)
    print("-----------------------------------")
    print("✔ Full text extracted")
    print("✔ Abstract & Introduction extracted")
    print("✔ Key findings identified :", len(findings))
    print("Output saved in:", paper_folder)
    print("===================================")


def main():
    pdf_files = [f for f in os.listdir(PAPERS_FOLDER) if f.endswith(".pdf")]

    print("\nResearch Paper Analysis Started")
    print("Total Papers Found:", len(pdf_files))

    for pdf in pdf_files:
        process_paper(pdf)

    print("\nAll papers processed successfully 🎉")


if __name__ == "__main__":
    main()