from data_collection.paper_search import search_papers
from data_collection.paper_download import download_pdf

from processing.pdf_extractor import extract_text_from_pdf
from processing.ocr_handler import extract_text_with_ocr
from processing.text_cleaner import clean_text

from analysis.section_extractor import extract_sections
from analysis.findings_extractor import extract_key_findings
from analysis.comparator import compare_papers

from generation.gpt_writer import generate_abstract, generate_methods, generate_results
from generation.reference_formatter import format_apa_references

from generation.reviewer import evaluate_content, revise_content

import json

import sys
import os

sys.path.append(os.path.abspath(os.path.dirname(__file__)))


# def run_pipeline():
#     topic = input("Enter research topic: ")

#     print("\n🔍 Searching papers...")
#     papers = search_papers(topic, max_results=5)

#     dataset = []

#     print("\n⬇️ Downloading + Processing...")

#     for paper in papers:
#         path = download_pdf(paper)

#         if not path:
#             continue

#         # 🔹 Extract text
#         text = extract_text_from_pdf(path)

#         if text is None:
#             print("⚠️ Using OCR...")
#             text = extract_text_with_ocr(path)

#         text = clean_text(text)

#         # 🔹 Extract sections
#         sections = extract_sections(text)

#         # 🔹 Extract findings
#         findings = extract_key_findings(text)

#         dataset.append({
#             "title": paper["title"],
#             "pdf_path": path,
#             "Abstract": sections["Abstract"],
#             "Methodology": sections["Methodology"],
#             "Key_Findings": findings
#         })

#     # Save dataset
#     with open("processed_dataset.json", "w") as f:
#         json.dump(dataset, f, indent=4)

#     print("\n✅ Processed dataset saved!")

#     # Comparison
#     print(compare_papers(dataset))

#     # 🔥 GPT GENERATION (FIXED INDENTATION)
#     print("\n🧠 Generating research paper sections...\n")

#     abstract = generate_abstract(dataset)
#     methods = generate_methods(dataset)
#     results = generate_results(dataset)
#     references = format_apa_references(dataset)

#     # Save outputs
#     with open("final_output.txt", "w") as f:
#         f.write("=== ABSTRACT ===\n")
#         f.write(abstract + "\n\n")

#         f.write("=== METHODS ===\n")
#         f.write(methods + "\n\n")

#         f.write("=== RESULTS ===\n")
#         f.write(results + "\n\n")

#         f.write("=== REFERENCES (APA) ===\n")
#         f.write(references)

#     print("✅ Final research draft generated!")

#     print("\n🔍 Evaluating generated content...\n")

#     evaluation = evaluate_content(abstract + methods + results)

#     print("\n🛠 Revising content...\n")

#     revised_abstract = revise_content(abstract)
#     revised_methods = revise_content(methods)
#     revised_results = revise_content(results)

#     with open("final_output.txt", "w") as f:
#         f.write("=== ABSTRACT ===\n")
#         f.write(revised_abstract + "\n\n")

#         f.write("=== METHODS ===\n")
#         f.write(revised_methods + "\n\n")

#         f.write("=== RESULTS ===\n")
#         f.write(revised_results + "\n\n")

#         f.write("=== REFERENCES ===\n")
#         f.write(references + "\n\n")

#         f.write("=== EVALUATION ===\n")
#         f.write(evaluation)


# if __name__ == "__main__":
#     run_pipeline()




def run_pipeline(topic):
    print("\n🔍 Searching papers...")
    papers = search_papers(topic, max_results=5)

    dataset = []

    print("\n⬇️ Downloading + Processing...")

    for paper in papers:
        path = download_pdf(paper)

        if not path:
            continue

        text = extract_text_from_pdf(path)

        if text is None:
            print("⚠️ Using OCR...")
            text = extract_text_with_ocr(path)

        text = clean_text(text)

        sections = extract_sections(text)
        findings = extract_key_findings(text)

        dataset.append({
            "title": paper["title"],
            "pdf_path": path,
            "Abstract": sections["Abstract"],
            "Methodology": sections["Methodology"],
            "Key_Findings": findings
        })

    with open("processed_dataset.json", "w") as f:
        json.dump(dataset, f, indent=4)

    print("\n🧠 Generating research paper sections...\n")

    abstract = generate_abstract(dataset)
    methods = generate_methods(dataset)
    results = generate_results(dataset)
    references = format_apa_references(dataset)

    # Save initial
    with open("initial_output.txt", "w") as f:
        f.write("=== ABSTRACT ===\n" + abstract + "\n\n")
        f.write("=== METHODS ===\n" + methods + "\n\n")
        f.write("=== RESULTS ===\n" + results + "\n\n")
        f.write("=== REFERENCES ===\n" + references)

    print("\n🔍 Evaluating...\n")

    evaluation = evaluate_content(abstract + methods + results)

    print("\n🛠 Revising...\n")

    revised_abstract = revise_content(abstract)
    revised_methods = revise_content(methods)
    revised_results = revise_content(results)

    # Save final
    with open("final_output.txt", "w") as f:
        f.write("=== ABSTRACT ===\n" + revised_abstract + "\n\n")
        f.write("=== METHODS ===\n" + revised_methods + "\n\n")
        f.write("=== RESULTS ===\n" + revised_results + "\n\n")
        f.write("=== REFERENCES ===\n" + references + "\n\n")
        f.write("=== EVALUATION ===\n" + evaluation)

    return f"""
    ABSTRACT:
    {revised_abstract}

    METHODS:
    {revised_methods}

    RESULTS:
    {revised_results}

    REFERENCES:
    {references}
    """