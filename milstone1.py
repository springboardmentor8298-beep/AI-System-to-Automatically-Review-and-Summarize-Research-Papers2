import requests
import pandas as pd
import xml.etree.ElementTree as ET
import webbrowser
import os

print("🚀 Program Started...")

topic = input("🔍 Enter research topic: ")

url = f"http://export.arxiv.org/api/query?search_query=all:{topic}&start=0&max_results=5"

response = requests.get(url)

if response.status_code != 200:
    print("❌ Failed to fetch data")
    exit()

root = ET.fromstring(response.content)

papers = []

# 📁 Create folder for PDFs
folder = "downloaded_papers"
os.makedirs(folder, exist_ok=True)

print("\n📚 Top Research Papers:\n")

for i, entry in enumerate(root.findall("{http://www.w3.org/2005/Atom}entry"), start=1):
    
    title = entry.find("{http://www.w3.org/2005/Atom}title").text.strip()
    published = entry.find("{http://www.w3.org/2005/Atom}published").text[:4]

    authors = [a.find("{http://www.w3.org/2005/Atom}name").text 
               for a in entry.findall("{http://www.w3.org/2005/Atom}author")]
    authors_str = ", ".join(authors)

    pdf_link = ""
    for link in entry.findall("{http://www.w3.org/2005/Atom}link"):
        if link.attrib.get("title") == "pdf":
            pdf_link = link.attrib.get("href")

    print(f"{i}. 📄 {title}")
    print(f"   📅 Year: {published}")
    print(f"   👨‍🔬 Authors: {authors_str}")
    print(f"   🔗 PDF: {pdf_link}\n")

    papers.append({
        "title": title,
        "year": published,
        "authors": authors_str,
        "pdf_link": pdf_link
    })

# 📊 Save CSV
df = pd.DataFrame(papers)
df.to_csv("paper_dataset.csv", index=False)

print("✅ CSV file created!")

# 🔽 Download PDFs
download_choice = input("\nDo you want to download all PDFs? (yes/no): ")

if download_choice.lower() == "yes":
    for i, paper in enumerate(papers, start=1):
        try:
            pdf_url = paper["pdf_link"]
            pdf_data = requests.get(pdf_url).content

            file_name = f"{folder}/paper_{i}.pdf"

            with open(file_name, "wb") as f:
                f.write(pdf_data)

            print(f"⬇️ Downloaded: {file_name}")

        except Exception as e:
            print(f"❌ Failed to download paper {i}")

# 🌐 Open PDF
open_choice = input("\nDo you want to open a paper? (yes/no): ")

if open_choice.lower() == "yes":
    num = int(input("Enter paper number: "))
    webbrowser.open(papers[num-1]["pdf_link"])