import requests

OLLAMA_URL = "http://localhost:11434/api/generate"


def query_ollama(prompt):
    response = requests.post(
        OLLAMA_URL,
        json={
            "model": "llama3",
            "prompt": prompt,
            "stream": False
        }
    )
    return response.json()["response"]


def evaluate_content(text):
    prompt = f"""
    Evaluate the following research content:

    {text}

    Give:
    1. Clarity score (1-10)
    2. Coherence score (1-10)
    3. Suggestions for improvement
    """

    return query_ollama(prompt)


def revise_content(text):
    prompt = f"""
    Improve and refine the following research content to be more academic,
    clear, and well-structured:

    {text}
    """

    return query_ollama(prompt)