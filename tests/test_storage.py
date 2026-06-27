import pytest
from pathlib import Path
from memory_server import storage, config


def test_write_and_read(memories_dir, monkeypatch):
    monkeypatch.setattr(config, "MEMORIES_DIR", memories_dir)
    content = "---\nname: test\ndescription: a test\nmetadata:\n  type: user\n---\n\nHello world."
    storage.write_memory("test", content, "claude", "mac-air")
    assert storage.read_memory("test") == content


def test_read_missing_raises(memories_dir, monkeypatch):
    monkeypatch.setattr(config, "MEMORIES_DIR", memories_dir)
    with pytest.raises(FileNotFoundError):
        storage.read_memory("nonexistent")


def test_write_creates_git_commit(memories_dir, monkeypatch):
    import subprocess
    monkeypatch.setattr(config, "MEMORIES_DIR", memories_dir)
    content = "---\nname: foo\ndescription: bar\nmetadata:\n  type: project\n---\n\nContent."
    storage.write_memory("foo", content, "codex", "mac-mini")
    log = subprocess.check_output(
        ["git", "log", "--oneline"], cwd=memories_dir, text=True
    )
    assert "memory: write foo [codex/mac-mini]" in log


def test_delete_memory(memories_dir, monkeypatch):
    monkeypatch.setattr(config, "MEMORIES_DIR", memories_dir)
    content = "---\nname: todel\ndescription: x\nmetadata:\n  type: user\n---\n\nBye."
    storage.write_memory("todel", content, "claude", "host")
    storage.delete_memory("todel")
    with pytest.raises(FileNotFoundError):
        storage.read_memory("todel")


def test_list_memories_returns_index(memories_dir, monkeypatch):
    monkeypatch.setattr(config, "MEMORIES_DIR", memories_dir)
    content = "---\nname: listed\ndescription: I am listed\nmetadata:\n  type: reference\n---\n\nBody."
    storage.write_memory("listed", content, "claude", "host")
    index = storage.list_memories()
    assert "listed" in index
    assert "I am listed" in index


def test_diff_memory(memories_dir, monkeypatch):
    monkeypatch.setattr(config, "MEMORIES_DIR", memories_dir)
    content = "---\nname: diffme\ndescription: x\nmetadata:\n  type: user\n---\n\nV1."
    storage.write_memory("diffme", content, "claude", "host")
    content2 = content.replace("V1.", "V2.")
    storage.write_memory("diffme", content2, "claude", "host")
    diff = storage.diff_memory("diffme", n=2)
    assert "V1" in diff or "V2" in diff
