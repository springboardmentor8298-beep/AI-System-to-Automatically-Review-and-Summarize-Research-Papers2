from transformers import pipeline
import json

generator = pipeline("text-generation", model="gpt2")

def load_analysis():

    with open("analysis_output.json","r",encoding="utf-8") as f:
        return json.load(f)


def collect_findings(data):

    findings = []

    for paper in data["papers_analysis"]:
        findings.extend(paper["key_findings"])

    return " ".join(findings[:20])


def generate_sections():

    data = load_analysis()

    findings = collect_findings(data)

    abstract_prompt = f"Write a research abstract based on these findings: {findings}"
    methods_prompt = "Write a methodology section for a literature review research paper."
    results_prompt = f"Write a results section based on the following findings: {findings}"

    abstract = generator(abstract_prompt, max_length=200)[0]["generated_text"]
    methods = generator(methods_prompt, max_length=200)[0]["generated_text"]
    results = generator(results_prompt, max_length=200)[0]["generated_text"]

    return {
        "abstract": abstract,
        "methods": methods,
        "results": results
    }