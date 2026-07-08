from modules.paper_download import download_papers

from modules.pdf_extractor import extract_all_papers
from modules.section_extractor import extract_sections
from modules.findings_extractor import extract_findings
from modules.validator import validate_sections

import json
import os

PAPER_FOLDER = "data/papers"
OUTPUT_FOLDER = "processed_data/sections_json"


def process_papers():

    papers = extract_all_papers(PAPER_FOLDER)

    for paper_name, text in papers.items():

        print(f"\nProcessing: {paper_name}")

        sections = extract_sections(text)

        missing = validate_sections(sections)

        if missing:
            print("Missing sections:", missing)

        findings = extract_findings(text)

        sections["key_findings"] = findings

        json_name = paper_name.replace(".pdf", ".json")
        save_path = os.path.join(OUTPUT_FOLDER, json_name)

        with open(save_path, "w", encoding="utf-8") as f:
            json.dump(sections, f, indent=4)

        print("Saved:", save_path)


def main():

    topic = input("Enter research topic: ")

    download_papers(topic)

    print("\nStarting paper analysis...\n")

    process_papers()


if __name__ == "__main__":
    main()