import glob
import json
import re
from text_extractor import extract_pdf_text
from section_parser import get_sections_from_text
from key_finder import get_key_findings
from paper_comp import analyze_common_topics
def process_papers(dataset_file):
    with open(dataset_file, "r") as file:
        papers_data = json.load(file)

    processed_papers = []

    for paper in papers_data:
        if not paper.get("pdf_available") or not paper.get("local_path"):
            print("Skipping paper (PDF not available):", paper.get("title"))
            continue

        pdf_path = paper["local_path"]
        print("Processing:", pdf_path)
        text = extract_pdf_text(pdf_path)

        sections = get_sections_from_text(text)

        findings = get_key_findings(text)

        paper["sections"] = sections
        paper["key_findings"] = findings

        processed_papers.append(paper)

    comparison = analyze_common_topics(processed_papers)

    results = {
        "papers": processed_papers,
        "common_topics": comparison
    }

    with open("analysis_results.json", "w", encoding="utf-8") as output:
        json.dump(results, output, indent=4, ensure_ascii=False)

    print("\nAnalysis completed. Results saved in analysis_results.json")

if __name__ == "__main__":
    dataset_files = glob.glob("dataset_*.json")

    if not dataset_files:
        print("No dataset files found. Please run the paper downloader first.")
        exit()

    print("\nAvailable Datasets:\n")
    for i, file in enumerate(dataset_files, start=1):
        print(f"{i}. {file}")

    choice = int(input("\nSelect dataset number: "))
    dataset_file = dataset_files[choice - 1]

    print(f"\nAnalyzing dataset: {dataset_file}\n")
    process_papers(dataset_file)