# modules/paper_search.py
import arxiv

def search_papers(topic, max_results=5):
    """
    Search arXiv for papers by topic. Returns list of arxiv.Result objects.
    """
    search = arxiv.Search(
        query=topic,
        max_results=max_results,
        sort_by=arxiv.SortCriterion.Relevance
    )
    return list(search.results())