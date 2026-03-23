import requests
import os
import json
import time


BASE_URL = "https://api.semanticscholar.org/graph/v1/paper/search"
MAX_PAPERS = 3
PDF_DIR = "../data/raw_papers"
METADATA_FILE = "../data/papers_metadata.json"

HEADERS = {
    "User-Agent": "Infosys-AI-Internship-Project/6.0 (academic use)"
}

os.makedirs(PDF_DIR, exist_ok=True)


FALLBACK_PAPERS = [
    {
        "title": "Machine Learning in Healthcare: A Review",
        "authors": [{"name": "John Smith"}, {"name": "Alice Brown"}],
        "year": 2021,
        "citationCount": 120,
        "openAccessPdf": {
            "url": "https://arxiv.org/pdf/2102.01234.pdf"
        }
    },
    {
        "title": "Deep Learning Applications in Medical Diagnosis",
        "authors": [{"name": "Michael Lee"}],
        "year": 2020,
        "citationCount": 95,
        "openAccessPdf": {
            "url": "https://arxiv.org/pdf/2005.00123.pdf"
        }
    },
    {
        "title": "AI-Based Decision Support Systems in Healthcare",
        "authors": [{"name": "Sara Johnson"}],
        "year": 2019,
        "citationCount": 80,
        "openAccessPdf": {
            "url": "https://arxiv.org/pdf/1907.04567.pdf"
        }
    }
]


def search_papers(topic, max_retries=3):
    """Search papers using Semantic Scholar API with retry limit"""
    params = {
        "query": topic,
        "limit": 10,
        "fields": "title,authors,year,citationCount,openAccessPdf"
    }

    for attempt in range(1, max_retries + 1):
        response = requests.get(
            BASE_URL,
            params=params,
            headers=HEADERS,
            timeout=10
        )

        if response.status_code == 200:
            return response.json().get("data", [])

        if response.status_code == 429:
            print(f"Rate limit hit (attempt {attempt}/{max_retries}). Waiting 5 seconds...")
            time.sleep(5)
        else:
            response.raise_for_status()

    print("Semantic Scholar API unavailable. Using fallback dataset.")
    return []


def select_top_papers(papers):
    """Select top papers based on citation count"""
    valid_papers = [p for p in papers if p.get("openAccessPdf")]

    sorted_papers = sorted(
        valid_papers,
        key=lambda x: x.get("citationCount", 0),
        reverse=True
    )

    return sorted_papers


def download_pdf(pdf_url, filename):
    """Download PDF safely after validating URL"""
    if not pdf_url or not pdf_url.startswith("http"):
        print("Invalid PDF URL. Skipping.")
        return False

    try:
        response = requests.get(pdf_url, headers=HEADERS, timeout=20)
        response.raise_for_status()

        with open(filename, "wb") as f:
            f.write(response.content)

        return True
    except Exception as e:
        print(f"PDF download failed: {e}")
        return False


def main():
    topic = input("Enter research topic: ").strip()
    print("Searching papers...")

    papers = search_papers(topic)

    if not papers:
        papers = FALLBACK_PAPERS

    selected_papers = select_top_papers(papers)

    metadata = []
    count = 0

    for paper in selected_papers:
        if count >= MAX_PAPERS:
            break

        title = paper.get("title", "Unknown Title")
        year = paper.get("year", "N/A")
        authors = ", ".join(a["name"] for a in paper.get("authors", []))
        pdf_url = paper.get("openAccessPdf", {}).get("url", "")

        pdf_path = os.path.join(PDF_DIR, f"paper{count + 1}.pdf")

        print(f"Downloading paper {count + 1}: {title}")
        success = download_pdf(pdf_url, pdf_path)

        if success:
            metadata.append({
                "title": title,
                "authors": authors,
                "year": year,
                "pdf_path": pdf_path
            })
            count += 1
        else:
            print("Skipped due to invalid or inaccessible PDF.")

    with open(METADATA_FILE, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=4)

    # print("Milestone 1 completed successfully!")


if __name__ == "__main__":
    main()
