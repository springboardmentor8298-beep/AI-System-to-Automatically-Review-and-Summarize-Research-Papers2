from modules.paper_search import search_papers
from modules.paper_download import download_pdf


def run():
    print("============================================")
    print(" AI Research Review")
    print(" Automated Paper Search & PDF Download")
    print("============================================\n")

    topic = input("Enter research topic: ").strip()

    if not topic:
        print("Topic cannot be empty.")
        return

    print("\nSearching papers...\n")

    papers = search_papers(topic)

    if not papers:
        print("No papers found for this topic.")
        return

    print("Found Papers:\n")

    for i, paper in enumerate(papers, start=1):
        title = paper.get("title", "No Title")
        year = paper.get("year", "N/A")
        print(f"{i}. {title} ({year})")

    print("\n--------------------------------------------")
    print("Checking for Open Access PDFs...")
    print("--------------------------------------------\n")

    downloaded_count = 0

    for paper in papers:
        title = paper.get("title", "Untitled Paper")
        pdf_info = paper.get("openAccessPdf")

        if pdf_info and pdf_info.get("url"):
            print(f"Downloading: {title}")
            file_path = download_pdf(pdf_info["url"], title)

            if file_path:
                downloaded_count += 1
        else:
            print(f"No Open Access PDF available for: {title}")

    print("\n============================================")
    print(f"Download Complete. Total PDFs downloaded: {downloaded_count}")
    print("Milestone 1 Execution Finished Successfully!")
    print("============================================")


if __name__ == "__main__":
    run()
