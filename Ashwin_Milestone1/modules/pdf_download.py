# modules/pdf_download.py
import os
import requests

def download_pdf(url, folder="dataset/pdfs"):
    """
    Download PDF from URL and save in folder.
    """
    os.makedirs(folder, exist_ok=True)
    filename = os.path.join(folder, url.split('/')[-1] + ".pdf")
    
    if os.path.exists(filename):
        print(f"Already downloaded: {filename}")
        return filename
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        with open(filename, "wb") as f:
            f.write(response.content)
        print(f"Downloaded: {filename}")
        return filename
    except Exception as e:
        print(f"Failed to download {url}: {e}")
        return None