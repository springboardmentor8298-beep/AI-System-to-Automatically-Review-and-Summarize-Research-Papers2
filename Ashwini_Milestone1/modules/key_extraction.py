def extract_key_points(text, keyword):
    sentences = text.split(".")
    key_points = []

    for sentence in sentences:
        if keyword.lower() in sentence.lower():
            key_points.append(sentence.strip())

    # ✅ fallback if no match
    if not key_points:
        key_points = sentences[:5]

    return key_points[:5]