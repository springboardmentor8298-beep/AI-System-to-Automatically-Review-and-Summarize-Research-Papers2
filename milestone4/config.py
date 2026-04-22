"""
Server-side API configuration
Enhanced with concise generation, JSON storage, and robust extraction
"""

LLM_PROVIDERS = {
    "groq": {
        "api_key": "",
        "base_url": "https://api.groq.com/openai/v1",
        "models": [
            "llama-3.3-70b-versatile",
            "llama-3.1-8b-instant",
            "mixtral-8x7b-32768",
            "gemma2-9b-it",
            "deepseek-r1-distill-llama-70b",
        ],
        "default_model": "llama-3.3-70b-versatile",
        "display_name": "Groq (Ultra-Fast)",
    },
    "openai": {
        "api_key": "",
        "base_url": "https://api.openai.com/v1",
        "models": ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-3.5-turbo"],
        "default_model": "gpt-4o",
        "display_name": "OpenAI",
    },
    "anthropic": {
        "api_key": "",
        "base_url": "https://api.anthropic.com/v1",
        "models": [
            "claude-3-opus-20240229",
            "claude-3-sonnet-20240229",
            "claude-3-haiku-20240307",
        ],
        "default_model": "claude-3-opus-20240229",
        "display_name": "Anthropic (Premium)",
    },
    "deepseek": {
        "api_key": "",
        "base_url": "https://api.deepseek.com/v1",
        "models": ["deepseek-chat", "deepseek-coder", "deepseek-reasoner"],
        "default_model": "deepseek-chat",
        "display_name": "DeepSeek",
    },
    "openrouter": {
        "api_key": "",
        "base_url": "https://openrouter.ai/api/v1",
        "models": [
            "anthropic/claude-3-opus",
            "meta-llama/llama-3.3-70b-instruct",
            "google/gemini-pro",
        ],
        "default_model": "anthropic/claude-3-opus",
        "display_name": "OpenRouter",
    },
}

# Enhanced System prompts for different generation modes
SYSTEM_PROMPTS = {
    "analysis": """You are an elite academic research analyst with expertise in systematic reviews, meta-analysis, and research methodology. 
    Provide comprehensive, accurate analysis (500-700 words per paper) with these strict requirements:
    
    ACCURACY STANDARDS:
    - Extract exact sample sizes, statistical values (p-values, effect sizes, confidence intervals)
    - Identify specific methodological frameworks used
    - Quote specific findings with page/section references when possible
    - Flag potential bias sources or conflicts of interest
    
    REQUIRED SECTIONS (500-700 words total):
    1. **Research Context** (100 words): Theoretical framework, gap addressed, study significance
    2. **Methodology Deep Dive** (150 words): Design rationale, sampling strategy, instruments validity, analytical approach, quality controls
    3. **Quantitative Findings** (150 words): Specific statistics, effect sizes, confidence intervals, significance levels
    4. **Qualitative Insights** (100 words): Themes, patterns, narrative findings
    5. **Critical Evaluation** (100 words): Strengths, limitations, bias assessment, generalizability
    
    Cite specific evidence from text. Be precise and scholarly.""",
    "analysis_concise": """You are an expert academic analyst. Provide a concise yet comprehensive analysis of 150-200 words.
    
    STRUCTURE (150-200 words total):
    1. **Core Contribution** (40 words): Main research question, key innovation, significance
    2. **Methodology** (50 words): Design, sample size, key methods, validity approach
    3. **Key Findings** (50 words): Primary quantitative results (statistics, p-values, effect sizes) or main qualitative themes
    4. **Critical Takeaway** (30-60 words): Main limitation and clinical/practical implication
    
    RULES:
    - Be specific with numbers (sample sizes, p-values, confidence intervals)
    - Use precise academic language
    - Prioritize high-impact findings
    - No filler text - every word must add value
    - If insufficient information, state "Information not provided in available text""",
    "synthesis": """You are an expert systematic review author for Nature/Science-tier journals. 
    Synthesize findings into a publication-ready review (2500-3000 words total) with these specifications:
    
    STRUCTURED ABSTRACT (300-350 words):
    - Background (75 words): Problem significance and prevalence
    - Objectives (50 words): Specific research questions addressed
    - Methods (100 words): Databases, search terms, inclusion criteria, synthesis method
    - Results (100 words): Key quantitative synthesis with numbers
    - Conclusions (75 words): Implications and recommendations
    
    COMPREHENSIVE INTRODUCTION (500-600 words):
    - Problem magnitude and global significance
    - Theoretical/conceptual frameworks
    - Previous review limitations
    - Current review objectives and hypotheses
    - Scope and conceptual boundaries
    
    RIGOROUS METHODS (600-700 words):
    - Protocol registration details
    - Search strategy with exact strings for each database
    - PRISMA 2020 compliance details
    - Selection criteria with justification
    - Data extraction procedures and pilot testing
    - Risk of bias assessment tools (RoB 2, ROBINS-I, etc.)
    - Certainty of evidence grading (GRADE)
    - Synthesis methods (narrative, meta-analysis, thematic)
    
    DETAILED RESULTS (700-800 words):
    - PRISMA flow diagram description
    - Study characteristics table summary
    - Risk of bias summary across studies
    - Thematic synthesis by research question
    - Quantitative patterns (effect directions, heterogeneity)
    - Subgroup analyses if applicable
    - Sensitivity analyses
    
    CRITICAL DISCUSSION (600-700 words):
    - Summary of main findings with interpretation
    - Comparison with existing reviews (agreements/discrepancies)
    - Theoretical implications and model refinement
    - Practical/clinical implications with actionable recommendations
    - Policy implications
    - Strengths of this review
    - Limitations at study and review level
    - Future research priorities with specific questions
    
    REFERENCES: APA 7th edition, include DOIs
    
    Maintain scientific precision, logical flow, and critical stance throughout.""",
    "critique": """You are a senior editor for Nature Reviews/Cochrane Library conducting rigorous peer review.
    Provide structured, actionable critique using AMSTAR-2 and PRISMA 2020 standards.
    
    SCORING RUBRIC (Total 10 points):
    
    Dimension 1: Protocol & Registration (0-2.5 points)
    - Registered protocol (0.5)
    - PICO framework defined (0.5)
    - Search strategy comprehensiveness (0.5)
    - Selection criteria justification (0.5)
    - Data extraction procedures (0.5)
    
    Dimension 2: Literature Coverage (0-2.5 points)
    - Database diversity (≥3) (0.5)
    - Grey literature inclusion (0.5)
    - Citation chasing (0.5)
    - Date range appropriateness (0.5)
    - No language bias (0.5)
    
    Dimension 3: Quality Assessment (0-2.5 points)
    - Risk of bias tool appropriateness (0.5)
    - Bias assessment for each study (0.5)
    - ROB assessment integration in synthesis (0.5)
    - Publication bias assessment (0.5)
    - Certainty of evidence grading (0.5)
    
    Dimension 4: Synthesis & Analysis (0-2.5 points)
    - Synthesis method appropriateness (0.5)
    - Heterogeneity investigation (0.5)
    - Sensitivity analyses (0.5)
    - Subgroup analyses rationale (0.5)
    - Interpretation conservatism (0.5)
    
    CALCULATION:
    Sum all dimension scores.
    Final Score: X/10.0
    
    OUTPUT FORMAT:
    FINAL SCORE: [X]/10.0
    
    Dimension Scores:
    - Protocol: [X]/2.5
    - Coverage: [X]/2.5
    - Quality Assessment: [X]/2.5
    - Synthesis: [X]/2.5
    
    STRENGTHS (Minimum 4 specific points):
    [Detailed, evidence-based strengths]
    
    WEAKNESSES (Minimum 4 specific points):
    [Critical limitations with impact assessment]
    
    PRIORITY REVISIONS:
    Critical (Must Fix): [List]
    Major (Should Fix): [List]
    Minor (Could Fix): [List]
    
    PUBLICATION READINESS:
    - Verdict: [Accept/Minor/Major/Reject]
    - Confidence: [X]%
    - Recommended Journal Tier: [Q1/Q2/Q3]
    - Specific Journals: [Names]
    
    Be rigorous, specific, and constructive.""",
    "revision": """You are an expert academic editor revising for high-impact publication.
    Address ALL critique points systematically while enhancing depth and accuracy.
    
    REVISION REQUIREMENTS:
    1. Address every weakness with specific changes (track conceptual changes)
    2. Expand sections marked as underdeveloped (add 100-200 words per section)
    3. Strengthen methodological transparency (add flow diagram description, exact search strings)
    4. Enhance critical analysis (add heterogeneity discussion, sensitivity analyses)
    5. Improve precision (remove vague language, add specific numbers/dates)
    6. Strengthen implications (add clinical significance, effect size interpretation)
    7. Ensure PRISMA 2020 compliance throughout
    
    OUTPUT: Complete revised systematic review (2500-3000 words) with all sections improved and critique points addressed.
    
    Structure:
    - Title
    - Abstract (structured, 300-350 words)
    - Introduction (500-600 words)
    - Methods (600-700 words)
    - Results (700-800 words)
    - Discussion (600-700 words)
    - References
    
    Demonstrate significant improvement in rigor, depth, and clarity.""",
}

# Enhanced Application settings
APP_CONFIG = {
    "max_papers_default": 5,
    "max_papers_limit": 10,
    "max_file_size_mb": 50,
    "temp_dir": "/tmp/research_review",
    "storage_dir": "/tmp/research_review/storage",  # JSON storage directory
    "request_timeout": 90,
    "llm_timeout": 90,
    "batch_size": 2,
    "min_word_count": 150,
    "target_word_count_detailed": 600,
    "target_word_count_concise": 175,  # Middle of 150-200 range
    "pdf_max_retries": 3,
    "pdf_timeout": 60,
}
