import os
import json
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
# --- 1. MODEL CONFIGURATION ---
# We initialize the Gemini 1.5 Flash model. limit reach na ho taki 
# Temperature 0.2 is used  (low "randomness"),


llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.2)

def critique_draft(section_name, section_content):
    
    """
    Simulates an Academic Peer Reviewer.
    Instead of rewriting, this function identifies specific flaws or areas for improvement.
    """
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are an expert academic peer reviewer. Analyze the provided section for clarity, tone, and depth."),
        ("human", "Section Name: {section_name}\nContent: {content}\n\nTask: Provide 3 specific, constructive suggestions to improve this section. Be brief.")
    ])
    chain = prompt | llm
    return chain.invoke({"section_name": section_name, "content": section_content}).content

def revise_draft(section_name, section_content, critique, original_context):
    """
    Simulates a Professional Editor.
    This is the 'Refinement Cycle' where the AI takes the critique and the original data
    to produce a superior second draft.
    """
    # CRITICAL STEP: Converting the source data dictionary to a string.
    
    #  if it finds raw JSON braces, it will crash.
    context_str = json.dumps(original_context).replace("{", "{{").replace("}", "}}")
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are an expert academic editor. Revise the provided section by incorporating feedback while maintaining factual accuracy."),
        ("human", "Original Context Data: {context}\n\nSection: {section_name}\nCurrent Draft: {content}\n\nReviewer Critique: {critique}\n\nTask: Rewrite the section to be more polished and professional.")
    ])
    chain = prompt | llm
    return chain.invoke({
        "section_name": section_name, 
        "content": section_content, 
        "critique": critique, 
        "context": context_str
    }).content

def evaluate_quality(report_content):
    """
    Simulates a Senior Journal Editor.
    This provides a final metric (1-10) to help you understand if the generated 
    report meets academic standards.
    """
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a senior journal editor. Evaluate the overall quality of this systematic review."),
        ("human", "Full Report:\n{report}\n\nTask: Provide a Quality Score (1-10) and a one-sentence summary of the review's strength.")
    ])
    chain = prompt | llm
    return chain.invoke({"report": report_content}).content