import os               # Standard library to manage folders and files (create/delete)
import requests         # " Fetches data (PDFs) from the web(accesses the web)
from semanticscholar import SemanticScholar # The API client to search the database

# --- CONFIGURATION CONSTANTS ---
# Centralized settings make the code easier to maintain and tune later.
DOWNLOAD_DIR = "downloaded_papers"
MAX_PAPER_LIMIT = 10          # Safety Constraint: Prevents accidental bulk downloads that could fill disk space.
SEARCH_BUFFER_MULTIPLIER = 5  # Reliability Strategy: We search for 5x more papers than requested
                              # because many papers will be behind paywalls or have broken links.

def sanitize_filename(text):
    """
    UTILITY: Cleans a string to be used safely as a directory or file name.
    
    Why: Operating systems (Windows/Linux) have different illegal characters (like :, ?, /).
    This function prevents the script from crashing due to invalid file paths.
    """
    allowed_chars = set(' -_.()')
    clean_text = "".join(c for c in text if c.isalnum() or c in allowed_chars)
    return clean_text.strip()

def is_valid_pdf(file_path):
    """
    QUALITY CONTROL: Validates that a downloaded file is actually a usable PDF.
    not a downloaded web page or some sh@*
    
    Why: Sometimes a server returns a "403 Forbidden" HTML page instead of a PDF.
    This function detects those 'fake' PDFs so we don't pollute our dataset with bad data.
    """
    try:
        if not os.path.exists(file_path):
            return False
        
        # Check 1: Size Check. 
        # Files smaller than 1KB are almost always corrupt or empty error messages.
        if os.path.getsize(file_path) < 1000:
            return False
            
        # Check 2: Header Signature Check (Magic Number).
        # We read the first 4 bytes. A valid PDF MUST start with '%PDF'.
        with open(file_path, 'rb') as f:
            header = f.read(4)
            return header == b'%PDF'
    except IOError:
        return False

def download_file(url, save_path):
    """
    NETWORK LAYER: Handles the physical downloading of the file.
    Returns True if download AND validation are successful.          just theory 
    """
    # Anti-Blocking Strategy:
    # We send a 'User-Agent' header to mimic a real Chrome browser.
    # Many academic servers block requests that look like automated scripts (bots).
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    try:
        # Timeout Strategy:
        # We wait max 30 seconds. If the server hangs, we abort to prevent the script from freezing.
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status() # Raises an error if the web page sends a 404 or 500 error
        
        # Write binary data to disk
        with open(save_path, 'wb') as f:
            f.write(response.content)
            
        # Immediate Validation:
        # If the file we just downloaded is junk, delete it immediately.
        if is_valid_pdf(save_path):
            return True
        else:
            # Cleanup: Remove invalid file to keep folder clean
            os.remove(save_path)
            return False
            
    except (requests.RequestException, IOError):
        # Fail-safe: If network fails or file write fails, ensure no partial file remains.
        if os.path.exists(save_path):
            os.remove(save_path)
        return False

def setup_directory(topic):
    """
    FILE SYSTEM MANAGEMENT: Handles folder creation logic.
    Creates a specific sub-folder for the topic (e.g., 'downloaded_papers/AI_Agents')
    to keep research sessions isolated and organized.
    """
    safe_topic = sanitize_filename(topic)
    full_path = os.path.join(DOWNLOAD_DIR, safe_topic)
    
    if not os.path.exists(full_path):
        os.makedirs(full_path)
        print(f"[INFO] Created directory: {full_path}")
    else:
        print(f"[INFO] Using existing directory: {full_path}")
        
    return full_path

def process_paper_downloads(topic, target_count):
    """
    ORCHESTRATOR: The main logic loop.
    1. Searches for candidates.
    2. Filters for valid links.
    3. Manages the download loop until target count is met.
    """
    sch = SemanticScholar()
    
    # Strategy: Fetch more candidates than needed.
    # If user wants 3 papers, we search for 15 (3 * 5).
    # This ensures we hit our target even if many downloads fail.
    search_limit = target_count * SEARCH_BUFFER_MULTIPLIER
    print(f"[INFO] Searching for papers on '{topic}'...")
    
    # API Call to Semantic Scholar
    results = sch.search_paper(topic, limit=search_limit, open_access_pdf=True)
    save_directory = setup_directory(topic)
    
    downloaded_count = 0
    
    for paper in results:
        # Stop condition: We have enough papers.
        if downloaded_count >= target_count:
            break
            
        # Data Cleaning: Skip papers that don't have a direct PDF link.
        if not paper.openAccessPdf or not paper.openAccessPdf.get('url'):
            continue
            
        pdf_url = paper.openAccessPdf['url']
        safe_title = sanitize_filename(paper.title)
        file_path = os.path.join(save_directory, f"{safe_title}.pdf")
        
        # Efficiency: Don't re-download if we already have it.
        if os.path.exists(file_path):
            print(f"[SKIP] File already exists: {paper.title[:50]}...")
            downloaded_count += 1
            continue
            
        print(f"[DOWNLOAD] Attempting: {paper.title[:50]}...")
        
        # Attempt download
        success = download_file(pdf_url, file_path)
        
        if success:
            print(f"[SUCCESS] Saved: {safe_title}.pdf")
            downloaded_count += 1
        else:
            print(f"[FAILED] Could not retrieve or validate PDF. Skipping to next candidate.")
            
    return downloaded_count

def get_user_input():
    """
    UI/UX: Handles user interaction and validates inputs.
    Ensures the user provides a valid topic and a safe number of papers.
    """
    topic = input("Enter research topic: ").strip()
    if not topic:
        print("Error: Topic cannot be empty.")
        return None, None

    try:
        count_input = input(f"Enter number of papers to download (Max {MAX_PAPER_LIMIT}): ").strip()
        count = int(count_input)
        
        if count <= 0:
            print("Error: Number of papers must be greater than 0.")
            return None, None
            
        # Constraint Enforcement:
        if count > MAX_PAPER_LIMIT:
            print(f"Warning: Limit exceeded. Setting download count to {MAX_PAPER_LIMIT}.")
            count = MAX_PAPER_LIMIT
            
    except ValueError:
        print("Error: Please enter a valid number.")
        return None, None
        
    return topic, count

# --- ENTRY POINT ---
if __name__ == "__main__":
    topic, count = get_user_input()
    
    if topic and count:
        total_downloaded = process_paper_downloads(topic, count)
        
        if total_downloaded == 0:
            print("\n[RESULT] No valid papers were downloaded. Try a different topic.")
        else:
            print(f"\n[RESULT] Completed. {total_downloaded} papers saved in '{os.path.join(DOWNLOAD_DIR, sanitize_filename(topic))}'.")

