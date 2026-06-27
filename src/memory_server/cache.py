from __future__ import annotations
import shutil
from pathlib import Path


def sync(memories_dir: Path, cache_dir: Path) -> int:
    """Copy active memory files (not archive/, not MEMORY.md) to cache_dir."""
    cache_dir.mkdir(parents=True, exist_ok=True)
    count = 0
    for md_file in memories_dir.glob("*.md"):
        if md_file.name == "MEMORY.md":
            continue
        shutil.copy2(md_file, cache_dir / md_file.name)
        count += 1
    return count
