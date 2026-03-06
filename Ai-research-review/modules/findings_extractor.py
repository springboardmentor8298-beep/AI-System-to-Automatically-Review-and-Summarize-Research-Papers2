import nltk  #sentence tokenization

nltk.download('punkt')

keywords = [
    "propose",
    "result",
    "show",
    "demonstrate",
    "improve",
    "outperform"
]

def extract_findings(text):

    sentences = nltk.sent_tokenize(text)

    findings = []

    for sentence in sentences: # Each sentence is checked for keywords.

        for word in keywords:

            if word in sentence.lower():
                findings.append(sentence)
                break

    return findings