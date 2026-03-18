# modules/pdf_search.py
import os
import PyPDF2

def search_pdfs_by_topic(topic, folder="dataset/pdfs"):
    """
    Search all PDFs in folder for a keyword and return top 3 PDFs by frequency.
    """
    results = []

    for filename in os.listdir(folder):
        if filename.endswith(".pdf"):
            file_path = os.path.join(folder, filename)
            try:
                with open(file_path, "rb") as f:
                    reader = PyPDF2.PdfReader(f)
                    text = ""
                    for page in reader.pages:
                        text += page.extract_text() or ""
                    count = text.lower().count(topic.lower())
                    if count > 0:
                        results.append((filename, count))
            except Exception as e:
                print(f"Error reading {filename}: {e}")

    results.sort(key=lambda x: x[1], reverse=True)
    return results[:3]