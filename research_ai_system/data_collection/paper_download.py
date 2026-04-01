import requests
import os
import re

DOWNLOAD_DIR = "downloaded_papers"

# 🔥 This line fixes your error
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

def clean_filename(title):
    return re.sub(r'[^a-zA-Z0-9]', '_', title)[:80]

def download_pdf(paper):
    pdf_url = paper["pdf_url"]

    try:
        response = requests.get(pdf_url)

        if response.status_code == 200:
            filename = clean_filename(paper["title"]) + ".pdf"
            filepath = os.path.join(DOWNLOAD_DIR, filename)

            with open(filepath, "wb") as f:
                f.write(response.content)

            print(f"✅ Downloaded: {filename}")
            return filepath

    except Exception as e:
        print(f"❌ Error: {e}")

    return None


def download_papers(papers):
    paths = []

    for paper in papers:
        path = download_pdf(paper)
        if path:
            paths.append(path)

    return paths