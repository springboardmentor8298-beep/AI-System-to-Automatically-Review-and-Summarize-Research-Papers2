import fitz  # PyMuPDF
import os


def extract_text_from_pdf(pdf_path):
    """
    Extract text from a single PDF file
    """

    try:
        text = ""

        # open the PDF
        doc = fitz.open(pdf_path)

        # read every page
        for page in doc:
            text += page.get_text()

        doc.close()

        return text

    except Exception as e:
        print(f"⚠ Skipping invalid or corrupted PDF: {pdf_path}")
        print("Reason:", e)
        return None


def extract_all_papers(paper_folder):
    """
    Extract text from all PDF files in the folder
    """

    papers_text = {}

    # check if folder exists
    if not os.path.exists(paper_folder):
        print("❌ Paper folder not found:", paper_folder)
        return papers_text

    # loop through all files
    for file in os.listdir(paper_folder):

        if file.endswith(".pdf"):

            path = os.path.join(paper_folder, file)

            print(f"Extracting text from: {file}")

            text = extract_text_from_pdf(path)

            # store only valid extracted text
            if text and text.strip():
                papers_text[file] = text
            else:
                print(f"⚠ No text extracted from: {file}")

    return papers_text