from __future__ import annotations
from pathlib import Path
import chromadb
from openai import OpenAI
from . import config

_COLLECTION_NAME = "memories"
_CHUNK_SIZE = 800   # chars (~200 tokens)
_CHUNK_OVERLAP = 200


def _client() -> chromadb.ClientAPI:
    config.CHROMA_DIR.mkdir(parents=True, exist_ok=True)
    return chromadb.PersistentClient(path=str(config.CHROMA_DIR))


def _collection() -> chromadb.Collection:
    return _client().get_or_create_collection(_COLLECTION_NAME)


def _embed_texts(texts: list[str]) -> list[list[float]]:
    openai_client = OpenAI(base_url=config.SPARK_BASE_URL, api_key=config.SPARK_API_KEY)
    response = openai_client.embeddings.create(model=config.EMBEDDING_MODEL, input=texts)
    return [item.embedding for item in response.data]


def _try_embed_texts(texts: list[str]) -> list[list[float]] | None:
    """Returns None if the embedding server is unreachable."""
    try:
        return _embed_texts(texts)
    except Exception:
        return None


def _chunk(text: str) -> list[str]:
    chunks = []
    start = 0
    while start < len(text):
        end = start + _CHUNK_SIZE
        chunks.append(text[start:end])
        start += _CHUNK_SIZE - _CHUNK_OVERLAP
    return chunks or [text]


def upsert_memory(name: str, content: str, is_archive: bool, file_path: str) -> None:
    col = _collection()
    # Remove existing chunks for this memory
    try:
        existing = col.get(where={"name": name})
        if existing["ids"]:
            col.delete(ids=existing["ids"])
    except Exception:
        pass

    chunks = _chunk(content)
    embeddings = _try_embed_texts(chunks)
    if embeddings is None:
        return  # Spark unreachable; memory_reindex will catch up later
    ids = [f"{name}__chunk_{i}" for i in range(len(chunks))]
    metadatas = [
        {"name": name, "is_archive": is_archive, "file_path": file_path, "chunk_index": i}
        for i in range(len(chunks))
    ]
    col.add(ids=ids, embeddings=embeddings, documents=chunks, metadatas=metadatas)


def delete_memory_vectors(name: str) -> None:
    col = _collection()
    try:
        existing = col.get(where={"name": name})
        if existing["ids"]:
            col.delete(ids=existing["ids"])
    except Exception:
        pass


def search_memories(query: str, limit: int = 5) -> list[dict]:
    col = _collection()
    q_emb_list = _try_embed_texts([query])
    if q_emb_list is None:
        return []
    results = col.query(query_embeddings=[q_emb_list[0]], n_results=min(limit, col.count() or 1))
    output = []
    seen_names: set[str] = set()
    for doc, meta, distance in zip(
        results["documents"][0], results["metadatas"][0], results["distances"][0]
    ):
        name = meta["name"]
        if name in seen_names:
            continue
        seen_names.add(name)
        output.append({
            "name": name,
            "snippet": doc[:200],
            "score": round(1 - distance, 3),
            "is_archive": meta["is_archive"],
            "file_path": meta["file_path"],
        })
    return output


def reindex_all(memories_dir: Path) -> None:
    _client().delete_collection(_COLLECTION_NAME)
    col = _collection()  # recreate empty
    for md_file in memories_dir.rglob("*.md"):
        if md_file.name == "MEMORY.md":
            continue
        name = md_file.stem
        is_archive = "archive" in md_file.parts
        content = md_file.read_text()
        chunks = _chunk(content)
        embeddings = _embed_texts(chunks)
        ids = [f"{name}__chunk_{i}" for i in range(len(chunks))]
        metadatas = [
            {"name": name, "is_archive": is_archive, "file_path": str(md_file), "chunk_index": i}
            for i in range(len(chunks))
        ]
        col.add(ids=ids, embeddings=embeddings, documents=chunks, metadatas=metadatas)
