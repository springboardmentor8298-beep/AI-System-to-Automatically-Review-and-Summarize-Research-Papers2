import os
import requests
import pandas as pd
import time

def search_and_download_by_topic(topic: str, max_papers: int = 5, download_dir: str = "downloaded_papers"):
    """
    Searches for a topic and downloads the top Open Access papers found.
    """
    os.makedirs(download_dir, exist_ok=True)
    
    
    endpoint = "https://api.semanticscholar.org/graph/v1/paper/search"

    fields = "title,authors,year,openAccessPdf,url,abstract"
    
    params = {
        "query": topic,
        "limit": max_papers,
        "fields": fields
    }

    all_paper_data = []
    downloaded_count = 0

    print(f"Searching for topic: '{topic}' (Max: {max_papers} papers)...")

    try:

        response = requests.get(endpoint, params=params, timeout=20)
        
        if response.status_code == 429:
            print(" -> Error: Rate limited by Semantic Scholar. Try again in a few minutes.")
            return pd.DataFrame()
            
        response.raise_for_status()
        papers = response.json().get("data", [])

        if not papers:
            print(" -> No papers found for this topic.")
            return pd.DataFrame()

        for paper in papers:
            print(f"\n--- Processing: {paper['title'][:60]}... ---")
            
            pdf_url = None
            if paper.get("openAccessPdf"):
                pdf_url = paper["openAccessPdf"].get("url")
            
            # Fallback: Check if the main URL is from ArXiv
            if not pdf_url and "arxiv.org" in paper.get("url", "").lower():
                pdf_url = paper["url"].replace("/abs/", "/pdf/") + ".pdf"

            if pdf_url:
                safe_title = "".join([c for c in paper['title'] if c.isalnum() or c==' ']).strip()
                file_path = os.path.join(download_dir, f"{safe_title}.pdf")
                
                try:
                    print(f" -> Found PDF! Downloading...")
                    pdf_res = requests.get(pdf_url, stream=True, timeout=30)
                    pdf_res.raise_for_status()
                    
                    with open(file_path, "wb") as f:
                        for chunk in pdf_res.iter_content(chunk_size=8192):
                            f.write(chunk)
                    
                    paper["download_status"] = "Success"
                    downloaded_count += 1
                    print(f" -> Saved: {file_path}")
                except Exception as e:
                    paper["download_status"] = f"Download Failed: {e}"
                    print(f" -> Download failed.")
            else:
                paper["download_status"] = "No Open Access PDF"
                print(" -> No PDF available for this paper.")

            all_paper_data.append(paper)
            time.sleep(3)

    except Exception as e:
        print(f" -> API Search Error: {e}")

    print(f"\nFinished! Total downloaded: {downloaded_count}")
    return pd.DataFrame(all_paper_data)

if __name__ == "__main__":

    user_topic = "deep learning in robotics" 
    
    df_results = search_and_download_by_topic(user_topic, max_papers=5)
    
    if not df_results.empty:
        print("\nSearch Summary:")
        cols = [c for c in ["year", "title", "download_status"] if c in df_results.columns]
        print(df_results[cols].to_string(index=False))