from __future__ import annotations
import socket
from pathlib import Path
from fastmcp import FastMCP
from . import archive, cache, config, storage, vector

mcp = FastMCP("shared-memory")


@mcp.tool()
def memory_read(name: str) -> str:
    """Read a memory by name. Returns its full markdown content."""
    try:
        return storage.read_memory(name)
    except FileNotFoundError as e:
        return f"Error: {e}"


@mcp.tool()
def memory_write(name: str, content: str, type: str, source_tool: str = "unknown") -> str:
    """Write or update a memory. Auto-commits to git and re-indexes in ChromaDB."""
    host = socket.gethostname()
    storage.write_memory(name, content, source_tool, host)
    archive.check_and_archive(name)
    # Re-read after possible archiving
    current = storage.memory_path(name).read_text()
    vector.upsert_memory(name, current, False, str(storage.memory_path(name)))
    cache.sync(config.MEMORIES_DIR, config.CACHE_DIR)
    return f"Memory '{name}' written, indexed, and cache synced."


@mcp.tool()
def memory_delete(name: str) -> str:
    """Delete a memory by name. Auto-commits to git and removes from ChromaDB."""
    try:
        storage.delete_memory(name)
        vector.delete_memory_vectors(name)
        cache.sync(config.MEMORIES_DIR, config.CACHE_DIR)
        return f"Memory '{name}' deleted."
    except FileNotFoundError as e:
        return f"Error: {e}"


@mcp.tool()
def memory_list() -> str:
    """List all memories. Returns the MEMORY.md index."""
    return storage.list_memories()


@mcp.tool()
def memory_search(query: str, limit: int = 5) -> str:
    """Semantic search across all memories (active + archive) using ChromaDB."""
    results = vector.search_memories(query, limit=limit)
    if not results:
        return "No results found."
    lines = [f"## Search results for: {query}\n"]
    for r in results:
        archive_tag = " [archive]" if r["is_archive"] else ""
        lines.append(f"### {r['name']}{archive_tag} (score: {r['score']})")
        lines.append(f"{r['snippet']}\n")
    return "\n".join(lines)


@mcp.tool()
def memory_diff(name: str, n: int = 5) -> str:
    """Show the last N git commits and diffs for a memory file."""
    return storage.diff_memory(name, n=n)


@mcp.tool()
def memory_sync() -> str:
    """Force a full refresh of the local cache from the memories directory."""
    count = cache.sync(config.MEMORIES_DIR, config.CACHE_DIR)
    return f"Cache synced: {count} files written to {config.CACHE_DIR}"


@mcp.tool()
def memory_reindex() -> str:
    """Rebuild the ChromaDB vector index from scratch."""
    vector.reindex_all(config.MEMORIES_DIR)
    return "ChromaDB index rebuilt from all memory files."


def main() -> None:
    mcp.run(transport="sse", host="0.0.0.0", port=config.SERVER_PORT)


if __name__ == "__main__":
    main()
