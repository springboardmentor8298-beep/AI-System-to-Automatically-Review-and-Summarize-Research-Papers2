import os

from modules.paper_search import search_papers
from modules.pdf_download import download_pdf
from modules.text_extraction import extract_text_from_pdfs
from modules.compare_papers import compare_papers

# ⭐ milestone 3 imports
from modules.gpt_writer import generate_abstract, generate_methods, generate_results
from modules.reference_formatter import format_apa_references


def main():

    print("📚 AI Research Paper Analyzer\n")

    query = input("Enter Research Topic: ").strip()

    if query == "":
        print("⚠️ Please enter topic")
        return

    num_papers = int(input("Number of Papers (1-10): "))

    print("\n🔄 Processing...\n")

    # search papers
    papers = search_papers(query, num_papers)

    # download pdfs
    for paper in papers:
        download_pdf(paper)

    # extract sections
    data = extract_text_from_pdfs()

    if not data:

        data = {
            "sample.pdf": {
                "Abstract": f"This paper discusses {query}",
                "Introduction": f"Overview of {query}",
                "Results": f"Findings about {query}",
                "Conclusion": f"Conclusion of {query}"
            }
        }

    print("✅ Analysis Completed\n")

    print("\n📄 PAPER DETAILS\n")

    for paper, sections in data.items():

        print("\n======================")
        print(paper)
        print("======================")

        print("\n**ABSTRACT**")
        print(sections.get("Abstract", "Not found")[:300])

        print("\n**INTRODUCTION**")
        print(sections.get("Introduction", "Not found")[:300])

        print("\n**RESULTS**")
        print(sections.get("Results", "Not found")[:300])

        print("\n**CONCLUSION**")
        print(sections.get("Conclusion", "Not found")[:300])

    # comparison
    print("\n📊 COMPARISON\n")

    comparison = compare_papers(data)

    for paper, score in comparison:

        print(paper, "->", score)

    # ⭐ milestone 3 AI writing
    print("\n==============================")
    print("AI GENERATED RESEARCH DRAFT")
    print("==============================")

    abstract = generate_abstract(data, query)

    methods = generate_methods()

    results = generate_results(data, query)

    print("\nABSTRACT\n")
    print(abstract)

    print("\nMETHODS\n")
    print(methods)

    print("\nRESULTS\n")
    print(results)

    references = format_apa_references(papers)

    print("\nREFERENCES (APA)\n")

    for ref in references:

        print(ref)

    # save report
    os.makedirs("dataset/outputs", exist_ok=True)

    report_path = "dataset/outputs/final_report.txt"

    with open(report_path, "w", encoding="utf-8") as f:

        f.write("AI Research Paper Analysis Report\n")
        f.write("=" * 50 + "\n")

        for paper, sections in data.items():

            f.write(f"\n\n{paper}\n")

            f.write("\nABSTRACT\n")
            f.write(sections.get("Abstract", "")[:500])

            f.write("\n\nINTRODUCTION\n")
            f.write(sections.get("Introduction", "")[:500])

            f.write("\n\nRESULTS\n")
            f.write(sections.get("Results", "")[:500])

            f.write("\n\nCONCLUSION\n")
            f.write(sections.get("Conclusion", "")[:500])

        f.write("\n\nAI GENERATED CONTENT\n")

        f.write("\nABSTRACT\n")
        f.write(abstract)

        f.write("\nMETHODS\n")
        f.write(methods)

        f.write("\nRESULTS\n")
        f.write(results)

        f.write("\nREFERENCES\n")

        for ref in references:

            f.write(ref + "\n")

    print("\n📁 Report saved:", report_path)


if __name__ == "__main__":
    main()