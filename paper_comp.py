from collections import Counter

def analyze_common_topics(papers):

    collected_sentences = []

    for paper in papers:
        findings = paper.get("key_findings", [])
        collected_sentences.extend(findings)

    word_counter = Counter()

    for sentence in collected_sentences:
        words = sentence.lower().split()

        for word in words:
            if len(word) > 4:
                word_counter[word] += 1

    return word_counter.most_common(10)