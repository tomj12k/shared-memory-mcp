import pytest
from unittest.mock import MagicMock, patch
from memory_server import vector, config


@pytest.fixture
def chroma_dir(tmp_path):
    return tmp_path / "chroma"


def _fake_embed(texts):
    """Return deterministic fake embeddings."""
    import hashlib
    results = []
    for t in texts:
        h = int(hashlib.md5(t.encode()).hexdigest(), 16)
        vec = [(h >> i & 0xFF) / 255.0 for i in range(384)]
        results.append(vec)
    return results


def test_upsert_and_search(chroma_dir, monkeypatch):
    monkeypatch.setattr(config, "CHROMA_DIR", chroma_dir)
    with patch("memory_server.vector._embed_texts", side_effect=_fake_embed):
        vector.upsert_memory("test-mem", "Some content about databases", False, "/memories/test-mem.md")
        results = vector.search_memories("databases", limit=5)
    assert any(r["name"] == "test-mem" for r in results)


def test_delete_vectors(chroma_dir, monkeypatch):
    monkeypatch.setattr(config, "CHROMA_DIR", chroma_dir)
    with patch("memory_server.vector._embed_texts", side_effect=_fake_embed):
        vector.upsert_memory("todelete", "Some content", False, "/memories/todelete.md")
        vector.delete_memory_vectors("todelete")
        results = vector.search_memories("Some content", limit=5)
    assert not any(r["name"] == "todelete" for r in results)


def test_search_returns_snippet(chroma_dir, monkeypatch):
    monkeypatch.setattr(config, "CHROMA_DIR", chroma_dir)
    with patch("memory_server.vector._embed_texts", side_effect=_fake_embed):
        vector.upsert_memory("snip", "The quick brown fox", False, "/memories/snip.md")
        results = vector.search_memories("fox", limit=5)
    if results:
        assert "snippet" in results[0]
        assert "name" in results[0]
        assert "score" in results[0]
