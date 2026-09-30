import pytest
from app.search import BM25Index, _dedup_key, _matches_where, _normalize, hybrid_search


def _chunk(text, doc_id, filename="doc.md", page=1, chunk_id=None, index=0):
    return {
        "text": text,
        "page_num": page,
        "document_id": doc_id,
        "filename": filename,
        "chunk_id": chunk_id or f"{doc_id}:{index}",
    }


@pytest.fixture
def index():
    idx = BM25Index()
    idx.add(
        [
            _chunk(
                "Acme Robotics revenue grew 38 percent on customer concentration",
                "doc-acme",
                "acme.md",
                chunk_id="doc-acme:0",
            ),
            _chunk(
                "Acme Robotics faces pending EU robotics safety regulations",
                "doc-acme",
                "acme.md",
                chunk_id="doc-acme:1",
            ),
        ]
    )
    idx.add(
        [
            _chunk(
                "Snap Inc revenue was 5.3 billion with advertising concentration",
                "doc-snap",
                "snap.pdf",
                chunk_id="doc-snap:0",
            ),
            _chunk(
                "Snap Inc daily active users reached 453 million in Q4",
                "doc-snap",
                "snap.pdf",
                chunk_id="doc-snap:1",
            ),
        ]
    )
    return idx


# --- the regression that caused cross-document evidence contamination ---


def test_sparse_search_respects_where_filter(index):
    results = index.search("revenue", top_k=10, where={"document_id": "doc-snap"})
    assert results
    assert {r["metadata"]["document_id"] for r in results} == {"doc-snap"}


def test_sparse_search_without_filter_spans_documents(index):
    results = index.search("revenue", top_k=10)
    assert {r["metadata"]["document_id"] for r in results} == {"doc-acme", "doc-snap"}


def test_where_filter_can_still_reach_beyond_top_k(index):
    """Filtering must not be applied before the top-k cut, or a filtered
    branch can come back empty while the corpus clearly has matches."""
    results = index.search("Acme", top_k=1, where={"document_id": "doc-acme"})
    assert results, "filtering before top-k starved the result set"
    assert results[0]["metadata"]["document_id"] == "doc-acme"


def test_hybrid_search_only_returns_requested_document(index, monkeypatch):
    monkeypatch.setattr("app.search.get_bm25_index", lambda: index)
    monkeypatch.setattr("app.search.search_similar", lambda *a, **k: [])

    results = hybrid_search("revenue", top_k=10, where={"document_id": "doc-snap"})
    assert results
    assert {r["metadata"]["document_id"] for r in results} == {"doc-snap"}


def test_hybrid_search_falls_back_to_dense_when_sparse_is_empty(index, monkeypatch):
    """The dense branch must still work if BM25 has nothing indexed."""
    monkeypatch.setattr("app.search.get_bm25_index", lambda: BM25Index())
    monkeypatch.setattr(
        "app.search.search_similar",
        lambda *a, **k: [{"text": "Snap Inc revenue", "metadata": {"document_id": "doc-snap"}}],
    )
    results = hybrid_search("revenue", top_k=5, where={"document_id": "doc-snap"})
    assert len(results) == 1
    assert results[0]["metadata"]["document_id"] == "doc-snap"


def test_dense_and_sparse_hits_for_same_chunk_are_fused_not_duplicated(index, monkeypatch):
    """The chunk present in both branches must appear once, with both scores fused."""
    shared = _chunk(
        "Snap Inc revenue was 5.3 billion", "doc-snap", "snap.pdf", chunk_id="doc-snap:0"
    )
    dense_hit = {
        "text": shared["text"],
        "metadata": {
            "document_id": shared["document_id"],
            "filename": shared["filename"],
            "page_num": shared["page_num"],
            "chunk_id": shared["chunk_id"],
        },
    }
    monkeypatch.setattr("app.search.get_bm25_index", lambda: index)
    monkeypatch.setattr("app.search.search_similar", lambda *a, **k: [dense_hit])

    results = hybrid_search("Snap Inc revenue", top_k=10, where={"document_id": "doc-snap"})

    shared_hits = [r for r in results if r["metadata"]["chunk_id"] == "doc-snap:0"]
    assert len(shared_hits) == 1, f"chunk fused twice, got {len(shared_hits)} copies"

    # dense (0.6/61) + sparse (0.4/61) both contributed
    expected = 0.6 / 61 + 0.4 / 61
    assert shared_hits[0]["rrf_score"] == pytest.approx(expected)

    # and it is not beaten by a chunk that only one branch returned
    assert results[0]["metadata"]["chunk_id"] == "doc-snap:0"


# --- supporting behaviour ---


def test_remove_document_drops_only_that_document(index):
    assert index.remove_document("doc-acme") == 2
    assert {c["metadata"]["document_id"] for c in index.corpus} == {"doc-snap"}
    assert index.search("Acme", top_k=10) == []
    assert index.search("Snap", top_k=10)


def test_replace_document_does_not_duplicate_on_reupload(index):
    before = len(index.corpus)
    index.replace_document(
        "doc-acme", [_chunk("Acme re-uploaded body", "doc-acme", "acme.md", chunk_id="new:0")]
    )
    assert len(index.corpus) == before - 2 + 1
    assert len([c for c in index.corpus if c["metadata"]["document_id"] == "doc-acme"]) == 1
    assert index.search("Acme", top_k=5)


def test_dedup_key_uses_chunk_id_not_text_prefix():
    a = _chunk("shared opening text one", "doc-a", chunk_id="doc-a:0")
    b = _chunk("shared opening text two", "doc-b", chunk_id="doc-b:0")
    assert _dedup_key(a) != _dedup_key(b)


def test_normalize_flattens_sparse_shape_into_metadata():
    out = _normalize({"text": "x", "document_id": "d1", "filename": "f.md", "page_num": 2})
    assert out["metadata"]["document_id"] == "d1"
    assert out["metadata"]["filename"] == "f.md"
    assert out["metadata"]["page_num"] == 2


def test_matches_where_treats_none_as_no_filter():
    assert _matches_where({"document_id": "d1"}, None)
    assert _matches_where({"document_id": "d1"}, {})
    assert not _matches_where({"document_id": "d2"}, {"document_id": "d1"})


def test_empty_query_returns_no_sparse_hits(index):
    assert index.search("", top_k=5) == []


def test_unmatched_token_scores_zero_and_is_dropped(index):
    assert index.search("zzzzznotpresent", top_k=5) == []
