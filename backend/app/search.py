from rank_bm25 import BM25Okapi
import re
from app.embeddings import search_similar


_tokenizer = re.compile(r'\b\w+\b', re.IGNORECASE)


def tokenize(text: str) -> list[str]:
    return _tokenizer.findall(text.lower())


class BM25Index:
    def __init__(self):
        self.corpus: list[dict] = []
        self.tokenized: list[list[str]] = []
        self.bm25: BM25Okapi | None = None

    def add(self, chunks: list[dict]):
        for chunk in chunks:
            self.corpus.append(chunk)
            self.tokenized.append(tokenize(chunk["text"]))
        if self.tokenized:
            self.bm25 = BM25Okapi(self.tokenized)

    def search(self, query: str, top_k: int = 8) -> list[dict]:
        if not self.bm25 or not self.corpus:
            return []
        tokenized_query = tokenize(query)
        scores = self.bm25.get_scores(tokenized_query)
        ranked = sorted(enumerate(scores), key=lambda x: x[1], reverse=True)[:top_k]
        results = []
        for idx, score in ranked:
            if score > 0:
                result = dict(self.corpus[idx])
                result["bm25_score"] = float(score)
                results.append(result)
        return results


_bm25_index: BM25Index | None = None


def get_bm25_index() -> BM25Index:
    global _bm25_index
    if _bm25_index is None:
        _bm25_index = BM25Index()
    return _bm25_index


def hybrid_search(
    query: str,
    top_k: int = 8,
    dense_weight: float = 0.6,
    sparse_weight: float = 0.4,
    where: dict | None = None,
) -> list[dict]:
    dense_results = search_similar(query, top_k=top_k, where=where)

    bm25 = get_bm25_index()
    sparse_results = bm25.search(query, top_k=top_k)

    # Reciprocal Rank Fusion
    rrf_scores: dict[str, float] = {}
    rrf_map: dict[str, dict] = {}
    k = 60

    for rank, result in enumerate(dense_results):
        key = result["text"][:100]
        rrf_scores[key] = rrf_scores.get(key, 0) + dense_weight / (k + rank + 1)
        rrf_map[key] = result

    for rank, result in enumerate(sparse_results):
        key = result["text"][:100]
        rrf_scores[key] = rrf_scores.get(key, 0) + sparse_weight / (k + rank + 1)
        if key not in rrf_map:
            rrf_map[key] = result

    ranked = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)[:top_k]

    final = []
    for key, score in ranked:
        item = dict(rrf_map[key])
        item["rrf_score"] = score
        final.append(item)

    return final
