import requests
import os
import json
import feedparser

ARXIV_API_URL = "http://export.arxiv.org/api/query"
BASE_DIR = "papers"
METADATA_FILE = "papers_metadata.json"


def search_papers(query, max_results=5):
    params = {"search_query": f"all:{query}", "start": 0, "max_results": max_results}
    response = requests.get(ARXIV_API_URL, params=params)
    response.raise_for_status()
    feed = feedparser.parse(response.text)
    return feed.entries


def download_pdf(pdf_url, filename, topic_folder):
    os.makedirs(topic_folder, exist_ok=True)
    response = requests.get(pdf_url)
    if response.status_code == 200:
        filepath = os.path.join(topic_folder, filename)
        with open(filepath, "wb") as f:
            f.write(response.content)
        return filepath
    else:
        print(f"Failed to download PDF: {pdf_url}")
        return None


def save_metadata(metadata_list):
    with open(METADATA_FILE, "w", encoding="utf-8") as f:
        json.dump(metadata_list, f, indent=4)
    print(f"\nMetadata saved to {METADATA_FILE}")


def milestone1_workflow():
    topic = input("Enter your research topic: ")
    print(f"\nSearching papers for topic: {topic}\n")
    papers = search_papers(topic)

    metadata_list = []

    for idx, paper in enumerate(papers, start=1):
        title = paper.title
        authors = [author.name for author in paper.authors]
        pdf_url = paper.id.replace("abs", "pdf")
        safe_topic = "".join(c if c.isalnum() else "_" for c in topic)
        topic_folder = os.path.join(BASE_DIR, safe_topic)
        os.makedirs(topic_folder, exist_ok=True)

        print(f"{idx}. {title}")
        safe_title = "".join(c if c.isalnum() else "_" for c in title[:50])
        filename = f"paper_{idx}_{safe_title}.pdf"
        pdf_path = download_pdf(pdf_url, filename, topic_folder)

        metadata = {
            "paper_id": f"arxiv_{idx}",
            "title": title,
            "authors": authors,
            "pdf_path": pdf_path if pdf_path else "Not downloaded",
            "source_url": paper.id,
        }
        metadata_list.append(metadata)

    save_metadata(metadata_list)


if __name__ == "__main__":
    milestone1_workflow()
