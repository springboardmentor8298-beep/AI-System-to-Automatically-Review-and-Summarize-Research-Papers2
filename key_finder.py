import re

KEY_PHRASES = [
    "we propose",
    "we present",
    "our results",
    "we demonstrate",
    "this paper shows",
    "significant improvement"
]

def get_key_findings(text):

    sentences = re.split(r'(?<=[.!?])\s+', text)

    findings = []

    for sentence in sentences:
        lower_sentence = sentence.lower()

        for phrase in KEY_PHRASES:
            if phrase in lower_sentence:
                findings.append(sentence.strip())
                break

    return findings[:5]