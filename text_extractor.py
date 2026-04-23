from pdfminer.high_level import extract_text
from pathlib import Path

def extract_pdf_text(pdf_path):
    try:
        pdf_file = Path(pdf_path)
        text = extract_text(pdf_file)
        return text
    except Exception as error:
        print(f"Error extracting text from {pdf_path}: {error}")
        return ""