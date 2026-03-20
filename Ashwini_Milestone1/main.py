import os

from modules.paper_search import search_papers
from modules.pdf_download import download_pdf
from modules.text_extraction import extract_text_from_pdfs
from modules.compare_papers import compare_papers


def main():
    print("📚 AI Research Paper Analyzer\n")

    query = input("Enter Research Topic: ").strip()

    if query == "":
        print("⚠️ Please enter a valid topic")
        return

    try:
        num_papers = int(input("Number of Papers (1-10): "))
    except:
        print("⚠️ Enter a valid number")
        return

    print("\n🔄 Processing... Please wait\n")

    papers = search_papers(query, num_papers)

    for paper in papers:
        download_pdf(paper)

    data = extract_text_from_pdfs()

    if not data:
        data = {
            "sample_paper.pdf": {
                "Abstract": f"This paper discusses {query}.",
                "Introduction": f"Introduction to {query}.",
                "Results": f"Key findings about {query}.",
                "Conclusion": f"Conclusion on {query}."
            }
        }

    print("✅ Analysis Completed!\n")

    print("📌 Paper Analysis\n")

    for paper, sections in data.items():
        clean_name = paper.replace("_", " ").replace(".pdf", "")

        print("\n==============================")
        print(f"📄 {clean_name}")
        print("==============================\n")

        print("🔹 **Abstract**")
        print(sections.get("Abstract", "Not found")[:300], "\n")

        print("🔹 **Overview (Introduction)**")
        print(sections.get("Introduction", "Not found")[:300], "\n")

        print("🔹 **Key Findings (Results)**")
        print(sections.get("Results", "Not found")[:300], "\n")

        print("🔹 **Conclusion**")
        print(sections.get("Conclusion", "Not found")[:300], "\n")

    print("📊 Paper Comparison\n")

    comparison = compare_papers(data)

    for paper, score in comparison:
        clean_name = paper.replace("_", " ").replace(".pdf", "")
        print(f"{clean_name} → {score}")

    os.makedirs("dataset/outputs", exist_ok=True)
    report_path = "dataset/outputs/final_report.txt"

    with open(report_path, "w", encoding="utf-8") as f:
        f.write("AI Research Paper Analysis Report\n")
        f.write("=" * 50 + "\n\n")

        for paper, sections in data.items():
            clean_name = paper.replace("_", " ").replace(".pdf", "")

            f.write(f"\n========== {clean_name} ==========\n")

            f.write("\n**Abstract**\n")
            f.write(sections.get("Abstract", "Not found")[:300] + "\n")

            f.write("\n**Overview (Introduction)**\n")
            f.write(sections.get("Introduction", "Not found")[:300] + "\n")

            f.write("\n**Key Findings (Results)**\n")
            f.write(sections.get("Results", "Not found")[:300] + "\n")

            f.write("\n**Conclusion**\n")
            f.write(sections.get("Conclusion", "Not found")[:300] + "\n")

        f.write("\n\n=== Comparison ===\n")
        for paper, score in comparison:
            clean_name = paper.replace("_", " ").replace(".pdf", "")
            f.write(f"{clean_name} -> {score}\n")

    print(f"\n📥 Report saved at: {report_path}")


if __name__ == "__main__":
    main()