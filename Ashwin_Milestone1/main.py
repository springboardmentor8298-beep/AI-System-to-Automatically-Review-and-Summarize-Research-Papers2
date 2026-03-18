# main.py
from modules.paper_search import search_papers
from modules.pdf_download import download_pdf
from modules.pdf_search import search_pdfs_by_topic

def main():
    topic = input("Enter your research topic: ")
    num_papers = int(input("How many papers to fetch from arXiv? "))

    # Step 1: Download PDFs from arXiv
    papers = search_papers(topic, max_results=num_papers)
    for paper in papers:
        download_pdf(paper.pdf_url)

    # Step 2: Search downloaded PDFs
    top_pdfs = search_pdfs_by_topic(topic)
    if top_pdfs:
        print(f"\nTop {len(top_pdfs)} PDFs for topic '{topic}':")
        for i, (filename, count) in enumerate(top_pdfs, start=1):
            print(f"{i}. {filename} (Keyword found {count} times)")
    else:
        print(f"No PDFs found containing the topic '{topic}'.")

if __name__ == "__main__":
    main()