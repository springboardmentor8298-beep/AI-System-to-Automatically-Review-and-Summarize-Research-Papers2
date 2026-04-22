import os
import re
import io
import json
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from flask import jsonify, request, send_file

# ReportLab imports for PDF generation
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    PageBreak,
    Table,
    TableStyle,
)
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib import colors


class ReviewGenerator:
    """High-performance review generator with batch analysis - MILESTONES 3-4"""

    def __init__(self, provider, model, mode="detailed"):
        self.provider = provider
        self.model = model
        self.mode = mode  # "detailed" or "concise"
        self.extracted_sections = []

    def extract_and_structure(self, paper_ids, downloaded_papers_cache):
        """Parallel extraction with robust handling"""
        self.extracted_sections = []

        def extract_single(paper_id):
            try:
                paper_info = downloaded_papers_cache.get(paper_id, {})
                filepath = paper_info.get("filepath")
                metadata = paper_info.get("metadata", {})

                if not filepath or not os.path.exists(filepath):
                    return None

                # Import here to avoid circular dependency
                from app import RobustPaperProcessor

                sections = RobustPaperProcessor.extract_text(filepath)

                return {
                    "id": paper_id,
                    "title": metadata.get("title", f"Paper {paper_id}"),
                    "authors": metadata.get("authors", []),
                    "year": metadata.get("year", "Unknown"),
                    "source": metadata.get("source", "Unknown"),
                    "doi": metadata.get("doi", ""),
                    "citations": metadata.get("citations", 0),
                    "journal": metadata.get("journal", ""),
                    "sections": sections,
                }
            except Exception as e:
                print(f"Error extracting {paper_id}: {e}")
                return None

        # Parallel extraction
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = {executor.submit(extract_single, pid): pid for pid in paper_ids}
            for future in as_completed(futures):
                result = future.result()
                if result:
                    self.extracted_sections.append(result)

        return self.extracted_sections

    def analyze_papers_batch(self, LLMManager, SYSTEM_PROMPTS):
        """Batch analysis with parallel processing and mode selection"""
        if not self.extracted_sections:
            raise Exception("No papers extracted")

        analysis_results = []

        # Determine prompt and token limit based on mode
        if self.mode == "concise":
            system_prompt = SYSTEM_PROMPTS["analysis_concise"]
            max_tokens = 800
            target_words = "150-200"
        else:
            system_prompt = SYSTEM_PROMPTS["analysis"]
            max_tokens = 3000
            target_words = "500-700"

        def analyze_single(paper):
            analysis_prompt = f"""Provide {target_words} word academic analysis:

TITLE: {paper["title"]}
AUTHORS: {", ".join(paper["authors"])}
YEAR: {paper["year"]}
JOURNAL: {paper.get("journal", "N/A")}
CITATIONS: {paper.get("citations", "N/A")}

ABSTRACT: {paper["sections"]["abstract"][:1000] if paper["sections"]["abstract"] else "N/A"}

INTRODUCTION: {paper["sections"]["introduction"][:1500] if paper["sections"]["introduction"] else "N/A"}

METHODS: {paper["sections"]["methods"][:1500] if paper["sections"]["methods"] else "N/A"}

RESULTS: {paper["sections"]["results"][:1500] if paper["sections"]["results"] else "N/A"}

CONCLUSION: {paper["sections"]["conclusion"][:1500] if paper["sections"]["conclusion"] else "N/A"}

Provide {target_words} word analysis following the system instructions."""

            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": analysis_prompt},
            ]

            try:
                analysis = LLMManager.generate_completion(
                    self.provider, self.model, messages, max_tokens=max_tokens
                )
                return {
                    "paper_id": paper["id"],
                    "title": paper["title"],
                    "analysis": analysis,
                    "mode": self.mode,
                    "word_count": len(analysis.split()),
                }
            except Exception as e:
                return {
                    "paper_id": paper["id"],
                    "title": paper["title"],
                    "analysis": f"Analysis failed: {str(e)}",
                    "mode": self.mode,
                    "word_count": 0,
                }

        # Process papers with progress tracking
        total = len(self.extracted_sections)
        completed = 0

        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = {
                executor.submit(analyze_single, paper): paper
                for paper in self.extracted_sections
            }
            for future in as_completed(futures):
                result = future.result()
                if result:
                    analysis_results.append(result)
                completed += 1
                print(f"Analysis progress: {completed}/{total}")

        return analysis_results

    def generate_writing_phase(self, analyses, SYSTEM_PROMPTS, LLMManager):
        """MILESTONE 3: Generate comprehensive review with separate sections"""
        papers_content = ""
        for i, analysis in enumerate(analyses, 1):
            papers_content += (
                f"\n\nPAPER {i}: {analysis['title']}\n{analysis['analysis']}\n"
            )

        sections = {}

        # 1. ABSTRACT (300-350 words)
        abstract_prompt = f"""Create a structured abstract (300-350 words) based on these papers:

{papers_content}

Write ONLY the abstract content. Structure:
- Background (75 words): Problem, prevalence, significance
- Objectives (50 words): Research questions, aims  
- Methods (100 words): Databases, search strategy, inclusion criteria, synthesis approach
- Results (100 words): Key findings with specific numbers/statistics
- Conclusions (75 words): Implications, recommendations

Requirements:
- Use specific numbers and statistics
- Follow PRISMA 2020 systematic review format
- Do NOT include headings like "Abstract" or section labels
- Write as flowing narrative text
- Target: 300-350 words"""

        abstract_messages = [
            {"role": "system", "content": SYSTEM_PROMPTS["synthesis"]},
            {"role": "user", "content": abstract_prompt},
        ]

        try:
            sections["abstract"] = LLMManager.generate_completion(
                self.provider, self.model, abstract_messages, max_tokens=800
            ).strip()
        except Exception as e:
            sections["abstract"] = f"Error generating abstract: {str(e)}"

        # 2. METHODOLOGY (600-700 words)
        methods_prompt = f"""Create a comprehensive Methodology section (600-700 words) based on these papers:

{papers_content}

Write ONLY the methodology content. Include:
- Protocol registration and PICO framework specification
- Exact search strategy with database names, search strings, date limits
- PRISMA 2020 compliance details and flow diagram description
- Inclusion and exclusion criteria with clear justification
- Data extraction procedures and pilot testing
- Risk of bias assessment tools and procedures
- GRADE certainty of evidence assessment
- Synthesis approach (narrative synthesis or meta-analysis)

Requirements:
- Be methodological and precise
- Include specific database names (e.g., PubMed, Scopus, Web of Science)
- Specify exact search terms and Boolean operators used
- Do NOT include headings like "Methodology" or section labels
- Write as flowing narrative text
- Target: 600-700 words"""

        methods_messages = [
            {"role": "system", "content": SYSTEM_PROMPTS["synthesis"]},
            {"role": "user", "content": methods_prompt},
        ]

        try:
            sections["methods"] = LLMManager.generate_completion(
                self.provider, self.model, methods_messages, max_tokens=1200
            ).strip()
        except Exception as e:
            sections["methods"] = f"Error generating methodology: {str(e)}"

        # 3. RESULTS (700-800 words)
        results_prompt = f"""Create a detailed Results section (700-800 words) based on these papers:

{papers_content}

Write ONLY the results content. Structure:
- Study selection: PRISMA flow description with specific numbers at each stage
- Study characteristics: Research designs, sample sizes, settings, countries
- Risk of bias: Summary across all studies, graphical description
- Thematic synthesis organized by research question (3-4 major themes)
- Quantitative patterns: Effect directions, consistency across studies, heterogeneity
- Subgroup analyses: Comparisons by methodology, population, intervention setting
- Sensitivity analyses: Impact of exclusions, robustness of findings

Requirements:
- Use specific numbers and percentages
- Include actual data from the papers analyzed
- Do NOT include headings like "Results" or section labels
- Write as flowing narrative text
- Target: 700-800 words"""

        results_messages = [
            {"role": "system", "content": SYSTEM_PROMPTS["synthesis"]},
            {"role": "user", "content": results_prompt},
        ]

        try:
            sections["results"] = LLMManager.generate_completion(
                self.provider, self.model, results_messages, max_tokens=1400
            ).strip()
        except Exception as e:
            sections["results"] = f"Error generating results: {str(e)}"

        # 4. DISCUSSION (600-700 words)
        discussion_prompt = f"""Create a critical Discussion section (600-700 words) based on these papers:

{papers_content}

Write ONLY the discussion content. Cover:
- Main findings summary with interpretation and clinical significance
- Comparison with existing reviews: Agreements, discrepancies, novel contributions
- Theoretical implications: Framework refinement, model development, knowledge gaps
- Practical implications: Clinical recommendations, policy implications, real-world applications
- Strengths of this review: Methodological rigor, comprehensive coverage, novelty
- Limitations: Study-level limitations (risk of bias) and review-level constraints (coverage, language, publication bias)
- Future research priorities: Specific methodological improvements, research questions, study designs needed

Requirements:
- Be critical and forward-looking
- Balance optimism with caution
- Do NOT include headings like "Discussion" or section labels
- Write as flowing narrative text
- Target: 600-700 words"""

        discussion_messages = [
            {"role": "system", "content": SYSTEM_PROMPTS["synthesis"]},
            {"role": "user", "content": discussion_prompt},
        ]

        try:
            sections["discussion"] = LLMManager.generate_completion(
                self.provider, self.model, discussion_messages, max_tokens=1200
            ).strip()
        except Exception as e:
            sections["discussion"] = f"Error generating discussion: {str(e)}"

        # Generate references
        references = []
        for paper in self.extracted_sections:
            authors = paper.get("authors", ["Unknown"])
            year = paper.get("year", "n.d.")
            title = paper.get("title", "Untitled")
            source = paper.get("source", "")
            doi = paper.get("doi", "")
            journal = paper.get("journal", "")

            if len(authors) > 1:
                author_str = ", ".join(authors[:-1]) + ", & " + authors[-1]
            else:
                author_str = authors[0] if authors else "Unknown"

            ref = f"{author_str} ({year}). {title}."
            if journal:
                ref += f" {journal}."
            elif source == "arXiv":
                ref += " arXiv preprint."
            elif source == "Semantic Scholar":
                ref += " Retrieved from Semantic Scholar."
            if doi:
                ref += f" https://doi.org/{doi}"

            references.append(ref)

        sections["references"] = references

        # Create full review by combining sections
        sections["full_review"] = self._compile_full_review(
            sections, len(self.extracted_sections)
        )

        return {
            "abstract": sections["abstract"],
            "methods_comparison": sections["methods"],
            "results_synthesis": sections["results"],
            "discussion": sections["discussion"],
            "references": sections["references"],
            "full_review": sections["full_review"],
        }

    def _compile_full_review(self, sections, paper_count):
        """Compile final review with proper academic formatting"""
        review = f"""SYSTEMATIC LITERATURE REVIEW

ABSTRACT

{sections["abstract"]}

1. INTRODUCTION

This systematic review synthesizes evidence from {paper_count} studies to address the research question. The review follows PRISMA 2020 guidelines and employs rigorous methodological standards to ensure reliable and valid conclusions. The growing importance of this research area necessitates comprehensive synthesis to guide future research and practice.

2. METHODOLOGY

{sections["methods"]}

3. RESULTS

{sections["results"]}

4. DISCUSSION

{sections["discussion"]}

5. CONCLUSION

This systematic review provides comprehensive evidence synthesis, identifying key patterns, methodological considerations, and directions for future research. The findings contribute to theoretical understanding and offer practical guidance for stakeholders in the field.

REFERENCES

"""
        for i, ref in enumerate(sections["references"], 1):
            review += f"{i}. {ref}\n"

        return review

    def generate_critique(self, full_review, SYSTEM_PROMPTS, LLMManager):
        """MILESTONE 4: Generate accurate critique with structured scoring"""
        critique_prompt = f"""Conduct rigorous peer review using AMSTAR-2 and PRISMA 2020:

{full_review[:5000]}

STRICT SCORING (0-10 scale):

Dimension 1 - Protocol (0-2.5): Registered? PICO defined? Search comprehensive? Criteria justified? Extraction piloted?
Dimension 2 - Coverage (0-2.5): ≥3 databases? Grey literature? Citation chasing? Appropriate dates? Language inclusive?
Dimension 3 - Quality Assessment (0-2.5): Appropriate ROB tool? Study-level assessment? Integration in synthesis? Publication bias assessed? GRADE used?
Dimension 4 - Synthesis (0-2.5): Appropriate method? Heterogeneity examined? Sensitivity analyses? Subgroup rationales? Conservative interpretation?

CALCULATE FINAL SCORE: Sum of dimensions (0-10.0)

OUTPUT FORMAT:
FINAL SCORE: [X]/10.0

Dimension Breakdown:
- Protocol & Registration: [X]/2.5
- Literature Coverage: [X]/2.5
- Quality Assessment: [X]/2.5
- Synthesis & Analysis: [X]/2.5

STRENGTHS (4+ specific points):
1. [Evidence-based strength]
...

WEAKNESSES (4+ specific points):
1. [Critical limitation with impact]
...

PRIORITY REVISIONS:
Critical (Must Fix): [Specific list]
Major (Should Fix): [Specific list]
Minor (Could Fix): [Specific list]

PUBLICATION READINESS:
- Verdict: [Accept/Minor/Major/Reject]
- Confidence: [X]%
- Recommended Tier: [Q1/Q2/Q3]
- Specific Journals: [Names]"""

        messages = [
            {"role": "system", "content": SYSTEM_PROMPTS["critique"]},
            {"role": "user", "content": critique_prompt},
        ]

        return LLMManager.generate_completion(
            self.provider, self.model, messages, max_tokens=3000
        )

    def generate_revision(self, full_review, critique, SYSTEM_PROMPTS, LLMManager):
        """MILESTONE 4: Generate improved revision"""
        revision_prompt = f"""Revise systematically addressing ALL critique points:

ORIGINAL REVIEW:
{full_review[:4000]}

CRITIQUE TO ADDRESS:
{critique[:2000]}

REVISION INSTRUCTIONS:
1. Fix every weakness identified in critique
2. Expand underdeveloped sections (add 150+ words each)
3. Strengthen methodology transparency
4. Enhance critical analysis depth
5. Improve precision and reduce vague language
6. Add sensitivity analyses, heterogeneity discussion
7. Strengthen implications with clinical significance

OUTPUT: Complete revised review (2800-3200 words) with all sections improved."""

        messages = [
            {"role": "system", "content": SYSTEM_PROMPTS["revision"]},
            {"role": "user", "content": revision_prompt},
        ]

        return LLMManager.generate_completion(
            self.provider, self.model, messages, max_tokens=4000
        )


class PDFGenerator:
    """MILESTONE 4: Enhanced PDF generator with professional academic formatting"""

    @staticmethod
    def generate_pdf(content, title="Systematic Literature Review", metadata=None):
        """Generate publication-quality PDF"""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=36,
        )

        styles = getSampleStyleSheet()

        # Custom styles
        title_style = ParagraphStyle(
            "Title",
            parent=styles["Heading1"],
            fontSize=24,
            textColor=colors.HexColor("#1e3a8a"),
            spaceAfter=30,
            alignment=TA_CENTER,
            fontName="Helvetica-Bold",
        )

        heading1_style = ParagraphStyle(
            "Heading1",
            parent=styles["Heading1"],
            fontSize=16,
            textColor=colors.HexColor("#1e40af"),
            spaceAfter=12,
            spaceBefore=12,
            fontName="Helvetica-Bold",
        )

        heading2_style = ParagraphStyle(
            "Heading2",
            parent=styles["Heading2"],
            fontSize=13,
            textColor=colors.HexColor("#3b82f6"),
            spaceAfter=10,
            spaceBefore=10,
            fontName="Helvetica-Bold",
        )

        body_style = ParagraphStyle(
            "Body",
            parent=styles["BodyText"],
            fontSize=11,
            leading=16,
            alignment=TA_JUSTIFY,
            spaceAfter=10,
            fontName="Times-Roman",
        )

        abstract_style = ParagraphStyle(
            "Abstract",
            parent=styles["BodyText"],
            fontSize=10,
            leading=14,
            alignment=TA_JUSTIFY,
            leftIndent=20,
            rightIndent=20,
            spaceAfter=12,
            fontName="Times-Roman",
        )

        elements = []

        # Title
        elements.append(Paragraph(title, title_style))
        elements.append(Spacer(1, 20))

        # Metadata if provided
        if metadata:
            meta_text = f"<i>Generated: {metadata.get('date', '')} | Papers analyzed: {metadata.get('paper_count', '')} | AI Provider: {metadata.get('provider', '')}</i>"
            elements.append(
                Paragraph(
                    meta_text,
                    ParagraphStyle(
                        "Meta",
                        parent=styles["Normal"],
                        fontSize=9,
                        textColor=colors.gray,
                        alignment=TA_CENTER,
                    ),
                )
            )
            elements.append(Spacer(1, 20))

        # Process content
        lines = content.split("\n")
        in_abstract = False
        current_paragraph = []

        def flush_paragraph():
            if current_paragraph:
                text = " ".join(current_paragraph)
                if in_abstract:
                    elements.append(Paragraph(text, abstract_style))
                else:
                    elements.append(Paragraph(text, body_style))
                current_paragraph.clear()

        for line in lines:
            line = line.strip()

            if not line:
                flush_paragraph()
                continue

            # Headers detection
            if line.isupper() and len(line) < 150 and not line.startswith("---"):
                flush_paragraph()
                if "ABSTRACT" in line:
                    in_abstract = True
                    elements.append(Paragraph(line, heading1_style))
                elif any(
                    x in line
                    for x in [
                        "INTRODUCTION",
                        "METHODS",
                        "RESULTS",
                        "DISCUSSION",
                        "CONCLUSION",
                        "REFERENCES",
                    ]
                ):
                    in_abstract = False
                    elements.append(PageBreak() if elements else Spacer(1, 12))
                    elements.append(Paragraph(line, heading1_style))
                else:
                    elements.append(Paragraph(line, heading2_style))

            elif line.startswith("**") and line.endswith("**"):
                flush_paragraph()
                clean = line.strip("*")
                elements.append(Paragraph(f"<b>{clean}</b>", body_style))

            elif re.match(r"^\d+\.", line):
                flush_paragraph()
                elements.append(Paragraph(line, body_style))
            elif line.startswith("•") or line.startswith("-"):
                flush_paragraph()
                elements.append(Paragraph(f"• {line[1:].strip()}", body_style))
            else:
                current_paragraph.append(line)

        flush_paragraph()

        doc.build(elements)
        buffer.seek(0)
        return buffer


def register_milestone_routes(
    app,
    analysis_cache,
    storage,
    LLMManager,
    ReviewGenerator,
    PDFGenerator,
    SYSTEM_PROMPTS,
    APP_CONFIG,
    TEMP_DIR,
):
    """Register all Milestone 3-4 routes to the Flask app"""

    @app.route("/api/generate", methods=["POST"])
    def generate_review():
        """Milestone 3: Writing Phase - Generate full review"""
        data = request.json
        provider = data.get("provider", "groq")
        model = data.get("model")

        cache_key = request.remote_addr
        if cache_key not in analysis_cache:
            return jsonify({"error": "No analysis found"}), 400

        cached = analysis_cache[cache_key]

        # Recreate generator with stored parameters
        generator = ReviewGenerator(
            provider or cached.get("provider", "groq"),
            model or cached.get("model"),
            mode=cached.get("mode", "detailed"),
        )
        generator.extracted_sections = cached["extracted"]
        analyses = cached["analyses"]

        try:
            writing_results = generator.generate_writing_phase(
                analyses, SYSTEM_PROMPTS, LLMManager
            )

            # Update cache with results
            analysis_cache[cache_key]["full_review"] = writing_results["full_review"]
            analysis_cache[cache_key]["writing_results"] = writing_results

            # Update storage
            session_id = f"review_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            storage.save_session(
                session_id,
                {
                    **cached,
                    "writing_results": writing_results,
                    "full_review": writing_results["full_review"],
                },
            )

            return jsonify(
                {
                    "phase": "writing",
                    "session_id": session_id,
                    "abstract": writing_results["abstract"],
                    "methods_comparison": writing_results["methods_comparison"],
                    "results_synthesis": writing_results["results_synthesis"],
                    "discussion": writing_results["discussion"],
                    "references": writing_results["references"],
                    "full_review": writing_results["full_review"],
                }
            )

        except Exception as e:
            import traceback

            print(f"Error in generate_review: {e}")
            traceback.print_exc()
            return jsonify({"error": str(e)}), 500

    @app.route("/api/review", methods=["POST"])
    def review_assessment():
        """Milestone 4: Review Phase - Critique and Revision"""
        data = request.json
        provider = data.get("provider", "groq")
        model = data.get("model")
        action = data.get("action", "critique")

        cache_key = request.remote_addr
        if (
            cache_key not in analysis_cache
            or "full_review" not in analysis_cache[cache_key]
        ):
            return jsonify({"error": "No review found"}), 400

        cached = analysis_cache[cache_key]

        # Recreate generator with stored parameters
        generator = ReviewGenerator(
            provider or cached.get("provider", "groq"),
            model or cached.get("model"),
            mode=cached.get("mode", "detailed"),
        )
        full_review = cached["full_review"]

        try:
            if action == "critique":
                critique = generator.generate_critique(
                    full_review, SYSTEM_PROMPTS, LLMManager
                )
                return jsonify(
                    {"phase": "review", "action": "critique", "critique": critique}
                )

            elif action == "revise":
                critique = data.get("critique", "")
                if not critique:
                    critique = generator.generate_critique(
                        full_review, SYSTEM_PROMPTS, LLMManager
                    )

                revised = generator.generate_revision(
                    full_review, critique, SYSTEM_PROMPTS, LLMManager
                )

                # Save final revision
                session_id = f"final_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                storage.save_session(
                    session_id,
                    {**cached, "critique": critique, "revised_review": revised},
                )

                return jsonify(
                    {
                        "phase": "review",
                        "action": "revision",
                        "session_id": session_id,
                        "critique": critique,
                        "revised_review": revised,
                    }
                )
            else:
                return jsonify({"error": "Invalid action"}), 400

        except Exception as e:
            import traceback

            print(f"Error in review_assessment: {e}")
            traceback.print_exc()
            return jsonify({"error": str(e)}), 500

    @app.route("/api/export", methods=["POST"])
    def export_review():
        """Milestone 4: Export Phase - PDF and JSON export"""
        data = request.json
        content = data.get("content", "")
        filename = data.get("filename", "systematic_review.pdf")
        export_format = data.get("format", "pdf")
        metadata = data.get("metadata", {})

        if not content:
            return jsonify({"error": "No content"}), 400

        try:
            if export_format == "pdf":
                pdf_buffer = PDFGenerator.generate_pdf(content, metadata=metadata)
                return send_file(
                    pdf_buffer,
                    as_attachment=True,
                    download_name=filename.replace(".txt", ".pdf"),
                    mimetype="application/pdf",
                )
            elif export_format == "json":
                # Export as structured JSON
                json_data = {
                    "metadata": metadata,
                    "content": content,
                    "exported_at": datetime.now().isoformat(),
                    "format": "json",
                }
                buffer = io.BytesIO()
                buffer.write(
                    json.dumps(json_data, indent=2, ensure_ascii=False).encode("utf-8")
                )
                buffer.seek(0)
                return send_file(
                    buffer,
                    as_attachment=True,
                    download_name=filename.replace(".pdf", ".json").replace(
                        ".txt", ".json"
                    ),
                    mimetype="application/json",
                )
            else:
                safe_filename = filename.replace("/", "_").replace("\\", "_")
                filepath = os.path.join(TEMP_DIR, safe_filename)
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(content)
                return send_file(
                    filepath,
                    as_attachment=True,
                    download_name=safe_filename,
                    mimetype="text/plain",
                )

        except Exception as e:
            import traceback

            print(f"Error in export: {e}")
            traceback.print_exc()
            return jsonify({"error": f"Export failed: {str(e)}"}), 500
