from __future__ import annotations
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from . import config


def memory_path(name: str) -> Path:
    return config.MEMORIES_DIR / f"{name}.md"


def _git_commit(message: str) -> None:
    d = config.MEMORIES_DIR
    subprocess.run(["git", "add", "-A"], cwd=d, check=True, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", message],
        cwd=d,
        check=True,
        capture_output=True,
        env={**__import__("os").environ, "GIT_AUTHOR_NAME": "memory-server",
             "GIT_AUTHOR_EMAIL": "memory@local",
             "GIT_COMMITTER_NAME": "memory-server",
             "GIT_COMMITTER_EMAIL": "memory@local"},
    )


def _extract_description(content: str) -> str:
    for line in content.splitlines():
        if line.startswith("description:"):
            return line.split(":", 1)[1].strip()
    return ""


def update_index(memories_dir: Path) -> None:
    lines = ["# Memory Index\n"]
    for f in sorted(memories_dir.glob("*.md")):
        if f.name == "MEMORY.md":
            continue
        name = f.stem
        desc = _extract_description(f.read_text())
        lines.append(f"- [{name}]({f.name}) — {desc}")
    (memories_dir / "MEMORY.md").write_text("\n".join(lines) + "\n")


def read_memory(name: str) -> str:
    path = memory_path(name)
    if not path.exists():
        raise FileNotFoundError(f"Memory {name} not found")
    return path.read_text()


def write_memory(name: str, content: str, source_tool: str, source_host: str) -> None:
    memory_path(name).write_text(content)
    update_index(config.MEMORIES_DIR)
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
    _git_commit(f"memory: write {name} [{source_tool}/{source_host}] {ts}")


def delete_memory(name: str) -> None:
    path = memory_path(name)
    if not path.exists():
        raise FileNotFoundError(f"Memory {name} not found")
    path.unlink()
    update_index(config.MEMORIES_DIR)
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
    _git_commit(f"memory: delete {name} [memory-server/local] {ts}")


def list_memories() -> str:
    index = config.MEMORIES_DIR / "MEMORY.md"
    if not index.exists():
        return "# Memory Index\n\n(empty)"
    return index.read_text()


def diff_memory(name: str, n: int = 5) -> str:
    path = memory_path(name)
    result = subprocess.run(
        ["git", "log", f"-{n}", "--patch", "--follow", "--", path.name],
        cwd=config.MEMORIES_DIR,
        capture_output=True,
        text=True,
    )
    return result.stdout or f"No history found for '{name}'"
