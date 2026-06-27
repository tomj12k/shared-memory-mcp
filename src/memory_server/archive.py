from __future__ import annotations
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from . import config, storage


def check_and_archive(name: str) -> bool:
    path = storage.memory_path(name)
    if not path.exists():
        return False
    if path.stat().st_size <= config.ARCHIVE_THRESHOLD_BYTES:
        return False

    content = path.read_text()
    # Split at frontmatter boundary
    parts = content.split("---", 2)
    if len(parts) < 3:
        return False  # malformed frontmatter, skip

    frontmatter = "---" + parts[1] + "---\n"
    body = parts[2]

    # Keep last ARCHIVE_KEEP_BYTES of body in active file
    keep = body[-config.ARCHIVE_KEEP_BYTES:]
    overflow = body[: -config.ARCHIVE_KEEP_BYTES]

    # Write archive file
    archive_dir = config.MEMORIES_DIR / "archive"
    archive_dir.mkdir(exist_ok=True)
    month = datetime.now(timezone.utc).strftime("%Y-%m")
    archive_path = archive_dir / f"{name}_{month}.md"
    if archive_path.exists():
        archive_path.write_text(archive_path.read_text() + overflow)
    else:
        archive_path.write_text(overflow)

    # Rewrite active file with pointer
    pointer = f"\n<!-- archive: archive/{archive_path.name} -->\n"
    path.write_text(frontmatter + keep + pointer)

    # Commit
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
    _git_commit(f"memory: archive {name} -> {archive_path.name} {ts}")
    return True


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
