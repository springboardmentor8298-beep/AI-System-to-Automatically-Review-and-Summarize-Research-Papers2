def extract_key_findings(text):
    sentences = text.split('.')

    keywords = ["result", "outperform", "accuracy", "improvement", "better", "performance"]

    important = [
        s.strip() for s in sentences
        if any(word in s.lower() for word in keywords)
    ]

    return ". ".join(important[:5])