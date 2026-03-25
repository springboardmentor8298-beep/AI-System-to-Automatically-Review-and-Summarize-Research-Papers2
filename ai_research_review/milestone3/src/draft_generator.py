from openai import OpenAI
from dotenv import load_dotenv
import os
import json
import re

# -------------------------------
# LOAD ENV VARIABLES
# -------------------------------
load_dotenv()

API_KEY = os.getenv("GROQ_API_KEY")

if not API_KEY:
    raise ValueError("API key not found. Check your .env file.")

# -------------------------------
# CONFIG
# -------------------------------
BASE_DIR = os.path.dirname(__file__)

INPUT_FILE = os.path.normpath(os.path.join(BASE_DIR, "../data/extracted_text.json"))
OUTPUT_FILE = os.path.normpath(os.path.join(BASE_DIR, "../data/final_draft.json"))

client = OpenAI(
    api_key=API_KEY,
    base_url="https://api.groq.com/openai/v1"
)

MODEL = "llama-3.3-70b-versatile"

# -------------------------------
# LOAD DATA
# -------------------------------
def load_data():
    if not os.path.exists(INPUT_FILE):
        print("extracted_text.json not found.")
        return []

    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


# -------------------------------
# PROMPT BUILDER
# -------------------------------
def build_prompt(papers):
    combined_text = ""

    for paper in papers:
        combined_text += f"\nTITLE: {paper.get('title')}\n"
        combined_text += f"KEY FINDINGS: {paper.get('key_findings')}\n"
        combined_text += f"METHODS: {paper.get('sections', {}).get('methods', '')[:500]}\n"
        combined_text += f"RESULTS: {paper.get('sections', {}).get('results', '')[:500]}\n"
        combined_text += "\n----------------------\n"

    prompt = f"""
You are an academic research assistant.

Based on the following research papers:

{combined_text}

Return ONLY a valid JSON object in this exact format:

{{
  "abstract": "...",
  "methods_comparison": "...",
  "results_synthesis": "..."
}}

Rules:
- Abstract must be max 100 words
- Methods comparison must compare approaches across papers
- Results synthesis must combine key findings
- Do NOT include explanations
- Do NOT include extra text
- ONLY return JSON
"""

    return prompt

# -------------------------------
# GENERATE AI RESPONSE
# -------------------------------
def generate_draft(prompt):
    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": "You are an expert academic writer."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.5
        )

        content = response.choices[0].message.content.strip()

        # 🔍 Extract JSON using regex
        match = re.search(r"\{.*\}", content, re.DOTALL)

        if match:
            json_str = match.group(0)
            return json.loads(json_str)

        print("No valid JSON found. Saving raw output.")
        return {"raw_output": content}

    except Exception as e:
        print(f"API Error: {e}")
        return None


def group_by_topic(papers):
    grouped = {}

    for paper in papers:
        topic = paper.get("topic", "Unknown Topic")

        if topic not in grouped:
            grouped[topic] = []

        grouped[topic].append(paper)

    return grouped

# -------------------------------
# MAIN
# -------------------------------
def main():
    papers = load_data()

    if not papers:
        print("No extracted data available.")
        return

    grouped_papers = group_by_topic(papers)

    final_output = {}

    print("Generating topic-wise research drafts...")

    for topic, topic_papers in grouped_papers.items():
        print(f"\nProcessing topic: {topic}")

        prompt = build_prompt(topic_papers)
        result = generate_draft(prompt)

        if result:
            final_output[topic] = result
        else:
            final_output[topic] = {"error": "Generation failed"}

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(final_output, f, indent=4)

    print("Milestone 3 completed successfully!")


if __name__ == "__main__":
    main()
