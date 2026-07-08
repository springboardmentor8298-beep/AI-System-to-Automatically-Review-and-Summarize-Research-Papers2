from sklearn.feature_extraction.text import TfidfVectorizer #converts text documents into numerical vectors so that machines can analyze them mathematically.
from sklearn.metrics.pairwise import cosine_similarity #converts text documents into numerical vectors so that machines can analyze them mathematically.


def compare_papers(text_list):

    vectorizer = TfidfVectorizer()

    tfidf = vectorizer.fit_transform(text_list)

    similarity = cosine_similarity(tfidf)

    return similarity