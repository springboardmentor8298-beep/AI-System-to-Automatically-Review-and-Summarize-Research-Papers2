import requests
import xml.etree.ElementTree as ET
import os

def fetch_papers(topic):
    url = f"http://export.arxiv.org/api/query?search_query=all:{topic}&start=0&max_results=3"
    response = requests.get(url)

    if response.status_code != 200:
        print("Error fetching papers")
        return

    root = ET.fromstring(response.text)
    namespace = {'atom': 'http://www.w3.org/2005/Atom'}

    # Create papers folder if not exists
    if not os.path.exists("papers"):
        os.makedirs("papers")

    for entry in root.findall('atom:entry', namespace):
        title = entry.find('atom:title', namespace).text.strip()
        link = entry.find('atom:id', namespace).text

        print("\nTitle:", title)
        print("Link:", link)

        # Convert abstract link to PDF link
        pdf_url = link.replace("abs", "pdf") + ".pdf"

        pdf_response = requests.get(pdf_url)

        safe_title = title.replace(" ", "_").replace("/", "_")
        file_path = os.path.join("papers", safe_title + ".pdf")

        with open(file_path, "wb") as pdf_file:
            pdf_file.write(pdf_response.content)

        print("PDF downloaded:", file_path)

if __name__ == "__main__":
    topic = input("Enter research topic: ")
    fetch_papers(topic)