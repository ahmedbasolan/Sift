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
    return client.get_or_create_collection(
        name=name,
        metadata={"hnsw:space": "cosine"}
    )


def embed_texts(texts: list[str]) -> list[list[float]]:
    model = get_embedding_model()
    embeddings = model.encode(texts, show_progress_bar=False)
    return embeddings.tolist()


def add_chunks_to_collection(
    chunks: list[dict],
    document_id: str,
    filename: str,
    collection_name: str = "documents"
):
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
    query_embedding = embed_texts([query])

    where_filter = where if where else None
    results = collection.query(
        query_embeddings=query_embedding,
        n_results=top_k,
        where=where_filter,
        include=["documents", "metadatas", "distances"],
    )

    results_list = []
    if results["documents"] and results["documents"][0]:
        for i, doc in enumerate(results["documents"][0]):
            results_list.append({
                "text": doc,
                "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                "distance": results["distances"][0][i] if results["distances"] else 0,
                "score": 1 - (results["distances"][0][i] if results["distances"] else 0),
            })
    return results_list


def delete_document_chunks(document_id: str, collection_name: str = "documents"):
    try:
        collection = get_or_create_collection(collection_name)
        collection.delete(where={"document_id": document_id})
    except Exception:
        pass
