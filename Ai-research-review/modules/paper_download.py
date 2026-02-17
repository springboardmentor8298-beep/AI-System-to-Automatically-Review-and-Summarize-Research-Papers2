import requests
import os

def download_pdf(pdf_url, title):
    if not pdf_url:
        return None

    os.makedirs("data/papers", exist_ok=True)

    safe_title = title.replace(" ", "_").replace("/", "_")
    file_path = f"data/papers/{safe_title}.pdf"

    response = requests.get(pdf_url)

    if response.status_code == 200:
        with open(file_path, "wb") as f:
            f.write(response.content)
        print(f"Downloaded: {title}")
        return file_path
    else:
        print(f"Failed to download: {title}")
        return None
