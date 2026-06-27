import pytest
from pathlib import Path
from memory_server import cache


def test_sync_copies_active_files(tmp_path):
    memories = tmp_path / "memories"
    memories.mkdir()
    (memories / "user_role.md").write_text("content a")
    (memories / "project_wow.md").write_text("content b")
    (memories / "MEMORY.md").write_text("# index")
    archive_dir = memories / "archive"
    archive_dir.mkdir()
    (archive_dir / "user_role_2026-06.md").write_text("old content")

    cache_dir = tmp_path / "cache"
    count = cache.sync(memories, cache_dir)

    assert count == 2  # user_role + project_wow, not MEMORY.md, not archive
    assert (cache_dir / "user_role.md").read_text() == "content a"
    assert (cache_dir / "project_wow.md").read_text() == "content b"
    assert not (cache_dir / "archive").exists()


def test_sync_creates_cache_dir(tmp_path):
    memories = tmp_path / "memories"
    memories.mkdir()
    (memories / "foo.md").write_text("foo")
    cache_dir = tmp_path / "nonexistent" / "cache"
    cache.sync(memories, cache_dir)
    assert cache_dir.exists()


def test_sync_overwrites_stale(tmp_path):
    memories = tmp_path / "memories"
    memories.mkdir()
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()
    (memories / "item.md").write_text("new version")
    (cache_dir / "item.md").write_text("old version")
    cache.sync(memories, cache_dir)
    assert (cache_dir / "item.md").read_text() == "new version"
