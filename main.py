import requests
import json
import re
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

SEMANTIC_API = "https://api.semanticscholar.org/graph/v1/paper/search"
ARXIV_API = "http://export.arxiv.org/api/query"

DATA_FOLDER = Path("research_papers")

MAX_SEARCH = 30
REQUIRED_PAPERS = 5
THREADS = 4
TIMEOUT = (5,10)


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

            pdf = item.get("openAccessPdf", {})
            pdf_url = pdf.get("url") if pdf else None

            results.append({
                "title": item.get("title"),
                "authors": [a["name"] for a in item.get("authors", [])],
                "year": item.get("year"),
                "abstract": item.get("abstract"),
                "citations": item.get("citationCount",0),
                "pdf": pdf_url
            })

        results.sort(key=lambda x: x["citations"], reverse=True)

        return results

    except Exception as e:
        print("Semantic Scholar Error:", e)
        return []


def fetch_arxiv_papers(topic, needed):

    print("\nSearching backup papers from arXiv...\n")

    params = {
        "search_query": f"all:{topic}",
        "start": 0,
        "max_results": needed
    }

    try:
        response = requests.get(ARXIV_API, params=params, timeout=10)
        entries = response.text.split("<entry>")[1:]

        papers = []

        for entry in entries:

            title = re.search(r"<title>(.*?)</title>", entry, re.S)
            abstract = re.search(r"<summary>(.*?)</summary>", entry, re.S)
            pdf = re.search(r'href="(https://arxiv.org/pdf/.*?)"', entry)

            papers.append({
                "title": title.group(1).strip() if title else "Unknown",
                "authors": ["arXiv"],
                "year": None,
                "abstract": abstract.group(1).strip() if abstract else None,
                "citations": 0,
                "pdf": pdf.group(1) if pdf else None
            })

        return papers

    except Exception as e:
        print("arXiv Error:", e)
        return []


def download_file(url, path):

    try:
        headers = {"User-Agent":"Mozilla/5.0"}

        r = requests.get(url, headers=headers, stream=True, timeout=TIMEOUT)

        with open(path,"wb") as f:
            for chunk in r.iter_content(8192):
                if chunk:
                    f.write(chunk)

        return True

    except:
        return False


def gather_papers(topic):

    papers = fetch_semantic_papers(topic)

    unique = {}

    for p in papers:
        unique[p["title"]] = p

    papers = list(unique.values())

    if len(papers) < REQUIRED_PAPERS:
        extra = fetch_arxiv_papers(topic, REQUIRED_PAPERS-len(papers))
        papers.extend(extra)

    return papers[:REQUIRED_PAPERS]


def download_papers(papers, topic):

    folder = DATA_FOLDER / clean_name(topic)
    folder.mkdir(parents=True, exist_ok=True)

    dataset = []

    with ThreadPoolExecutor(max_workers=THREADS) as pool:

        tasks = []

        for i,p in enumerate(papers,1):

            file_path = folder / f"paper_{i}.pdf"
            p["id"] = i

            if p["pdf"]:
                tasks.append((pool.submit(download_file,p["pdf"],file_path),p,file_path))
            else:
                p["pdf_available"] = False
                dataset.append(p)

        for future,p,file_path in tasks:

            success = future.result()

            if success:
                p["pdf_available"] = True
                p["file_path"] = str(file_path)
                print("Downloaded:",file_path.name)
            else:
                p["pdf_available"] = False
                print("Failed:",p["title"])

            dataset.append(p)

    return dataset


def save_json(data,topic):

    file_name = f"dataset_{clean_name(topic)}.json"

    with open(file_name,"w",encoding="utf-8") as f:
        json.dump(data,f,indent=4,ensure_ascii=False)

    print("\nDataset saved:",file_name)


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

    dataset = download_papers(papers,topic)

    save_json(dataset,topic)

    print("\nProcess Finished Successfully")


if __name__ == "__main__":
    main()