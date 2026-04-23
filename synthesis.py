import json
from transformers import pipeline

print("Loading generated sections...")

with open("generated_sections.json", "r", encoding="utf-8") as f:
    papers = json.load(f)

print("Loading AI model...")

generator = pipeline(
    "text-generation",
    model="gpt2"
)

combined_results = ""

for paper in papers:
    combined_results += paper.get("results", "") + " "

print("Generating synthesis from multiple papers...")

summary = generator(
    "Combine and summarize these research findings: " + combined_results,
    max_length=200,
    num_return_sequences=1
)

synthesis = summary[0]["generated_text"]

with open("synthesis.txt", "w", encoding="utf-8") as f:
    f.write(synthesis)

print("Synthesis created successfully!")