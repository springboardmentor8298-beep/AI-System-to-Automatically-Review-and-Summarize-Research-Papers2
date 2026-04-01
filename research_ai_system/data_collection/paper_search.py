import requests

API_URL = "https://api.semanticscholar.org/graph/v1/paper/search"

HEADERS = {
    "User-Agent": "research-ai-system/1.0",
    "x-api-key": "YOUR_API_KEY_HERE"
}

import arxiv

def search_papers(query, max_results=5):
    search = arxiv.Search(
        query=query,
        max_results=max_results,
        sort_by=arxiv.SortCriterion.Relevance
    )

    papers = []

    for result in search.results():
        papers.append({
            "title": result.title,
            "authors": [a.name for a in result.authors],
            "year": result.published.year,
            "pdf_url": result.pdf_url,
            "summary": result.summary
        })

    return papers