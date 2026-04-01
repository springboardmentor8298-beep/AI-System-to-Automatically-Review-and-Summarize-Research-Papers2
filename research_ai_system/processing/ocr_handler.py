from pdf2image import convert_from_path
import pytesseract

def extract_text_with_ocr(pdf_path):
    try:
        images = convert_from_path(pdf_path)
        text = ""

        for img in images:
            text += pytesseract.image_to_string(img)

        return text

    except Exception as e:
        print(f"❌ OCR Error: {e}")
        return ""