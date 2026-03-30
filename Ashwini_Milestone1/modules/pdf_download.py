import os
import requests
import certifi

def download_pdf(paper, folder="dataset/pdfs"):
    os.makedirs(folder, exist_ok=True)

    try:
        pdf_url = paper.pdf_url
        filename = os.path.join(folder, pdf_url.split("/")[-1] + ".pdf")

        response = requests.get(pdf_url, verify=certifi.where())

        if response.status_code == 200:
            with open(filename, "wb") as f:
                f.write(response.content)
            print(f"Downloaded: {filename}")
        else:
            print(f"Failed to download: {pdf_url}")

    except Exception as e:
        print(f"Error downloading: {e}")