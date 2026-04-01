def format_apa_references(papers):
    references = []

    for p in papers:
        authors = ", ".join(p.get("authors", ["Unknown"]))
        year = p.get("year", "n.d.")
        title = p.get("title", "Untitled")

        ref = f"{authors} ({year}). {title}."
        references.append(ref)

    return "\n".join(references)