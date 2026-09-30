import re

from rank_bm25 import BM25Okapi

from app.embeddings import get_or_create_collection, search_similar

_tokenizer = re.compile(r"\b\w+\b", re.IGNORECASE)

# BM25Okapi floors negative IDFs to `epsilon * average_idf`, which is itself
# negative on small corpora (a term present in most documents). The resulting
# negative scores then get dropped by any `score > 0` relevance gate, so a
# single-chunk corpus returns nothing at all. Floor IDF at a small positive
# value instead: a term that appears in every document is uninformative, but
# it is not a reason to discard the only match.
_MIN_IDF = 1e-6


class _BM25(BM25Okapi):
    def __init__(self, corpus, **kwargs):
        super().__init__(corpus, **kwargs)
        for word, idf in self.idf.items():
            if idf < _MIN_IDF:
                self.idf[word] = _MIN_IDF


def tokenize(text: str) -> list[str]:
    return _tokenizer.findall(text.lower())


def _matches_where(metadata: dict, where: dict | None) -> bool:
    """Chroma-style equality filter over a chunk's metadata."""
    if not where:
        return True
    return all(metadata.get(key) == value for key, value in where.items())


def _normalize(chunk: dict) -> dict:
    """Give dense and sparse hits one shape: text plus a flat metadata dict.

    Every result carries a `chunk_id`. Chunks indexed before ids were stored
    get a stable one derived from document and position, so RRF can still
    recognise the same chunk arriving from both branches.
    """
    metadata = dict(chunk.get("metadata") or {})
    for key in ("document_id", "filename", "page_num", "chunk_index", "chunk_id"):
        if key in chunk and key not in metadata:
            metadata[key] = chunk[key]
    if not metadata.get("chunk_id"):
        metadata["chunk_id"] = (
            f"{metadata.get('document_id')}:{metadata.get('chunk_index', metadata.get('page_num', 0))}"
        )
    return {"text": chunk.get("text", ""), "metadata": metadata}


def _dedup_key(chunk: dict) -> str:
    """Stable identity for RRF fusion.

    Prefers the chunk id so two distinct chunks that happen to share a
    leading prefix are not merged. Falls back to the text when no id is
    present (e.g. dense hits reconstructed from Chroma).
    """
    chunk_id = (chunk.get("metadata") or {}).get("chunk_id")
    if chunk_id:
        return str(chunk_id)
    return str(chunk.get("text", ""))[:100]


class BM25Index:
    def __init__(self):
        self.corpus: list[dict] = []
        self.tokenized: list[list[str]] = []
        self.bm25: BM25Okapi | None = None

    def _rebuild(self) -> None:
        self.tokenized = [tokenize(c["text"]) for c in self.corpus]
        self.bm25 = _BM25(self.tokenized) if self.tokenized else None

    def add(self, chunks: list[dict]) -> None:
        for chunk in chunks:
            self.corpus.append(_normalize(chunk))
        self._rebuild()

    def remove_document(self, document_id: str) -> int:
        """Drop every chunk belonging to a document. Returns count removed."""
        before = len(self.corpus)
        self.corpus = [c for c in self.corpus if c["metadata"].get("document_id") != document_id]
        removed = before - len(self.corpus)
        if removed:
            self._rebuild()
        return removed

    def replace_document(self, document_id: str, chunks: list[dict]) -> None:
        """Atomically swap a document's chunks, so re-indexing cannot duplicate."""
        self.remove_document(document_id)
        if chunks:
            self.add(chunks)

    def search(self, query: str, top_k: int = 8, where: dict | None = None) -> list[dict]:
        if not self.bm25 or not self.corpus:
            return []
        tokenized_query = tokenize(query)
        if not tokenized_query:
            return []
        scores = self.bm25.get_scores(tokenized_query)

        # Score the whole corpus, then filter, so a document filter can never
        # starve the result set by being applied before the top-k cut.
        ranked = sorted(
            (i for i, s in enumerate(scores) if s > 0),
            key=lambda i: scores[i],
            reverse=True,
        )

        results = []
        for idx in ranked:
            result = dict(self.corpus[idx])
            if not _matches_where(result["metadata"], where):
                continue
            result["bm25_score"] = float(scores[idx])
            results.append(result)
            if len(results) >= top_k:
                break
        return results


_bm25_index: BM25Index | None = None


def get_bm25_index() -> BM25Index:
    global _bm25_index
    if _bm25_index is None:
        _bm25_index = BM25Index()
    return _bm25_index


def rebuild_bm25_from_collection(collection_name: str = "documents") -> int:
    """Repopulate the in-memory BM25 index from persisted Chroma chunks.

    The dense index survives a restart but BM25 does not, so without this the
    sparse half of the hybrid search silently returns nothing on every boot
    after the first.
    """
    collection = get_or_create_collection(collection_name)
    total = collection.count()
    index = get_bm25_index()
    index.corpus = []
    if total == 0:
        index._rebuild()
        return 0

    batch = 500
    loaded = 0
    for offset in range(0, total, batch):
        got = collection.get(limit=batch, offset=offset, include=["documents", "metadatas"])
        documents = got.get("documents") or []
        metadatas = got.get("metadatas") or []
        for i, doc in enumerate(documents):
            meta = metadatas[i] if i < len(metadatas) else {}
            chunk_id = meta.get("chunk_id")
            if not chunk_id:
                meta = {**meta, "chunk_id": f"{meta.get('document_id')}:{meta.get('chunk_index')}"}
            index.corpus.append({"text": doc, "metadata": meta})
            loaded += 1

    index._rebuild()
    return loaded


def hybrid_search(
    query: str,
    top_k: int = 8,
    dense_weight: float = 0.6,
    sparse_weight: float = 0.4,
    where: dict | None = None,
) -> list[dict]:
    dense_results = [_normalize(r) for r in search_similar(query, top_k=top_k, where=where)]

    bm25 = get_bm25_index()
    sparse_results = bm25.search(query, top_k=top_k, where=where)

    # Reciprocal Rank Fusion
    rrf_scores: dict[str, float] = {}
    rrf_map: dict[str, dict] = {}
    k = 60

    for rank, result in enumerate(dense_results):
        key = _dedup_key(result)
        rrf_scores[key] = rrf_scores.get(key, 0) + dense_weight / (k + rank + 1)
        rrf_map[key] = result

    for rank, result in enumerate(sparse_results):
        key = _dedup_key(result)
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
