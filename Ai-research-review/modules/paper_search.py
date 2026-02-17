import requests

SEMANTIC_SCHOLAR_API = "https://api.semanticscholar.org/graph/v1/paper/search"


def search_papers(query, limit=10):
    params = {
        "query": query,
        "limit": limit,
        "fields": "title,authors,year,openAccessPdf,isOpenAccess"
    }

    response = requests.get(SEMANTIC_SCHOLAR_API, params=params)

    if response.status_code != 200:
        print("API Error:", response.status_code)
        return []

    papers = response.json().get("data", [])

    # Filter only open-access papers with valid PDF link
    open_access_papers = [
        paper for paper in papers
        if paper.get("isOpenAccess")
        and paper.get("openAccessPdf")
        and paper["openAccessPdf"].get("url")
    ]

    return open_access_papers[:3]
