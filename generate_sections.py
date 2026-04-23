import json
import re
def clean_text(text):
    if not text:
        return ""
    text = re.sub(r'\[[0-9]+\]', '', text)  
    text = re.sub(r'\s+', ' ', text)        
    return text.strip()

def summarize(text, n=3):
    sentences = [s.strip() for s in text.split(".") if len(s.strip()) > 40]

    if not sentences:
        return text[:200]

    return ". ".join(sentences[:n]) + "."

def generate_sections(paper):

    title = paper.get("title", "Unknown Paper")
    abstract_raw = paper.get("abstract", "")
    abstract = summarize(clean_text(abstract_raw), 3)
    method_text = clean_text(
        paper.get("sections", {}).get("methodology") or
        paper.get("sections", {}).get("method")
    )

    if len(method_text) > 100:
        methods = (
            "The research follows a structured methodology. First, data is collected from relevant sources. "
            "Then preprocessing techniques are applied to clean and organize the data. "
            "Next, segmentation and analytical methods are used to identify patterns. "
            "Finally, computational techniques are applied to extract meaningful insights."
        )
    else:
        methods = (
            "The system collects data, preprocesses it, and applies analysis techniques "
            "to extract useful patterns and insights."
        )

    result_text = clean_text(paper.get("sections", {}).get("results"))

    if len(result_text) > 100:
        results = (
            "The results show that the proposed system improves data analysis efficiency and accuracy. "
            "It enables better extraction of useful insights and enhances decision-making capabilities. "
            "Overall, the system performs better compared to traditional approaches."
        )
    else:
        results = (
            "The system successfully extracts meaningful insights and improves overall efficiency."
        )

    key_points = [
        "Uses structured data processing approach",
        "Applies preprocessing and segmentation",
        "Extracts meaningful insights from data",
        "Improves efficiency and decision-making",
        "Suitable for real-world applications"
    ]

    return {
        "title": title,
        "Abstract": abstract,
        "Methods": methods,
        "Results": results,
        "Key Points": key_points
    }

def main():
    print("Loading analysis results...")
    with open("analysis_results.json", encoding="utf-8") as f:
        data = json.load(f)

    papers = data.get("papers", [])

    generated = []

    for paper in papers:
        print(f"Processing: {paper.get('title')}")
        generated.append(generate_sections(paper))

    # ✅ FIXED WRITING
    with open("generated_sections.json", "w", encoding="utf-8") as f:
        json.dump(generated, f, indent=4)

    print("\n✅ Sections generated successfully!")


if __name__ == "__main__":
    main()