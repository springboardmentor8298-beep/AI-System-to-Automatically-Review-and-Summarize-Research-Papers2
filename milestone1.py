import feedparser
import requests
import os
import re

# Create folder automatically
os.makedirs("data/pdfs", exist_ok=True)


# -------- SEARCH ARXIV --------
def search_arxiv(query, max_results=5):
    query = query.replace(" ", "+")
    url = f"http://export.arxiv.org/api/query?search_query=all:{query}&start=0&max_results={max_results}"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    }

    response = requests.get(url, headers=headers, timeout=30)
    feed = feedparser.parse(response.text)
    return feed.entries


# -------- SAFE FILE NAME --------
def clean_filename(name):
    name = re.sub(r'[\\/*?:"<>|]', "", name)
    name = name.replace(" ", "_")
    return name[:150]


# -------- DOWNLOAD REAL PDF --------
def download_pdf(entry):
    pdf_url = None

    # Find PDF link
    for link in entry.links:
        if "pdf" in link.href:
            pdf_url = link.href
            break

    if not pdf_url:
        print("No PDF:", entry.title)
        return

    # Force proper PDF URL format
    if not pdf_url.endswith(".pdf"):
        pdf_url = pdf_url.replace("abs", "pdf") + ".pdf"

    filename = clean_filename(entry.title) + ".pdf"
    path = os.path.join("data/pdfs", filename)

    try:
        headers = {
            "User-Agent": "Mozilla/5.0",
            "Accept": "application/pdf"
        }

        # STREAM download (IMPORTANT)
        with requests.get(pdf_url, headers=headers, stream=True, timeout=60) as r:

            # Check if server really returned a PDF
            content_type = r.headers.get("Content-Type", "")

            if "pdf" not in content_type:
                print("Skipped (not real PDF):", entry.title)
                return

            with open(path, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)

        print("Downloaded REAL PDF:", filename)

    except Exception as e:
        print("Error:", entry.title, e)


# -------- MAIN --------
if __name__ == "__main__":
    topic = input("Enter research topic: ")

    papers = search_arxiv(topic)

    if not papers:
        print("No papers found.")
    else:
        print("\nDownloading papers...\n")
        for paper in papers:
            print("Title:", paper.title)
            download_pdf(paper)

        print("\nAll done. Check data/pdfs folder.")
