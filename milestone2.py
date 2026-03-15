import os
import re
import pandas as pd
from PyPDF2 import PdfReader

PDF_FOLDER = "data/pdfs"


# -------- EXTRACT TEXT FROM PDF --------
def extract_text_from_pdf(pdf_path):

    reader = PdfReader(pdf_path)

    text = ""

    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            text += page_text

    return text


# -------- EXTRACT SECTIONS --------
def extract_sections(text):

    sections = {}

    abstract = re.search(r'Abstract(.*?)(Introduction)', text, re.S | re.I)
    introduction = re.search(r'Introduction(.*?)(Method|Methods)', text, re.S | re.I)
    methods = re.search(r'(Method|Methods)(.*?)(Result|Results)', text, re.S | re.I)
    results = re.search(r'(Result|Results)(.*?)(Conclusion)', text, re.S | re.I)

    sections["abstract"] = abstract.group(1).strip() if abstract else "Not found"
    sections["introduction"] = introduction.group(1).strip() if introduction else "Not found"
    sections["methods"] = methods.group(2).strip() if methods else "Not found"
    sections["results"] = results.group(2).strip() if results else "Not found"

    return sections


# -------- READ ALL PDFs --------
def read_all_pdfs():

    data = []   # STORE ALL PAPER DATA HERE

    if not os.path.exists(PDF_FOLDER):
        print("PDF folder not found.")
        return

    files = os.listdir(PDF_FOLDER)

    if not files:
        print("No PDFs found.")
        return

    for file in files:

        if file.endswith(".pdf"):

            path = os.path.join(PDF_FOLDER, file)

            print("\n===================================")
            print("Paper:", file)

            text = extract_text_from_pdf(path)

            sections = extract_sections(text)

            print("\nAbstract:\n")
            print(sections["abstract"][:500])

            print("\nIntroduction:\n")
            print(sections["introduction"][:500])

            print("\nMethods:\n")
            print(sections["methods"][:500])

            print("\nResults:\n")
            print(sections["results"][:500])

            # -------- SAVE DATA --------
            data.append({
                "paper": file,
                "abstract": sections["abstract"],
                "introduction": sections["introduction"],
                "methods": sections["methods"],
                "results": sections["results"]
            })

    # -------- CREATE CSV FILE --------
    df = pd.DataFrame(data)

    df.to_csv("paper_sections.csv", index=False)

    print("\n Data saved to paper_sections.csv")


# -------- MAIN --------
if __name__ == "__main__":
    read_all_pdfs()