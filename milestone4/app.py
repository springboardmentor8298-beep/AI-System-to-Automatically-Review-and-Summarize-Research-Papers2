import os
import re
import json
import time
import random
import tempfile
import requests
import io
import shutil
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from flask import (
    Flask,
    render_template,
    request,
    jsonify,
    send_file,
    send_from_directory,
    make_response,
)
from flask_cors import CORS
import arxiv
import fitz  # PyMuPDF
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from config import LLM_PROVIDERS, SYSTEM_PROMPTS, APP_CONFIG

# Try to import optional LLM clients
try:
    from groq import Groq
except ImportError:
    Groq = None

try:
    import openai
except ImportError:
    openai = None

try:
    import anthropic
except ImportError:
    anthropic = None

app = Flask(__name__)
CORS(app)
app.config["SECRET_KEY"] = "your-secret-key-here-change-in-production"
app.config["MAX_CONTENT_LENGTH"] = APP_CONFIG["max_file_size_mb"] * 1024 * 1024

# Ensure directories exist
TEMP_DIR = APP_CONFIG["temp_dir"]
STORAGE_DIR = APP_CONFIG["storage_dir"]
os.makedirs(TEMP_DIR, exist_ok=True)
os.makedirs(STORAGE_DIR, exist_ok=True)

# Track downloaded papers with folder organization
downloaded_papers_cache = {}
current_topic_folder = None  # Track current topic folder

# Store analysis results - DO NOT store generator objects
analysis_cache = {}


# JSON Storage for persistence
class JSONStorage:
    @staticmethod
    def save_session(session_id, data):
        """Save session data to JSON file"""
        filepath = os.path.join(STORAGE_DIR, f"{session_id}.json")
        # Remove non-serializable objects before saving
        clean_data = JSONStorage._clean_for_json(data)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(clean_data, f, indent=2, default=str, ensure_ascii=False)
        return filepath

    @staticmethod
    def _clean_for_json(obj):
        """Remove non-serializable objects from dict"""
        if isinstance(obj, dict):
            return {
                k: JSONStorage._clean_for_json(v)
                for k, v in obj.items()
                if not callable(v) and not isinstance(v, (io.BytesIO, type))
            }
        elif isinstance(obj, list):
            return [JSONStorage._clean_for_json(item) for item in obj]
        return obj

    @staticmethod
    def load_session(session_id):
        """Load session data from JSON file"""
        filepath = os.path.join(STORAGE_DIR, f"{session_id}.json")
        if os.path.exists(filepath):
            with open(filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        return None

    @staticmethod
    def list_sessions():
        """List all stored sessions"""
        sessions = []
        for filename in os.listdir(STORAGE_DIR):
            if filename.endswith(".json"):
                session_id = filename[:-5]
                filepath = os.path.join(STORAGE_DIR, filename)
                stat = os.stat(filepath)
                sessions.append(
                    {
                        "id": session_id,
                        "created": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                        "size": stat.st_size,
                    }
                )
        return sorted(sessions, key=lambda x: x["created"], reverse=True)

    @staticmethod
    def delete_session(session_id):
        """Delete session file"""
        filepath = os.path.join(STORAGE_DIR, f"{session_id}.json")
        if os.path.exists(filepath):
            os.remove(filepath)
            return True
        return False


storage = JSONStorage()

# Thread pool for concurrent processing
executor = ThreadPoolExecutor(max_workers=5)


class MultiSourcePaperAPI:
    """Enhanced multi-source API with organized folder structure"""

    # Rate limiting configuration
    ARXIV_DELAY = 3  # seconds between arXiv requests
    SEMANTIC_SCHOLAR_DELAY = 1  # seconds between SS requests
    MAX_RETRIES = 3

    @staticmethod
    def _get_session():
        """Create requests session with retry strategy for 429 errors"""
        retry_strategy = Retry(
            total=MultiSourcePaperAPI.MAX_RETRIES,
            status_forcelist=[429, 500, 502, 503, 504],
            backoff_factor=2,
            raise_on_redirect=False,
            raise_on_status=False,
            respect_retry_after_header=True,
        )

        adapter = HTTPAdapter(max_retries=retry_strategy)
        session = requests.Session()
        session.mount("https://", adapter)
        session.mount("http://", adapter)

        session.headers.update(
            {
                "User-Agent": "AI-Research-Review-System/1.0 (Research Project)",
                "Accept": "application/json",
            }
        )

        return session

    @staticmethod
    def _sanitize_folder_name(topic):
        """Convert topic to safe folder name"""
        # Remove special characters, limit length
        safe_name = re.sub(r"[^\w\s-]", "", topic)
        safe_name = re.sub(r"[-\s]+", "_", safe_name)
        safe_name = safe_name[:50].strip("_")
        # Add timestamp to ensure uniqueness
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"{safe_name}_{timestamp}"

    @staticmethod
    def search_and_download(query, max_results=10):
        """Search papers with organized folder structure"""
        global current_topic_folder

        # Create organized folder structure
        papers_base_dir = os.path.join(STORAGE_DIR, "papers")
        os.makedirs(papers_base_dir, exist_ok=True)

        # Create topic-specific folder
        folder_name = MultiSourcePaperAPI._sanitize_folder_name(query)
        topic_folder = os.path.join(papers_base_dir, folder_name)
        os.makedirs(topic_folder, exist_ok=True)

        current_topic_folder = topic_folder  # Track for later use

        all_papers = []
        downloaded_count = 0
        session = MultiSourcePaperAPI._get_session()

        # Try arXiv first
        try:
            arxiv_papers = MultiSourcePaperAPI._search_arxiv(
                query, max_results, session
            )
            for idx, paper in enumerate(arxiv_papers):
                if downloaded_count >= max_results:
                    break
                try:
                    time.sleep(MultiSourcePaperAPI.ARXIV_DELAY)

                    # Create unique filename with index and paper ID
                    safe_id = re.sub(r"[^\w]", "_", paper["id"])[:50]
                    filename = f"{idx + 1:02d}_arxiv_{safe_id}.pdf"
                    filepath = os.path.join(topic_folder, filename)

                    # Skip if already exists (shouldn't happen with timestamp)
                    if not os.path.exists(filepath):
                        MultiSourcePaperAPI._download_arxiv_to_path(
                            paper["id"], filepath, session
                        )

                    paper["local_path"] = filepath
                    paper["filename"] = filename
                    paper["folder"] = folder_name
                    paper["download_path"] = f"/papers/{folder_name}/{filename}"
                    paper["downloaded"] = True
                    downloaded_papers_cache[paper["id"]] = {
                        "filepath": filepath,
                        "metadata": paper,
                    }
                    all_papers.append(paper)
                    downloaded_count += 1
                except Exception as e:
                    print(f"Error downloading arXiv paper {paper['id']}: {e}")
                    paper["downloaded"] = False
                    paper["error"] = str(e)
        except Exception as e:
            print(f"arXiv search error: {e}")

        # Fill remaining with Semantic Scholar
        if downloaded_count < max_results:
            try:
                remaining = max_results - downloaded_count
                ss_papers = MultiSourcePaperAPI._search_semantic_scholar(
                    query, remaining * 2, session
                )

                for idx, paper in enumerate(ss_papers):
                    if downloaded_count >= max_results:
                        break

                    # Skip duplicates
                    if any(
                        p.get("doi") == paper.get("doi") and paper.get("doi")
                        for p in all_papers
                    ):
                        continue

                    try:
                        if paper.get("pdf_url"):
                            time.sleep(MultiSourcePaperAPI.SEMANTIC_SCHOLAR_DELAY)

                            # Create unique filename
                            safe_id = re.sub(r"[^\w]", "_", paper["id"])[:50]
                            filename = (
                                f"{downloaded_count + 1:02d}_semantic_{safe_id}.pdf"
                            )
                            filepath = os.path.join(topic_folder, filename)

                            if not os.path.exists(filepath):
                                MultiSourcePaperAPI._download_direct_to_path(
                                    paper["pdf_url"], filepath, session
                                )

                            paper["local_path"] = filepath
                            paper["filename"] = filename
                            paper["folder"] = folder_name
                            paper["download_path"] = f"/papers/{folder_name}/{filename}"
                            paper["downloaded"] = True
                            downloaded_papers_cache[paper["id"]] = {
                                "filepath": filepath,
                                "metadata": paper,
                            }
                            all_papers.append(paper)
                            downloaded_count += 1
                    except Exception as e:
                        print(f"Error downloading SS paper {paper['id']}: {e}")
                        paper["downloaded"] = False
            except Exception as e:
                print(f"Semantic Scholar error: {e}")

        return all_papers[:max_results], folder_name

    @staticmethod
    def _search_arxiv(query, max_results, session):
        """Search arXiv with enhanced metadata"""
        time.sleep(random.uniform(0.5, 1.5))

        try:
            client = arxiv.Client(
                page_size=100,
                delay_seconds=3.0,
                num_retries=MultiSourcePaperAPI.MAX_RETRIES,
            )
            search = arxiv.Search(
                query=query,
                max_results=max_results * 2,
                sort_by=arxiv.SortCriterion.Relevance,
            )

            papers = []
            for result in client.results(search):
                papers.append(
                    {
                        "id": result.get_short_id(),
                        "title": result.title,
                        "authors": [author.name for author in result.authors],
                        "summary": result.summary,
                        "published": result.published.strftime("%Y-%m-%d"),
                        "year": result.published.year,
                        "pdf_url": result.pdf_url,
                        "primary_category": result.primary_category,
                        "doi": result.doi or "",
                        "source": "arXiv",
                        "citations": 0,
                        "journal_ref": result.journal_ref or "",
                    }
                )
            return papers
        except Exception as e:
            print(f"arXiv API error: {e}")
            return []

    @staticmethod
    def _search_semantic_scholar(query, max_results, session):
        """Search Semantic Scholar with citation data"""
        url = "https://api.core.ac.uk/v3/search/works?q=your_query"
        params = {
            "query": query,
            "limit": min(max_results, 100),
            "fields": "title,year,authors,abstract,citationCount,openAccessPdf,externalIds,journal,venue",
        }

        time.sleep(random.uniform(0.5, 1.0))

        try:
            response = session.get(url, params=params, timeout=30)

            if response.status_code == 429:
                retry_after = int(response.headers.get("Retry-After", 60))
                print(
                    f"Semantic Scholar rate limited. Waiting {retry_after} seconds..."
                )
                time.sleep(retry_after)
                response = session.get(url, params=params, timeout=30)

            response.raise_for_status()
            data = response.json()

            papers = []
            for paper in data.get("data", []):
                authors = [
                    a.get("name", "Unknown") for a in paper.get("authors", [])[:5]
                ]
                oa_pdf = paper.get("openAccessPdf")
                pdf_url = oa_pdf.get("url") if oa_pdf else None

                papers.append(
                    {
                        "id": paper.get("paperId", "")[:20],
                        "title": paper.get("title", "Untitled"),
                        "authors": authors if authors else ["Unknown Author"],
                        "summary": paper.get("abstract") or "No abstract available",
                        "published": str(paper.get("year"))
                        if paper.get("year")
                        else "Unknown",
                        "year": paper.get("year"),
                        "pdf_url": pdf_url,
                        "primary_category": paper.get("venue", "research-paper"),
                        "doi": paper.get("externalIds", {}).get("DOI", ""),
                        "source": "Semantic Scholar",
                        "citations": paper.get("citationCount", 0),
                        "journal": paper.get("journal", {}).get("name", "")
                        if paper.get("journal")
                        else "",
                    }
                )
            return papers

        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:
                print(
                    "Semantic Scholar: Rate limit exceeded. Consider getting an API key."
                )
            raise

    @staticmethod
    def _download_arxiv_to_path(paper_id, filepath, session):
        """Download arXiv paper to specific path"""
        time.sleep(MultiSourcePaperAPI.ARXIV_DELAY)

        client = arxiv.Client(
            page_size=100,
            delay_seconds=3.0,
            num_retries=MultiSourcePaperAPI.MAX_RETRIES,
        )
        search = arxiv.Search(id_list=[paper_id])
        paper = next(client.results(search))

        # Download to temp first, then move
        temp_dir = tempfile.mkdtemp()
        temp_file = paper.download_pdf(dirpath=temp_dir)
        shutil.move(temp_file, filepath)
        shutil.rmtree(temp_dir)

    @staticmethod
    def _download_direct_to_path(pdf_url, filepath, session):
        """Download PDF to specific path"""
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "application/pdf,*/*",
        }

        time.sleep(random.uniform(1, 2))

        response = session.get(
            pdf_url, headers=headers, timeout=60, allow_redirects=True
        )

        if response.status_code == 429:
            retry_after = int(response.headers.get("Retry-After", 30))
            print(f"PDF download rate limited. Waiting {retry_after} seconds...")
            time.sleep(retry_after)
            response = session.get(
                pdf_url, headers=headers, timeout=60, allow_redirects=True
            )

        response.raise_for_status()

        content_type = response.headers.get("content-type", "")
        if "pdf" not in content_type.lower():
            if not response.content.startswith(b"%PDF"):
                raise Exception("Downloaded file is not a PDF")

        with open(filepath, "wb") as f:
            f.write(response.content)


class RobustPaperProcessor:
    """Enhanced paper text extraction with robust PDF handling"""

    @staticmethod
    def extract_text(pdf_path, max_retries=3):
        """Extract text with advanced section detection and retry logic"""
        for attempt in range(max_retries):
            try:
                if not os.path.exists(pdf_path):
                    raise Exception(f"PDF not found: {pdf_path}")

                # Try PyMuPDF first
                result = RobustPaperProcessor._extract_with_pymupdf(pdf_path)

                # If extraction is too short, try OCR or alternative methods
                if len(result["full_text"]) < 1000 and attempt < max_retries - 1:
                    print(
                        f"Extraction too short, retrying... ({attempt + 1}/{max_retries})"
                    )
                    continue

                return result

            except Exception as e:
                if attempt == max_retries - 1:
                    # Return error structure but don't crash
                    return {
                        "full_text": f"Error extracting PDF: {str(e)}",
                        "abstract": "",
                        "introduction": "",
                        "methods": "",
                        "results": "",
                        "discussion": "",
                        "conclusion": "",
                        "references": "",
                        "keywords": "",
                        "funding": "",
                        "conflicts": "",
                        "error": str(e),
                    }
                print(f"Extraction attempt {attempt + 1} failed: {e}, retrying...")
                continue

    @staticmethod
    def _extract_with_pymupdf(pdf_path):
        """Extract using PyMuPDF with enhanced section detection"""
        doc = fitz.open(pdf_path)
        full_text = ""
        raw_pages = []

        # Extract text from all pages with structure preservation
        for page_num in range(len(doc)):
            page = doc[page_num]
            text = page.get_text()
            raw_pages.append(text)
            full_text += f"\n--- Page {page_num + 1} ---\n"
            full_text += text

        doc.close()

        # Enhanced structural segmentation
        sections = {
            "full_text": full_text[:25000],
            "abstract": "",
            "introduction": "",
            "methods": "",
            "results": "",
            "discussion": "",
            "conclusion": "",
            "references": "",
            "keywords": "",
            "funding": "",
            "conflicts": "",
        }

        # Multi-pattern extraction for robustness
        extraction_patterns = {
            "abstract": [
                r"(?i)abstract\s*[:\n]\s*(.*?)(?=\n\s*(?:introduction|keywords|1\.|i\.|$))",
                r"(?i)summary\s*[:\n]\s*(.*?)(?=\n\s*(?:introduction|1\.|$))",
            ],
            "introduction": [
                r"(?i)(?:introduction|background)\s*[:\n]\s*(.*?)(?=\n\s*(?:methods|methodology|materials|2\.|$))",
            ],
            "methods": [
                r"(?i)(?:methods|methodology|materials and methods|experimental setup)\s*[:\n]\s*(.*?)(?=\n\s*(?:results|findings|3\.|$))",
            ],
            "results": [
                r"(?i)(?:results|findings|experimental results)\s*[:\n]\s*(.*?)(?=\n\s*(?:discussion|conclusion|4\.|$))",
            ],
            "discussion": [
                r"(?i)(?:discussion)\s*[:\n]\s*(.*?)(?=\n\s*(?:conclusion|limitations|5\.|$))",
            ],
            "conclusion": [
                r"(?i)(?:conclusion|conclusions|summary and conclusion)\s*[:\n]\s*(.*?)(?=\n\s*(?:references|acknowledgments|appendix|$))",
            ],
            "keywords": [
                r"(?i)keywords[:\s]*(.*?)(?=\n\s*(?:introduction|1\.|$))",
            ],
        }

        for section, patterns in extraction_patterns.items():
            for pattern in patterns:
                match = re.search(pattern, full_text, re.DOTALL)
                if match:
                    content = match.group(1).strip()
                    # Limit section length but keep more content
                    limit = 4000 if section in ["methods", "results"] else 3000
                    sections[section] = content[:limit]
                    break

        return sections


class LLMManager:
    """Optimized LLM manager with batch processing"""

    @staticmethod
    def get_available_providers():
        """Return configured providers"""
        available = []
        for name, config in LLM_PROVIDERS.items():
            api_key = config.get("api_key", "")
            if (
                api_key
                and not api_key.endswith("_here")
                and "your" not in api_key.lower()
            ):
                available.append(
                    {
                        "id": name,
                        "name": config.get("display_name", name.upper()),
                        "models": config["models"],
                        "default_model": config["default_model"],
                    }
                )
        return available

    @staticmethod
    def generate_completion(
        provider, model, messages, temperature=0.7, max_tokens=4000
    ):
        """Generate completion with retry logic"""
        config = LLM_PROVIDERS.get(provider)
        if not config:
            raise ValueError(f"Provider {provider} not configured")

        api_key = config["api_key"]
        base_url = config["base_url"]

        max_retries = 6
        for attempt in range(max_retries):
            try:
                if provider == "groq" and Groq:
                    client = Groq(api_key=api_key)
                    response = client.chat.completions.create(
                        model=model or config["default_model"],
                        messages=messages,
                        temperature=temperature,
                        max_tokens=max_tokens,
                    )
                    return response.choices[0].message.content

                elif provider == "openai" and openai:
                    client = openai.OpenAI(api_key=api_key, base_url=base_url)
                    response = client.chat.completions.create(
                        model=model or config["default_model"],
                        messages=messages,
                        temperature=temperature,
                        max_tokens=max_tokens,
                    )
                    return response.choices[0].message.content

                elif provider == "anthropic" and anthropic:
                    client = anthropic.Anthropic(api_key=api_key)
                    system_msg = ""
                    user_messages = []
                    for msg in messages:
                        if msg["role"] == "system":
                            system_msg = msg["content"]
                        else:
                            user_messages.append(
                                {"role": msg["role"], "content": msg["content"]}
                            )

                    response = client.messages.create(
                        model=model or config["default_model"],
                        max_tokens=max_tokens,
                        temperature=temperature,
                        system=system_msg,
                        messages=user_messages,
                    )
                    return response.content[0].text

                else:
                    headers = {
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json",
                    }

                    if provider == "openrouter":
                        headers["HTTP-Referer"] = "https://research-review-system.local"
                        headers["X-Title"] = "AI Research Review System"

                    data = {
                        "model": model or config["default_model"],
                        "messages": messages,
                        "temperature": temperature,
                        "max_tokens": max_tokens,
                    }

                    response = requests.post(
                        f"{base_url}/chat/completions",
                        headers=headers,
                        json=data,
                        timeout=APP_CONFIG["llm_timeout"],
                    )
                    response.raise_for_status()
                    result = response.json()

                    if "choices" in result and len(result["choices"]) > 0:
                        return result["choices"][0]["message"]["content"]
                    else:
                        raise Exception(f"Unexpected response: {result}")

            except Exception as e:
                if attempt == max_retries - 1:
                    raise Exception(
                        f"Error with {provider} after {max_retries} attempts: {str(e)}"
                    )
                continue


# Import processing modules from milestones.py
from milestones import ReviewGenerator, PDFGenerator, register_milestone_routes


# Flask Routes - Milestones 1-2 (Search and Extraction)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/providers", methods=["GET"])
def get_providers():
    return jsonify({"providers": LLMManager.get_available_providers()})


@app.route("/api/search", methods=["POST"])
def search_papers():
    """Milestone 1: Paper Retrieval with organized folders"""
    data = request.json
    query = data.get("query", "").strip()
    max_results = min(int(data.get("max_results", 5)), APP_CONFIG["max_papers_limit"])

    if not query:
        return jsonify({"error": "Query required"}), 400

    try:
        papers, folder_name = MultiSourcePaperAPI.search_and_download(
            query, max_results
        )

        if not papers:
            return jsonify({"error": "No papers found. Try different keywords."}), 404

        display_papers = [
            {
                "id": p["id"],
                "title": p["title"],
                "authors": p["authors"],
                "summary": p["summary"],
                "published": p["published"],
                "year": p.get("year"),
                "primary_category": p["primary_category"],
                "source": p["source"],
                "citations": p.get("citations", 0),
                "doi": p.get("doi", ""),
                "journal": p.get("journal", ""),
                "filename": p.get("filename"),
                "folder": p.get("folder"),
                "download_path": p.get("download_path"),
                "local_path": p.get("local_path"),
            }
            for p in papers
        ]

        session_id = f"search_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        storage.save_session(
            session_id,
            {
                "type": "search",
                "query": query,
                "folder": folder_name,
                "papers": display_papers,
                "timestamp": datetime.now().isoformat(),
            },
        )

        return jsonify(
            {
                "papers": display_papers,
                "folder": folder_name,
                "count": len(display_papers),
                "session_id": session_id,
                "message": f"Downloaded {len(display_papers)} papers to folder: {folder_name}",
            }
        )

    except Exception as e:
        import traceback

        print(f"Search error: {e}")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@app.route("/papers/<folder>/<filename>")
def serve_paper(folder, filename):
    """Serve PDF file from papers folder"""
    papers_dir = os.path.join(STORAGE_DIR, "papers")
    folder_path = os.path.join(papers_dir, folder)

    # Security check: ensure path is within papers directory
    real_folder_path = os.path.realpath(folder_path)
    real_papers_dir = os.path.realpath(papers_dir)

    if not real_folder_path.startswith(real_papers_dir):
        return jsonify({"error": "Invalid path"}), 403

    file_path = os.path.join(folder_path, filename)
    real_file_path = os.path.realpath(file_path)

    if not real_file_path.startswith(real_folder_path):
        return jsonify({"error": "Invalid file path"}), 403

    if not os.path.exists(file_path):
        return jsonify({"error": "File not found"}), 404

    return send_from_directory(folder_path, filename)


@app.route("/api/paper/<paper_id>/view")
def view_paper(paper_id):
    """Get PDF viewer URL for a paper"""
    paper_info = downloaded_papers_cache.get(paper_id, {})
    metadata = paper_info.get("metadata", {})

    if metadata.get("download_path"):
        return jsonify(
            {
                "view_url": metadata["download_path"],
                "title": metadata.get("title", "Paper"),
                "filename": metadata.get("filename", "paper.pdf"),
            }
        )

    return jsonify({"error": "Paper not found"}), 404


@app.route("/api/analyze", methods=["POST"])
def analyze_papers():
    """Milestone 2: Analysis Phase Endpoint"""
    data = request.json
    paper_ids = data.get("paper_ids", [])
    provider = data.get("provider", "groq")
    model = data.get("model")
    mode = data.get("mode", "detailed")

    if not paper_ids:
        return jsonify({"error": "No papers selected"}), 400

    if len(paper_ids) > APP_CONFIG["max_papers_limit"]:
        return jsonify(
            {"error": f"Maximum {APP_CONFIG['max_papers_limit']} papers allowed"}
        ), 400

    try:
        generator = ReviewGenerator(provider, model, mode=mode)

        # Pass downloaded_papers_cache to extract_and_structure
        extracted = generator.extract_and_structure(paper_ids, downloaded_papers_cache)
        if not extracted:
            return jsonify({"error": "Could not extract papers"}), 400

        # Pass LLMManager and SYSTEM_PROMPTS to analyze_papers_batch
        analyses = generator.analyze_papers_batch(LLMManager, SYSTEM_PROMPTS)

        # Store in cache
        cache_key = request.remote_addr
        cache_data = {
            "analyses": analyses,
            "extracted": extracted,
            "mode": mode,
            "provider": provider,
            "model": model,
            "timestamp": datetime.now().isoformat(),
        }
        analysis_cache[cache_key] = cache_data

        # Save to persistent storage
        session_id = f"analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        storage.save_session(session_id, cache_data)

        return jsonify(
            {
                "phase": "analysis",
                "extracted_papers": len(extracted),
                "analyses": analyses,
                "mode": mode,
                "session_id": session_id,
                "extraction_details": [
                    {
                        "id": p["id"],
                        "title": p["title"],
                        "word_count": len(p["sections"]["full_text"].split()),
                        "sections_found": [
                            k
                            for k, v in p["sections"].items()
                            if v and k != "full_text"
                        ],
                    }
                    for p in extracted
                ],
            }
        )

    except Exception as e:
        import traceback

        print(f"Error in analyze_papers: {e}")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


# Register Milestones 3-4 routes
register_milestone_routes(
    app,
    analysis_cache,
    storage,
    LLMManager,
    ReviewGenerator,
    PDFGenerator,
    SYSTEM_PROMPTS,
    APP_CONFIG,
    TEMP_DIR,
)


@app.route("/api/sessions", methods=["GET"])
def list_sessions():
    """List all stored sessions"""
    try:
        sessions = storage.list_sessions()
        return jsonify({"sessions": sessions})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/sessions/<session_id>", methods=["GET"])
def get_session(session_id):
    """Load a specific session"""
    try:
        data = storage.load_session(session_id)
        if data:
            return jsonify(data)
        return jsonify({"error": "Session not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/sessions/<session_id>", methods=["DELETE"])
def delete_session(session_id):
    """Delete a session"""
    try:
        if storage.delete_session(session_id):
            return jsonify({"message": "Session deleted"})
        return jsonify({"error": "Session not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    print("🚀 AI Research Review System - Enhanced Edition")
    print(f"📁 Temp: {TEMP_DIR}")
    print(f"💾 Storage: {STORAGE_DIR}")
    print(f"📄 Papers: {os.path.join(STORAGE_DIR, 'papers')}")
    print(f"🔧 Max Papers: {APP_CONFIG['max_papers_limit']}")
    print(f"⚡ Batch Processing Enabled")
    print(f"📝 Modes: Detailed (500-700w) & Concise (150-200w)")
    print(f"💾 JSON Export Enabled")
    app.run(debug=True, host="0.0.0.0", port=5000, threaded=True)
