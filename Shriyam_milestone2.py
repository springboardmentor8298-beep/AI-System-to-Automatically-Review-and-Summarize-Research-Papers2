import os
import json
import pymupdf4llm  # Converts PDF directly to Markdown
import milestone1   # Imports your existing paper retrieval module

# --- LANGCHAIN & AI IMPORTS ---
# We use LangChain to orchestrate the AI prompts and Pydantic to force 
# the AI to return perfectly structured, predictable data.
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

# --- CONFIGURATION CONSTANTS ---
PROCESSED_DIR = "processed_data"

# Ensure the  Google API Key is set in the environment
if not os.getenv("GOOGLE_API_KEY"):
    raise ValueError("CRITICAL ERROR: GOOGLE_API_KEY environment variable is missing. Please export it in your terminal before running.")

# --- PYDANTIC SCHEMAS (DATA VALIDATION) ---
# This defines the exact JSON structure the AI MUST follow in its output.
# It fulfills the requirement to "Validate correctness and completeness of extracted textual data".
class PaperAnalysis(BaseModel):
    abstract: str = Field(description="The summarized abstract of the paper.")
    methods: str = Field(description="The methodology used in the research.")
    results: str = Field(description="The primary results or outcomes.")
    key_findings: list[str] = Field(description="3-5 bullet points of the most critical findings.")
    validation_score: int = Field(description="Rate the completeness and readability of the provided text from 1-10.")

class CrossPaperComparison(BaseModel):
    common_themes: list[str] = Field(description="Themes or methodologies common across all provided papers.")
    methodology_differences: str = Field(description="How the papers differ in their approach.")
    overall_consensus: str = Field(description="The general consensus or combined conclusion of the papers.")

# --- INITIALIZE AI MODEL ---
# Using Google's Gemini Flash model via LangChain
llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0)

def setup_processed_directory(topic):
    """
    FILE SYSTEM MANAGEMENT: Creates the processed_data folder and a subfolder for the specific topic.
    """
    safe_topic = milestone1.sanitize_filename(topic)
    
    if not os.path.exists(PROCESSED_DIR):
        os.makedirs(PROCESSED_DIR)
        
    full_path = os.path.join(PROCESSED_DIR, safe_topic)
    
    if not os.path.exists(full_path):
        os.makedirs(full_path)
        print(f"[INFO] Created directory for processed data: {full_path}")
    else:
        print(f"[INFO] Using existing processed directory: {full_path}")
        
    return full_path

def extract_and_analyze_text(pdf_path):
    """
    ANALYSIS MODULE: Extracts text from the PDF and uses AI to break it into sections.
    """
    try:
        # 1. Raw Extraction: Convert PDF to Markdown
        print(f"   -> Converting {os.path.basename(pdf_path)} to Markdown...")
        md_text = pymupdf4llm.to_markdown(pdf_path)
        
        # Basic validation: Check if the PDF is empty or just a scanned image
        if len(md_text.strip()) < 500:
             return {"status": "error", "error_message": "Extracted text is too short. PDF might be a scanned image or corrupted."}

        # Safety Limit: Truncate massively long papers so we don't overwhelm the AI
        truncated_md = md_text[:30000] 

        # 2. Section-Wise AI Parsing
        print(f"    Running AI Section Parsing & Key Finding Extraction...")
        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are an expert academic research assistant. Extract the required sections and key findings from the provided academic paper markdown."),
            ("human", "Analyze the following paper markdown:\n\n{paper_text}")
        ])
        
        # Bind our Pydantic schema to the AI so it outputs perfect JSON
        structured_llm = llm.with_structured_output(PaperAnalysis)
        chain = prompt | structured_llm
        
        # Execute the AI extraction
        result = chain.invoke({"paper_text": truncated_md})
        
        return {
            "status": "success",
            "sectioned_data": result.dict()
        }
        
    except Exception as e:
        print(f"[ERROR] Failed to extract text from {pdf_path}: {e}")
        return {"status": "error", "error_message": str(e)}

def generate_cross_paper_comparison(all_papers_data):
    """
    COMPARISON MODULE: Takes findings from ALL papers and compares them to find consensus and differences.
    """
    print("\n[ANALYSIS] Generating cross-paper comparison...")
    
    # Gather all the 'key findings' from the successful extractions
    aggregated_summaries = ""
    for idx, paper in enumerate(all_papers_data):
        if paper["analysis_results"]["status"] == "success":
            findings = paper["analysis_results"]["sectioned_data"]["key_findings"]
            aggregated_summaries += f"Paper {idx+1} ({paper['file_name']}) Findings:\n{findings}\n\n"
            
    if not aggregated_summaries:
        return {"error": "Not enough successful extractions to compare."}

    # Prompt the AI to compare the findings
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are an expert academic reviewer. Compare the findings from the following papers and synthesize the overlaps, differences, and overall consensus."),
        ("human", "Here are the key findings from multiple papers:\n\n{summaries}")
    ])
    
    structured_llm = llm.with_structured_output(CrossPaperComparison)
    chain = prompt | structured_llm
    
    # Execute the comparison
    comparison_result = chain.invoke({"summaries": aggregated_summaries})
    return comparison_result.dict()

def run_milestone_2_pipeline(topic, count):
    """
    ORCHESTRATOR: Manages the flow from downloading (Milestone 1) to extraction and comparison (Milestone 2).
    """
    print("\n" + "="*50)
    print("PHASE 1: PAPER RETRIEVAL (Milestone 1)")
    print("="*50)
    
    # Call the code from milestone1.py
    downloaded_count = milestone1.process_paper_downloads(topic, count)
    
    if downloaded_count == 0:
        print("\n[STOP] No papers were downloaded. Cannot proceed to extraction.")
        return

    print("\n" + "="*50)
    print(" PHASE 2: TEXT EXTRACTION & SECTIONING (Milestone 2)")
    print("="*50)
    
    # Setup directories
    safe_topic = milestone1.sanitize_filename(topic)
    download_folder = os.path.join(milestone1.DOWNLOAD_DIR, safe_topic)
    processed_folder = setup_processed_directory(topic)
    
    all_papers_data = []

    # Loop through the PDFs that Milestone 1 just downloaded
    for filename in os.listdir(download_folder):
        if filename.endswith(".pdf"):
            print(f"\n[PROCESSING] {filename}")
            pdf_path = os.path.join(download_folder, filename)
            
            # Extract and parse
            paper_analysis = extract_and_analyze_text(pdf_path)
            
            record = {
                "file_name": filename,
                "analysis_results": paper_analysis
            }
            all_papers_data.append(record)

    # Cross-Paper Comparison
    print("\n" + "="*50)
    print("PHASE 3: CROSS-PAPER COMPARISON")
    print("="*50)
    
    comparison_data = generate_cross_paper_comparison(all_papers_data)
    
    # Compile the final comprehensive JSON dataset
    final_output = {
        "topic": topic,
        "papers_analyzed": len(all_papers_data),
        "cross_paper_analysis": comparison_data,
        "individual_papers": all_papers_data
    }

    # Save to JSON file
    json_filename = "processed_data.json"
    json_path = os.path.join(processed_folder, json_filename)
    
    with open(json_path, 'w', encoding='utf-8') as json_file:
        json.dump(final_output, json_file, indent=4)
        
    print(f"\n[SUCCESS] Milestone 2 Complete! Extracted and compared data saved to: {json_path}")

# --- ENTRY POINT ---
if __name__ == "__main__":
    print("--- SYSTEM AUTOMATIC REVIEW PIPELINE ---")
    # Borrow the input function from milestone1 to keep the user experience consistent
    topic, count = milestone1.get_user_input()
    
    if topic and count:
        run_milestone_2_pipeline(topic, count)
