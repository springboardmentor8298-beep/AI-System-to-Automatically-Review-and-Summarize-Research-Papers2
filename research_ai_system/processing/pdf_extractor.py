import fitz  # PyMuPDF

def extract_text_from_pdf(pdf_path):
    try:
        doc = fitz.open(pdf_path)
        text = ""

        for page in doc:
            text += page.get_text()

        # Detect bad extraction
        if len(text.strip()) < 500:
            return None

        return text

    except Exception as e:
        print(f"❌ Error reading {pdf_path}: {e}")
        return None