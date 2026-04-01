import requests

OLLAMA_URL = "http://localhost:11434/api/generate"


def query_ollama(prompt):
    try:
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": "llama3",
                "prompt": prompt,
                "stream": False
            }
        )
        return response.json()["response"]

    except Exception as e:
        return f"❌ Ollama Error: {e}"


def generate_abstract(papers):
    content = "\n".join([p["Key_Findings"] for p in papers])

    prompt = f"""
    Write a structured academic abstract based on:
    {content}
    """

    return query_ollama(prompt)


def generate_methods(papers):
    content = "\n".join([p["Methodology"] for p in papers if p["Methodology"]])

    prompt = f"""
    Compare and summarize methodologies:
    {content}
    """

    return query_ollama(prompt)


def generate_results(papers):
    content = "\n".join([p["Key_Findings"] for p in papers])

    prompt = f"""
    Summarize key results and insights:
    {content}
    """

    return query_ollama(prompt)