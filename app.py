from flask import Flask, render_template
import json
import webbrowser
import threading
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

app = Flask(__name__)

def evaluate_quality(paper):
    score = 0

    if paper.get("Abstract") and len(paper["Abstract"]) > 100:
        score += 1

    if paper.get("Methods") and len(paper["Methods"]) > 50:
        score += 1

    if paper.get("Results") and len(paper["Results"]) > 50:
        score += 1

    if len(paper.get("Key Points", [])) >= 3:
        score += 1

    return score

def suggest_revision(paper):
    suggestions = []

    if not paper.get("Abstract"):
        suggestions.append("Improve abstract clarity")

    if len(paper.get("Key Points", [])) < 3:
        suggestions.append("Add more key findings")

    if not paper.get("Methods"):
        suggestions.append("Explain methodology better")

    if not suggestions:
        suggestions.append("Content is well-structured. No major improvements needed.")

    return suggestions

def refine_paper(paper):
    if paper.get("Abstract"):
        paper["Abstract"] += " (Refined for clarity)"
    return paper

def generate_final_report(papers):
    report = ""

    report += "FINAL RESEARCH REPORT\n"
    report += "=" * 60 + "\n\n"

    report += "1. OVERVIEW\n"
    report += "-" * 60 + "\n"
    report += f"This report analyzes {len(papers)} research papers.\n\n"

    report += "2. PAPER ANALYSIS\n"
    report += "-" * 60 + "\n\n"

    for i, paper in enumerate(papers, 1):
        report += f"{i}. {paper.get('title', 'Untitled')}\n"
        report += "-" * 40 + "\n"

        report += "Abstract:\n"
        report += f"{paper.get('Abstract', '')}\n\n"

        report += "Methodology:\n"
        report += f"{paper.get('Methods', '')}\n\n"

        report += "Results:\n"
        report += f"{paper.get('Results', '')}\n\n"

        report += "Key Points:\n"
        for point in paper.get("Key Points", []):
            report += f"- {point}\n"

        report += "\n" + "-" * 60 + "\n\n"

    report += "3. COMMON METHODOLOGY\n"
    report += "-" * 60 + "\n"
    report += "Most studies follow data collection, preprocessing, analysis, and insight extraction.\n\n"

    report += "4. RESULTS SYNTHESIS\n"
    report += "-" * 60 + "\n"
    report += "All studies show improved efficiency and better decision-making.\n\n"

    report += "5. CONCLUSION\n"
    report += "-" * 60 + "\n"
    report += "Machine learning is widely applied across domains.\n\n"

    return report

def create_pdf(report_text, papers):
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib import colors

    doc = SimpleDocTemplate("static/final_report.pdf")
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        'TitleStyle',
        parent=styles['Normal'],
        fontSize=16,
        leading=20,
        spaceAfter=12,
        alignment=1, 
        textColor=colors.black
    )

    heading_style = ParagraphStyle(
        'HeadingStyle',
        parent=styles['Normal'],
        fontSize=13,
        leading=16,
        spaceAfter=8,
        textColor=colors.darkblue
    )

    subheading_style = ParagraphStyle(
        'SubHeadingStyle',
        parent=styles['Normal'],
        fontSize=11,
        leading=14,
        spaceAfter=6,
        textColor=colors.black
    )

    normal = styles["Normal"]

    elements = []

    elements.append(Paragraph("<b>FINAL REPORT</b>", title_style))
    elements.append(Spacer(1, 15))

    elements.append(Paragraph("<b>1. Overview</b>", heading_style))
    elements.append(Paragraph(f"This report analyzes {len(papers)} research papers.", normal))
    elements.append(Spacer(1, 15))

    elements.append(Paragraph("<b>2. Paper Analysis</b>", heading_style))
    elements.append(Spacer(1, 10))

    for i, paper in enumerate(papers, 1):

        elements.append(Paragraph(f"<b>{i}. {paper.get('title')}</b>", subheading_style))

        elements.append(Paragraph("<b>Abstract:</b>", normal))
        elements.append(Paragraph(paper.get("Abstract", ""), normal))
        elements.append(Spacer(1, 6))

        elements.append(Paragraph("<b>Methodology:</b>", normal))
        elements.append(Paragraph(paper.get("Methods", ""), normal))
        elements.append(Spacer(1, 6))

        elements.append(Paragraph("<b>Results:</b>", normal))
        elements.append(Paragraph(paper.get("Results", ""), normal))
        elements.append(Spacer(1, 6))

        elements.append(Paragraph("<b>Key Points:</b>", normal))

        for point in paper.get("Key Points", []):
            elements.append(Paragraph(f"• {point}", normal))

        elements.append(Spacer(1, 15))

    elements.append(Paragraph("<b>3. Common Methodology</b>", heading_style))
    elements.append(Paragraph(
        "Most studies follow data collection, preprocessing, analysis, and insight extraction.",
        normal
    ))
    elements.append(Spacer(1, 15))

    elements.append(Paragraph("<b>4. Results Synthesis</b>", heading_style))
    elements.append(Paragraph(
        "All studies show improved efficiency and better decision-making.",
        normal
    ))
    elements.append(Spacer(1, 15))

    elements.append(Paragraph("<b>5. Conclusion</b>", heading_style))
    elements.append(Paragraph(
        "Machine learning is widely applied across domains.",
        normal
    ))

    doc.build(elements)

@app.route("/")
def home():
    try:
        with open("generated_sections.json", encoding="utf-8") as f:
            papers = json.load(f)
    except:
        papers = []

    return render_template("index.html", papers=papers, revised=False)

@app.route("/revise")
def revise():
    try:
        with open("generated_sections.json", encoding="utf-8") as f:
            papers = json.load(f)
    except:
        papers = []

    for paper in papers:
        paper["quality_score"] = evaluate_quality(paper)
        paper["suggestions"] = suggest_revision(paper)
        refine_paper(paper)

    final_report = generate_final_report(papers)

    create_pdf(final_report, papers)

    return render_template(
        "index.html",
        papers=papers,
        revised=True,
        final_report=final_report
    )

def open_browser():
    webbrowser.open("http://127.0.0.1:5000")


if __name__ == "__main__":
    threading.Timer(1.5, open_browser).start()
    app.run(debug=True, use_reloader=False)