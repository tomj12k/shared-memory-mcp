import pytest
from memory_server import archive, config, storage


def _big_content(name: str, size: int) -> str:
    body = "x" * size
    return f"---\nname: {name}\ndescription: big memory\nmetadata:\n  type: project\n---\n\n{body}"


def test_no_archive_when_small(memories_dir, monkeypatch):
    monkeypatch.setattr(config, "MEMORIES_DIR", memories_dir)
    monkeypatch.setattr(config, "ARCHIVE_THRESHOLD_BYTES", 3072)
    content = _big_content("small", 100)
    storage.write_memory("small", content, "claude", "host")
    did_archive = archive.check_and_archive("small")
    assert did_archive is False


def test_archives_when_over_threshold(memories_dir, monkeypatch):
    monkeypatch.setattr(config, "MEMORIES_DIR", memories_dir)
    monkeypatch.setattr(config, "ARCHIVE_THRESHOLD_BYTES", 200)
    monkeypatch.setattr(config, "ARCHIVE_KEEP_BYTES", 50)
    content = _big_content("big", 300)
    storage.write_memory("big", content, "claude", "host")
    did_archive = archive.check_and_archive("big")
    assert did_archive is True


def test_archive_file_created(memories_dir, monkeypatch):
    from pathlib import Path
    monkeypatch.setattr(config, "MEMORIES_DIR", memories_dir)
    monkeypatch.setattr(config, "ARCHIVE_THRESHOLD_BYTES", 200)
    monkeypatch.setattr(config, "ARCHIVE_KEEP_BYTES", 50)
    content = _big_content("archiveme", 300)
    storage.write_memory("archiveme", content, "claude", "host")
    archive.check_and_archive("archiveme")
    archive_files = list((memories_dir / "archive").glob("archiveme_*.md"))
    assert len(archive_files) == 1


def test_active_file_shrinks_after_archive(memories_dir, monkeypatch):
    monkeypatch.setattr(config, "MEMORIES_DIR", memories_dir)
    monkeypatch.setattr(config, "ARCHIVE_THRESHOLD_BYTES", 200)
    monkeypatch.setattr(config, "ARCHIVE_KEEP_BYTES", 50)
    content = _big_content("shrink", 300)
    storage.write_memory("shrink", content, "claude", "host")
    archive.check_and_archive("shrink")
    active = storage.memory_path("shrink").read_text()
    assert len(active) < 300
    assert "archive:" in active  # pointer line present
