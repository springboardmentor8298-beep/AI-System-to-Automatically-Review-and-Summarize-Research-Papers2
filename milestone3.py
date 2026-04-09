import os
import requests
import xml.etree.ElementTree as ET
from PyPDF2 import PdfReader
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

PAPER_FOLDER = "papers"


# Step 1: download papers + store references pdf wise
def download_papers(topic, num_papers):

    os.makedirs(PAPER_FOLDER, exist_ok=True)

    topic_encoded = topic.replace(" ", "+")

    url = f"https://export.arxiv.org/api/query?search_query=all:{topic_encoded}&start=0&max_results={num_papers}"

    print("\nSearching papers from arXiv...")

    response = requests.get(url)

    root = ET.fromstring(response.text)

    namespace = {"atom": "http://www.w3.org/2005/Atom"}

    entries = root.findall("atom:entry", namespace)

    if len(entries) == 0:
        print("No papers found.")
        return {}, 0

    references = {}
    count = 0

    for entry in entries:

        title = entry.find("atom:title", namespace).text.strip()

        year = entry.find("atom:published", namespace).text[:4]

        authors = entry.findall("atom:author", namespace)

        author_names = []

        for author in authors:
            name = author.find("atom:name", namespace).text
            author_names.append(name)

        author_text = ", ".join(author_names)

        pdf_link = ""

        for link in entry.findall("atom:link", namespace):

            if link.attrib.get("title") == "pdf":
                pdf_link = link.attrib["href"]

        if pdf_link:

            filename = f"paper_{count+1}.pdf"

            filepath = os.path.join(PAPER_FOLDER, filename)

            print(f"Downloading paper {count+1}...")

            pdf_data = requests.get(pdf_link).content

            with open(filepath, "wb") as f:
                f.write(pdf_data)

            # APA format linked to PDF name
            apa = f"{author_text} ({year}). {title}. arXiv."

            references[filename] = apa

            count += 1

    print(f"\nDownloaded {count} papers successfully!")

    return references, count


# Step 2: extract text pdf wise
def extract_text():

    papers_text = {}

    print("\nExtracting text from papers...")

    for file in os.listdir(PAPER_FOLDER):

        if file.endswith(".pdf"):

            path = os.path.join(PAPER_FOLDER, file)

            reader = PdfReader(path)

            text = ""

            for page in reader.pages:

                extracted = page.extract_text()

                if extracted:
                    text += extracted + "\n"

            papers_text[file] = text

    return papers_text


# Step 3: search answer pdf wise
def search_answer(query, papers_text):

    results = []

    for file, text in papers_text.items():

        paragraphs = text.split("\n")

        paragraphs = [p.strip() for p in paragraphs if len(p.strip()) > 80]

        if len(paragraphs) == 0:
            continue

        vectorizer = TfidfVectorizer(stop_words="english")

        tfidf = vectorizer.fit_transform(paragraphs + [query])

        similarity = cosine_similarity(tfidf[-1], tfidf[:-1])[0]

        best_index = similarity.argmax()

        best_para = paragraphs[best_index]

        result = f"{file}\n{best_para}"

        results.append(result)

    return "\n\n-------\n\n".join(results)


# main
def main():

    topic = input("Enter research topic: ")

    num_papers = int(input("Enter number of papers: "))

    references, count = download_papers(topic, num_papers)

    if count == 0:
        return

    papers_text = extract_text()

    # show APA references pdf wise
    print("\nREFERENCES (APA FORMAT):\n")

    ref_list = []

    for file, ref in references.items():

        ref_list.append(f"{file}\n{ref}")

    print("\n\n-------\n\n".join(ref_list))

    # question loop
    while True:

        question = input("\nAsk question (or type exit): ")

        if question.lower() == "exit":
            break

        answer = search_answer(question, papers_text)

        print("\nAnswer:\n")

        print(answer)


if __name__ == "__main__":

    main()