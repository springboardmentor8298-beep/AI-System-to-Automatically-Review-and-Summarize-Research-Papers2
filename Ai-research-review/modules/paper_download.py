import os
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("SEMANTIC_SCHOLAR_API_KEY")

DOWNLOAD_FOLDER = "data/papers"
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)


def download_pdf(pdf_url, title):

    try:
        response = requests.get(pdf_url)

        if response.status_code == 200:

            safe_title = title[:60].replace(" ", "_").replace("/", "")
            file_path = os.path.join(DOWNLOAD_FOLDER, safe_title + ".pdf")

            with open(file_path, "wb") as f:
                f.write(response.content)

            print(f"✅ PDF downloaded: {file_path}")

        else:
            print("❌ Failed to download PDF")

    except Exception as e:
        print("❌ Download error:", str(e))


def download_papers(topic):

    if not API_KEY:
        print("❌ API key not found in .env")
        return

    print("\nSearching papers...\n")

    url = "https://api.semanticscholar.org/graph/v1/paper/search"

    headers = {
        "x-api-key": API_KEY,
        "User-Agent": "AI-Research-Review-System"
    }

    params = {
        "query": topic,
        "limit": 5,
        "fields": "title,authors,year,abstract,url,openAccessPdf"
    }

    try:

        response = requests.get(url, headers=headers, params=params)

        if response.status_code == 200:

            data = response.json()
            papers = data.get("data", [])

            if not papers:
                print("⚠ No papers found")
                return

            for i, paper in enumerate(papers, start=1):

                print("\n" + "=" * 60)
                print(f"Paper {i}")
                print("=" * 60)

                title = paper.get("title", "N/A")
                print("Title:", title)
                print("Year:", paper.get("year", "N/A"))

                authors = [a["name"] for a in paper.get("authors", [])]
                print("Authors:", ", ".join(authors) if authors else "N/A")

                abstract = paper.get("abstract", "No abstract available")
                print("\nAbstract:\n", abstract)

                pdf = paper.get("openAccessPdf")

                if pdf and pdf.get("url"):

                    pdf_url = pdf.get("url")

                    choice = input("Download this paper? (y/n): ")

                    if choice.lower() == "y":
                        download_pdf(pdf_url, title)

                else:
                    print("Open Access PDF not available")

        else:
            print("❌ API Error:", response.status_code)

    except Exception as e:
        print("❌ Error:", str(e))