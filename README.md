# AI-System-to-Automatically-Review-and-Summarize-Research-Papers2

## 📂 Milestone 1: Automated Academic Paper Ingestion

A robust ingestion script that automates the **search, validation, and storage** of open-access academic papers.  
The system performs staged processing—fetching metadata from the Semantic Scholar API, downloading binary PDF content, and applying **header-level validation (Magic Number checks)** to ensure that only genuine, usable PDFs are stored locally.

### Key Features
- Programmatic discovery of research papers using the Semantic Scholar API
- Safe file and directory handling with filename sanitization
- Network reliability handling (timeouts, HTTP error detection, bot-mitigation headers)
- PDF integrity verification using file size checks and magic number validation (`%PDF`)
- Automatic cleanup of corrupt or invalid downloads
- Topic-wise organization of validated papers

---

### ⚙️ Setup & Run

#### 1. Create & Activate Virtual Environment
```bash
python -m venv venv
# Windows
.\venv\Scripts\activate
# macOS / Linux
source venv/bin/activate
```
### 2. Install Dependencies
```bash
pip install requests semanticscholar
```
#### 3. Execute Script
```bash
python milestone1.py
```
-When prompted, enter:
(1) A research topic.
(2) The number of papers to download (bounded by a safety limit)

Successfully downladed papers are saved in folder``` downloaded_papers/<sanitized_topic_name>/```

I HAVE ALSO INCLUDED COMMENTS IN MY CODE , FEEL FREE TO READ THROUGH AND IGNORE ANY SPELLING OR TECHNICAL MISTAKE AS IT WAS FOR MY BASIC UNDERSTAND AND MAY ONLY CONTAIN KEYWORDS.

###ADIOS!!!

