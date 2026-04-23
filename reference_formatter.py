import json

def format_references():

    with open("dataset.json","r",encoding="utf-8") as f:
        papers = json.load(f)

    references = []

    for p in papers:

        authors = ", ".join(p.get("authors",["Unknown"]))
        year = p.get("year","n.d")
        title = p.get("title","Unknown")

        ref = f"{authors} ({year}). {title}."

        references.append(ref)

    return references