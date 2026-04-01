def extract_sections(text):
    text_lower = text.lower()

    sections = {
        "Abstract": "",
        "Methodology": "",
        "Results": ""
    }

    try:
        if "abstract" in text_lower:
            sections["Abstract"] = text.split("abstract", 1)[1][:1500]

        if "method" in text_lower:
            sections["Methodology"] = text.split("method", 1)[1][:2000]

        if "result" in text_lower:
            sections["Results"] = text.split("result", 1)[1][:2000]

    except:
        pass

    return sections