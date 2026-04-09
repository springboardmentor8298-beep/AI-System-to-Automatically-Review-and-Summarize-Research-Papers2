def format_apa_references(papers):

    references = []

    for paper in papers:

        try:
            authors = ", ".join(
                author.name for author in paper.authors[:2]
            )

            year = paper.published.year

            title = paper.title

            ref = f"{authors} ({year}). {title}. arXiv."

            references.append(ref)

        except:
            references.append("Unknown Author (2024). Research Paper. arXiv.")

    return references