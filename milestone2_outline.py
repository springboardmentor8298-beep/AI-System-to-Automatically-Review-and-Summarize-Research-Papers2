import requests
import json
import re
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import urllib.parse

SEMANTIC_API = "https://api.semanticscholar.org/graph/v1/paper/search"
ARXIV_API = "http://export.arxiv.org/api/query"

DATA_FOLDER = Path("research_papers")

MAX_SEARCH = 30
REQUIRED_PAPERS = 5
THREADS = 4
TIMEOUT = (5, 10)


def clean_name(text):
    return re.sub(r"[^\w\s-]", "", text).replace(" ", "_")


def fetch_semantic_papers(topic):
    print("\nSearching papers from Semantic Scholar...\n")

    params = {
        "query": topic,
        "limit": MAX_SEARCH,
        "fields": "title,authors,year,abstract,openAccessPdf,citationCount"
    }

    try:
        response = requests.get(SEMANTIC_API, params=params, timeout=10)
        response.raise_for_status()
        data = response.json().get("data", [])

        results = []

        for item in data:
            pdf = item.get("openAccessPdf") or {}
            pdf_url = pdf.get("url")

            results.append({
                "title": item.get("title"),
                "authors": [a["name"] for a in item.get("authors", [])],
                "year": item.get("year"),
                "abstract": item.get("abstract"),
                "citations": item.get("citationCount", 0),
                "pdf": pdf_url
            })

        results.sort(key=lambda x: x["citations"], reverse=True)
        return results

    except Exception as e:
        print("Semantic Scholar Error:", e)
        return []


def fetch_arxiv_papers(topic, needed):
    print("\nSearching backup papers from arXiv...\n")

    try:
        topic_encoded = urllib.parse.quote(topic)
        url = f"{ARXIV_API}?search_query=all:{topic_encoded}&start=0&max_results={needed}"

        response = requests.get(url, timeout=10)
        response.raise_for_status()

        entries = response.text.split("<entry>")[1:]
        papers = []

        for entry in entries:
            title_match = re.search(r"<title>(.*?)</title>", entry, re.S)
            abstract_match = re.search(r"<summary>(.*?)</summary>", entry, re.S)
            arxiv_id_match = re.search(r"<id>http://arxiv.org/abs/(.*?)</id>", entry)

            pdf_url = None
            if arxiv_id_match:
                arxiv_id = arxiv_id_match.group(1).strip()
                pdf_url = f"https://arxiv.org/pdf/{arxiv_id}.pdf"

            papers.append({
                "title": title_match.group(1).strip() if title_match else "Unknown",
                "authors": ["arXiv"],
                "year": None,
                "abstract": abstract_match.group(1).strip() if abstract_match else None,
                "citations": 0,
                "pdf": pdf_url
            })

        return papers

    except Exception as e:
        print("arXiv Error:", e)
        return []


def download_file(url, path):
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        r = requests.get(url, headers=headers, stream=True, timeout=TIMEOUT)
        r.raise_for_status()

        with open(path, "wb") as f:
            for chunk in r.iter_content(8192):
                if chunk:
                    f.write(chunk)

        return True

    except Exception:
        return False


def gather_papers(topic):
    papers = fetch_semantic_papers(topic)

    unique = {p["title"]: p for p in papers if p.get("title")}
    papers = list(unique.values())

    if len(papers) < REQUIRED_PAPERS:
        extra = fetch_arxiv_papers(topic, REQUIRED_PAPERS - len(papers))
        papers.extend(extra)

    return papers[:REQUIRED_PAPERS]


def download_papers(papers, topic):
    folder = DATA_FOLDER / clean_name(topic)
    folder.mkdir(parents=True, exist_ok=True)

    dataset = []
    tasks = []

    with ThreadPoolExecutor(max_workers=THREADS) as pool:

        for i, p in enumerate(papers, 1):
            file_path = folder / f"paper_{i}.pdf"
            p["id"] = i

            if p.get("pdf"):
                tasks.append((pool.submit(download_file, p["pdf"], file_path), p, file_path))
            else:
                p["pdf_available"] = False
                dataset.append(p)

        for future, p, file_path in tasks:
            success = future.result()

            if success:
                p["pdf_available"] = True
                p["file_path"] = str(file_path)
                p["local_path"] = str(file_path)
                print("Downloaded:", file_path.name)
            else:
                p["pdf_available"] = False
                print("Failed:", p["title"])

            dataset.append(p)

    return dataset


def save_json(data, topic):
    file_name = f"dataset_{clean_name(topic)}.json"

    with open(file_name, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

    print("\nDataset saved:", file_name)


def main():
    print("\n===== Automatic Research Paper Collector =====")

    topic = input("\nEnter research topic: ").strip()

    if not topic:
        print("Topic missing")
        return

    papers = gather_papers(topic)

    if not papers:
        print("No papers found")
        return

    dataset = download_papers(papers, topic)
    save_json(dataset, topic)

    print("\nProcess Finished Successfully")


if __name__ == "__main__":
    main()