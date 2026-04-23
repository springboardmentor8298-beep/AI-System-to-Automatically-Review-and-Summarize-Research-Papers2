import json

print("Generating APA references...")

# Load analysis results
with open("analysis_results.json", "r", encoding="utf-8") as f:
    data = json.load(f)

# Convert dictionary to list if needed
if isinstance(data, dict):
    papers = list(data.values())
else:
    papers = data

references = []

for paper in papers:

    if isinstance(paper, dict):
        title = paper.get("title", "Unknown Title")
        authors = paper.get("authors", ["Unknown Author"])
        year = paper.get("year", "2024")

        if isinstance(authors, list):
            author_text = ", ".join(authors)
        else:
            author_text = str(authors)

    else:
        title = str(paper)
        author_text = "Unknown Author"
        year = "2024"

    apa_reference = f"{author_text}. ({year}). {title}."

    references.append(apa_reference)

# Save references
with open("references.txt", "w", encoding="utf-8") as f:
    for ref in references:
        f.write(ref + "\n")

print("APA references generated successfully!")