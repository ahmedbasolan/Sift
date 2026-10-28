import chromadb
from sentence_transformers import SentenceTransformer

from app.config import settings

_model: SentenceTransformer | None = None
_client: chromadb.ClientAPI | None = None


def get_embedding_model() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer(settings.EMBEDDING_MODEL)
    return _model


def get_chroma_client() -> chromadb.ClientAPI:
    global _client
    if _client is None:
        _client = chromadb.PersistentClient(path=settings.CHROMA_PERSIST_DIR)
    return _client


def get_or_create_collection(name: str = "documents"):
    client = get_chroma_client()
    return client.get_or_create_collection(name=name, metadata={"hnsw:space": "cosine"})


def embed_texts(texts: list[str]) -> list[list[float]]:
    model = get_embedding_model()
    embeddings = model.encode(texts, show_progress_bar=False)
    vectors: list[list[float]] = embeddings.tolist()
    return vectors


def add_chunks_to_collection(
    chunks: list[dict],
    document_id: str,
    filename: str,
    collection_name: str = "documents",
):
    if not chunks:
        return 0

    collection = get_or_create_collection(collection_name)

    ids = [c["id"] for c in chunks]
    texts = [c["text"] for c in chunks]
    embeddings = embed_texts(texts)
    metadatas = [
        {
            "document_id": document_id,
            "filename": filename,
            "page_num": c["page_num"],
            "chunk_index": i,
            "chunk_id": c["id"],
        }
        for i, c in enumerate(chunks)
    ]

    collection.upsert(
        ids=ids,
        embeddings=embeddings,
        documents=texts,
        metadatas=metadatas,
    )
    return len(ids)


def search_similar(
    query: str,
    top_k: int = 8,
    collection_name: str = "documents",
    where: dict | None = None,
) -> list[dict]:
    collection = get_or_create_collection(collection_name)

    if collection.count() == 0:
        return []

    query_embedding = embed_texts([query])

    try:
        results = collection.query(
            query_embeddings=query_embedding,
            n_results=min(top_k, collection.count()),
            where=where if where else None,
        )
    except Exception as e:
        import sys

        print(f"[Sift] Embedding search error: {e}", file=sys.stderr)
        return []

    results_list = []
    if results and results.get("documents") and results["documents"][0]:
        for i, doc in enumerate(results["documents"][0]):
            meta = results["metadatas"][0][i] if results.get("metadatas") else {}
            dist = results["distances"][0][i] if results.get("distances") else 0
            results_list.append(
                {
                    "text": doc,
                    "metadata": meta,
                    "distance": dist,
                    "score": 1 - dist,
                }
            )
    return results_list


def delete_document_chunks(document_id: str, collection_name: str = "documents"):
    try:
        collection = get_or_create_collection(collection_name)
        collection.delete(where={"document_id": document_id})
    except Exception as e:
        import sys

        print(f"[Sift] Warning: failed to delete chunks for {document_id}: {e}", file=sys.stderr)
