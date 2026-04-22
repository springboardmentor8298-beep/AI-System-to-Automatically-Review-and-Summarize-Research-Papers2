7849062335
import os
import json
import re
from pathlib import Path
from io import BytesIO

from flask import Flask, render_template, request, redirect, url_for, session, send_file
import fitz
import requests
import feedparser
from pydantic import BaseModel
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

app = Flask(__name__)
app.secret_key = "systematic-review-secret-2026"

# ========================= GROQ =========================
os.environ["GROQ_API_KEY"] = ""  # ← CHANGE TO YOUR REAL GROQ KEY

llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0.2, max_tokens=4096)

BASE_DIR = "papers"
METADATA_FILE = "papers_metadata.json"
ANALYSIS_FILE = "analysis_results.json"
DRAFT_FILE = "systematic_review_draft.json"

SECTION_HEADERS = [
    "abstract",
    "introduction",
    "method",
    "methods",
    "methodology",
    "results",
    "discussion",
    "conclusion",
]


class PaperAnalysis(BaseModel):
    paper_id: str
    title: str
    authors: list
    pdf_path: str
    sections: dict
    key_findings: list


# ========================= SEARCH & DOWNLOAD =========================
def search_and_download_papers(topic: str, max_results: int):
    ARXIV_URL = "http://export.arxiv.org/api/query"
    params = {"search_query": f"all:{topic}", "max_results": max_results}
    metadata = []

    safe_topic = "".join(c if c.isalnum() else "_" for c in topic)
    folder = Path(BASE_DIR) / safe_topic
    folder.mkdir(parents=True, exist_ok=True)

    try:
        feed = feedparser.parse(requests.get(ARXIV_URL, params=params, timeout=20).text)
        for i, entry in enumerate(feed.entries, 1):
            title = entry.title
            authors = [a.name for a in getattr(entry, "authors", [])]
            pdf_url = entry.id.replace("abs", "pdf")
            filename = f"paper_{i}_{''.join(c if c.isalnum() else '_' for c in title[:50])}.pdf"
            filepath = folder / filename

            pdf_path = None
            status = " Failed"
            try:
                r = requests.get(pdf_url, timeout=25)
                if r.status_code == 200:
                    filepath.write_bytes(r.content)
                    pdf_path = str(filepath)
                    status = " arXiv"
            except:
                pass

            metadata.append(
                {
                    "paper_id": f"arxiv_{i}",
                    "title": title,
                    "authors": authors,
                    "pdf_path": pdf_path,
                    "status": status,
                    "source": "arXiv",
                }
            )
    except:
        pass

    success_count = sum(1 for m in metadata if m.get("pdf_path"))
    if success_count < max_results // 2:
        print("Switching to Semantic Scholar API...")
        SEM_URL = "https://api.semanticscholar.org/graph/v1/paper/search"
        params = {
            "query": topic,
            "limit": max_results,
            "fields": "title,authors,openAccessPdf",
        }
        try:
            data = requests.get(SEM_URL, params=params, timeout=15).json()
            for i, p in enumerate(data.get("data", []), len(metadata) + 1):
                title = p.get("title", "Untitled")
                authors = [a.get("name") for a in p.get("authors", [])]
                pdf_url = p.get("openAccessPdf", {}).get("url")
                filename = f"paper_s2_{i}.pdf"
                filepath = folder / filename
                pdf_path = None
                status = " No PDF"
                if pdf_url:
                    try:
                        r = requests.get(pdf_url, timeout=20)
                        if r.status_code == 200:
                            filepath.write_bytes(r.content)
                            pdf_path = str(filepath)
                            status = " Semantic Scholar"
                    except:
                        pass
                metadata.append(
                    {
                        "paper_id": f"s2_{i}",
                        "title": title,
                        "authors": authors,
                        "pdf_path": pdf_path,
                        "status": status,
                        "source": "Semantic Scholar",
                    }
                )
        except:
            pass

    Path(METADATA_FILE).write_text(json.dumps(metadata, indent=4), encoding="utf-8")
    return metadata[:max_results]


# ========================= MILESTONE 2 =========================
def extract_pdf_text(pdf_path):
    try:
        doc = fitz.open(pdf_path)
        text = "".join(page.get_text() for page in doc)
        doc.close()
        return text
    except:
        return ""


def segment_sections(text):
    sections = {}
    text_lower = text.lower()
    for header in SECTION_HEADERS:
        pattern = r"(?i)^\s*" + re.escape(header) + r"\b"
        matches = list(re.finditer(pattern, text_lower, re.MULTILINE))
        if matches:
            start = matches[0].start()
            next_start = len(text)
            for other in SECTION_HEADERS:
                if other == header:
                    continue
                nm = list(
                    re.finditer(
                        r"(?i)^\s*" + re.escape(other) + r"\b",
                        text_lower[start + 1 :],
                        re.MULTILINE,
                    )
                )
                if nm:
                    next_start = start + 1 + nm[0].start()
                    break
            sec = text[start:next_start].strip()
            if sec:
                sections[header] = sec
    return sections


def extract_key_findings(text):
    if not text:
        return []
    sentences = re.split(r"[.!?]\s+", text)
    keywords = [
        "improve",
        "increase",
        "outperform",
        "better",
        "significant",
        "achieve",
        "higher",
        "result",
    ]
    return [
        s.strip()
        for s in sentences
        if len(s.strip()) > 30 and any(k in s.lower() for k in keywords)
    ][:10]


def analyze_selected_papers(selected_paths, metadata):
    papers = []
    for m in metadata:
        if m.get("pdf_path") and m["pdf_path"] in selected_paths:
            text = extract_pdf_text(m["pdf_path"])
            sections = segment_sections(text)
            results_text = sections.get("results") or sections.get("discussion") or ""
            findings = extract_key_findings(results_text)
            papers.append(
                PaperAnalysis(
                    paper_id=m["paper_id"],
                    title=m["title"],
                    authors=m["authors"],
                    pdf_path=m["pdf_path"],
                    sections=sections,
                    key_findings=findings,
                )
            )
    Path(ANALYSIS_FILE).write_text(
        json.dumps({"papers": [p.model_dump() for p in papers]}, indent=4),
        encoding="utf-8",
    )
    return papers


# ========================= DRAFT GENERATION =========================
def generate_draft(topic, papers):
    formatted = []
    for i, p in enumerate(papers, 1):
        findings_str = "\n".join([f"• {f}" for f in p.key_findings])
        methods_str = p.sections.get("methods", p.sections.get("method", ""))[:600]
        formatted.append(
            f"Paper {i}: {p.title}\nAuthors: {', '.join(p.authors)}\nMethods: {methods_str}\nKey Findings:\n{findings_str}"
        )

    papers_info = "\n\n".join(formatted)
    papers_list = "\n".join([f"{p.title}. {', '.join(p.authors)}." for p in papers])

    prompts = {
        "abstract": ChatPromptTemplate.from_template(
            "Write a detailed academic abstract of 280 to 320 words for a systematic review on: {topic}. "
            "Include clear purpose, methodology overview, synthesis of key findings from all papers, "
            "and important implications. Make it scholarly and coherent.\n\nPapers:\n{papers_info}"
        ),
        "methods": ChatPromptTemplate.from_template(
            "Write a precise 'Methods Comparison' section for the review on: {topic}\n\n{papers_info}"
        ),
        "results": ChatPromptTemplate.from_template(
            "Write a comprehensive 'Results Synthesis' section. Integrate key findings from all papers on: {topic}. "
            "Highlight common themes, differences, and important insights.\n\n{papers_info}"
        ),
        "apa": ChatPromptTemplate.from_template(
            "Format these papers as APA 7th edition references (sorted alphabetically):\n{papers_list}"
        ),
    }

    draft = {
        "title": f"Systematic Review: {topic}",
        "abstract": (prompts["abstract"] | llm | StrOutputParser())
        .invoke({"topic": topic, "papers_info": papers_info})
        .strip(),
        "methods_comparison": (prompts["methods"] | llm | StrOutputParser())
        .invoke({"topic": topic, "papers_info": papers_info})
        .strip(),
        "results_synthesis": (prompts["results"] | llm | StrOutputParser())
        .invoke({"topic": topic, "papers_info": papers_info})
        .strip(),
        "references": (prompts["apa"] | llm | StrOutputParser())
        .invoke({"papers_list": papers_list})
        .strip(),
        "papers_reviewed": [
            {"title": p.title, "authors": ", ".join(p.authors)} for p in papers
        ],
    }
    Path(DRAFT_FILE).write_text(json.dumps(draft, indent=4), encoding="utf-8")
    return draft


# ========================= PDF GENERATION =========================
def generate_review_pdf(draft):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "Title", parent=styles["Title"], fontSize=18, spaceAfter=30
    )
    heading_style = ParagraphStyle(
        "Heading", parent=styles["Heading2"], fontSize=14, spaceAfter=12
    )
    normal_style = styles["Normal"]

    story = []
    story.append(Paragraph(draft["title"], title_style))
    story.append(Spacer(1, 20))

    # Papers Reviewed Section
    story.append(Paragraph("Papers Reviewed", heading_style))
    for p in draft.get("papers_reviewed", []):
        story.append(Paragraph(f"• {p['title']} ({p['authors']})", normal_style))
    story.append(Spacer(1, 25))

    story.append(Paragraph("Abstract", heading_style))
    story.append(Paragraph(draft["abstract"], normal_style))
    story.append(Spacer(1, 25))

    story.append(Paragraph("Methods Comparison", heading_style))
    story.append(
        Paragraph(draft["methods_comparison"].replace("\n", "<br/>"), normal_style)
    )
    story.append(Spacer(1, 25))

    story.append(Paragraph("Results Synthesis", heading_style))
    story.append(
        Paragraph(draft["results_synthesis"].replace("\n", "<br/>"), normal_style)
    )
    story.append(Spacer(1, 25))

    story.append(Paragraph("References (APA 7th Edition)", heading_style))
    story.append(Paragraph(draft["references"].replace("\n", "<br/>"), normal_style))

    doc.build(story)
    buffer.seek(0)
    return buffer


# ========================= ROUTES =========================
@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        topic = request.form["topic"].strip()
        max_papers = int(request.form.get("max_papers", 10))
        metadata = search_and_download_papers(topic, max_papers)
        session["topic"] = topic
        session["metadata"] = metadata
        return render_template("index.html", step=2, metadata=metadata, topic=topic)
    return render_template("index.html", step=1)


@app.route("/analyze", methods=["POST"])
def analyze():
    topic = session.get("topic")
    selected_ids = request.form.getlist("selected_papers")
    metadata = session.get("metadata", [])

    selected_paths = [
        m["pdf_path"]
        for m in metadata
        if m["paper_id"] in selected_ids and m.get("pdf_path")
    ]

    if not selected_paths:
        return (
            "<h3 class='text-danger'>Please select at least one paper</h3><a href='/'>← Go Back</a>",
            400,
        )

    papers = analyze_selected_papers(selected_paths, metadata)
    draft = generate_draft(topic, papers)
    session["draft"] = draft
    return redirect(url_for("results"))


@app.route("/results")
def results():
    draft = session.get("draft")
    if not draft:
        return redirect(url_for("index"))
    return render_template("results.html", draft=draft, topic=session.get("topic"))


@app.route("/download_pdf")
def download_pdf():
    draft = session.get("draft")
    if not draft:
        return "No draft found. Please generate first.", 404
    pdf_buffer = generate_review_pdf(draft)
    return send_file(
        pdf_buffer,
        as_attachment=True,
        download_name="systematic_review.pdf",
        mimetype="application/pdf",
    )


@app.route("/download_json")
def download_json():
    if Path(DRAFT_FILE).exists():
        return send_file(
            DRAFT_FILE, as_attachment=True, download_name="systematic_review_draft.json"
        )
    return "Draft not found", 404


@app.route("/regenerate", methods=["POST"])
def regenerate():
    topic = session.get("topic")
    metadata = session.get("metadata", [])
    selected_paths = [m["pdf_path"] for m in metadata if m.get("pdf_path")]
    papers = analyze_selected_papers(selected_paths, metadata)
    draft = generate_draft(topic, papers)
    session["draft"] = draft
    return redirect(url_for("results"))


if __name__ == "__main__":
    app.run(debug=True)
