from semanticscholar import SemanticScholar
from dotenv import load_dotenv
import os
import requests

# Load API Key
load_dotenv()
API_KEY = os.getenv("SEMANTIC_SCHOLAR_API_KEY")
print("API KEY:", API_KEY)
sch = SemanticScholar(api_key=API_KEY) if API_KEY else SemanticScholar()


# Search Papers
import time

import requests

def search_papers(query, limit=5):
    url = "https://api.semanticscholar.org/graph/v1/paper/search"

    params = {
        "query": query,
        "limit": limit,
        "fields": "title,abstract,year,openAccessPdf"
    }

    headers = {}
    if API_KEY:
        headers["x-api-key"] = API_KEY

    try:
        response = requests.get(url, params=params, headers=headers)

        if response.status_code != 200:
            print("API failed:", response.status_code)
            return []

        data = response.json()
        return data.get("data", [])

    except Exception as e:
        print("Request failed:", e)
        return []

# Filter Open Access Papers
def filter_papers(papers, max_papers=3):
    selected = []

    for paper in papers:
        pdf = paper.get("openAccessPdf")

        if pdf and paper.get("abstract"):
            selected.append(paper)

        if len(selected) >= max_papers:
            break

    return selected


# Download PDF
def download_pdf(paper, folder="papers"):
    if not os.path.exists(folder):
        os.makedirs(folder)

    pdf = paper.get("openAccessPdf")
    if not pdf:
        return None

    pdf_url = pdf.get("url")
    if not pdf_url:
        return None

    # Fix arXiv links
    if "arxiv.org/abs/" in pdf_url:
        pdf_url = pdf_url.replace("abs", "pdf") + ".pdf"

    title = paper.get("title", "paper")

    filename = os.path.join(
        folder,
        "".join(c for c in title if c.isalnum() or c == " ")[:50]
        .replace(" ", "_") + ".pdf"
    )

    try:
        print("Downloading:", title)
        print("From:", pdf_url)

        response = requests.get(pdf_url, timeout=20)

        if not response.content.startswith(b"%PDF"):
            print("Skipped (Invalid PDF)")
            return None

        with open(filename, "wb") as f:
            f.write(response.content)

        return filename

    except Exception as e:
        print("Download failed:", e)
        return None


# MAIN
if __name__ == "__main__":

    topic = input("Enter research topic: ").strip()

    if not topic:
        print("No topic entered. Exiting.")
        exit()

    print("\nSearching papers...")
    papers = search_papers(topic)

    print("Total papers fetched:", len(papers))

    if not papers:
        print("No papers found.")
        exit()

    selected_papers = filter_papers(papers, max_papers=10)
    print("Selected open-access papers:", len(selected_papers))

    if not selected_papers:
        print("No downloadable open-access papers found.")
        exit()

    downloaded_files = []

    for paper in selected_papers:
        path = download_pdf(paper)
        if path:
            downloaded_files.append(path)
            print("Downloaded:", path)

        if len(downloaded_files) >= 3:
            break

    if not downloaded_files:
        print("No valid PDFs downloaded.")
        exit()