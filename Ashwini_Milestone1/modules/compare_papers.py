def compare_papers(data):
    comparison = []

    for paper, sections in data.items():
        combined_text = ""

        for section in sections.values():
            if section:
                combined_text += section + " "

        words = combined_text.split()
        score = len(words)

        comparison.append((paper, score))

    comparison.sort(key=lambda x: x[1], reverse=True)

    return comparison