import requests
import xml.etree.ElementTree as ET

def fetch_papers(topic):
    url = f"http://export.arxiv.org/api/query?search_query=all:{topic}&start=0&max_results=5"
    response = requests.get(url)

    if response.status_code != 200:
        print("Error fetching papers")
        return

    root = ET.fromstring(response.text)
    namespace = {'atom': 'http://www.w3.org/2005/Atom'}

    with open("output.txt", "w", encoding="utf-8") as file:
        file.write(f"Research Papers on: {topic}\n\n")

        for entry in root.findall('atom:entry', namespace):
            title = entry.find('atom:title', namespace).text.strip()
            published = entry.find('atom:published', namespace).text
            link = entry.find('atom:id', namespace).text

            file.write(f"Title: {title}\n")
            file.write(f"Published: {published}\n")
            file.write(f"Link: {link}\n\n")

            print("\nTitle:", title)
            print("Published:", published)
            print("Link:", link)

    print("\n✅ Output saved to output.txt")

if __name__ == "__main__":
    topic = input("Enter research topic: ")
    fetch_papers(topic)
