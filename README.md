# shared-memory-mcp

A self-hosted MCP server that gives Claude and Codex a single shared memory store across all your machines.

Memories are markdown files in a local git repo, auto-committed on every write, and semantically searchable via ChromaDB + an OpenAI-compatible embedding endpoint. A local cache on each client machine means reads still work when the server is offline.

## How it works

```
Mac Mini (or any always-on machine)
├── ~/memories/          ← git repo, one .md file per memory
│   ├── MEMORY.md        ← auto-maintained index
│   └── archive/         ← rolled-over content when files get large
├── ~/memory-server/     ← this repo
└── ~/chroma/            ← ChromaDB vector index (not git-tracked)

Client machines (Mac, Linux, etc.)
└── ~/.memory-cache/     ← mirror of active files for offline reads
```

Every `memory_write` call:
1. Writes the markdown file
2. Auto-commits to git with a structured message (`memory: write <name> [tool/host] timestamp`)
3. Embeds and upserts chunks into ChromaDB
4. Syncs active files to the client's local cache

## MCP tools

| Tool | Args | Description |
|------|------|-------------|
| `memory_write` | `name`, `content`, `type`, `source_tool?` | Write or update a memory. Auto-commits + re-indexes. |
| `memory_read` | `name` | Read a memory by name. |
| `memory_list` | — | Return the MEMORY.md index. |
| `memory_search` | `query`, `limit?` | Semantic search across all memories including archives. |
| `memory_diff` | `name`, `n?` | Last N git commits + diffs for a memory. |
| `memory_delete` | `name` | Delete a memory. Auto-commits + removes from index. |
| `memory_sync` | — | Force refresh of the caller's local cache. |
| `memory_reindex` | — | Rebuild ChromaDB index from scratch (recovery tool). |

## Memory format

Every memory is a markdown file with YAML frontmatter:

```markdown
---
name: short-kebab-case-slug
description: one-line summary used for search relevance and the index
metadata:
  type: user | feedback | project | reference
---

Memory body here. Supports full markdown.
```

- **user** — who you are, preferences, expertise
- **feedback** — corrections or confirmations of non-obvious approaches
- **project** — ongoing work, goals, decisions
- **reference** — external systems, locations, pointers

## Rolling archive

When a memory file exceeds 3 KB, older content is automatically moved to `archive/<name>_YYYY-MM.md` and the active file keeps only the most recent ~1 KB. Archive files are embedded into ChromaDB so they remain searchable.

## Requirements

- Python 3.13+
- [uv](https://docs.astral.sh/uv/)
- git
- An OpenAI-compatible embedding endpoint (local or remote)

The server uses [FastMCP](https://github.com/jlowin/fastmcp) and ChromaDB. No cloud dependencies — everything runs on your LAN.

## Setup

### 1. Clone and install

```bash
git clone https://github.com/tomj12k/shared-memory-mcp.git ~/memory-server
cd ~/memory-server
uv sync
```

### 2. Create the memories repo

```bash
git init ~/memories
echo "chroma/" > ~/memories/.gitignore
```

### 3. Configure environment

All settings are environment variables with sensible defaults:

| Variable | Default | Description |
|----------|---------|-------------|
| `MEMORIES_DIR` | `~/memories` | Path to the git-backed memories directory |
| `CHROMA_DIR` | `~/chroma` | Path for ChromaDB storage |
| `CACHE_DIR` | `~/.memory-cache` | Local cache directory on the server host |
| `MEMORY_SERVER_PORT` | `7777` | Port the MCP server listens on |
| `SPARK_BASE_URL` | `http://127.0.0.1:8000/v1` | OpenAI-compatible embedding endpoint |
| `SPARK_API_KEY` | `not-needed-for-local` | API key (ignored by most local servers) |
| `EMBEDDING_MODEL` | `nomic-embed-text` | Embedding model name |
| `ARCHIVE_THRESHOLD_BYTES` | `3072` | File size that triggers archiving |
| `ARCHIVE_KEEP_BYTES` | `1024` | Bytes to retain in the active file after archiving |

### 4. Run the server

```bash
MEMORIES_DIR=~/memories uv run memory-server
```

### 5. Auto-start on macOS (launchd)

Edit `com.piecakes.memory-server.plist` to set your paths and environment variables, then:

```bash
cp com.piecakes.memory-server.plist ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/com.piecakes.memory-server.plist
```

### 6. Connect a client

**Claude Code** — add to `~/.claude.json`:

```bash
claude mcp add --transport http shared-memory http://<server-ip>:7777/mcp
```

**Codex** — add to `~/.codex/config.toml` or equivalent:

```json
{
  "mcpServers": [
    { "name": "shared-memory", "url": "http://<server-ip>:7777/mcp" }
  ]
}
```

### 7. Tell Claude to use it

Add to `~/.claude/CLAUDE.md` (global) so all sessions default to the shared store:

```markdown
## Shared Memory System

Use `mcp__shared-memory__memory_write` for all memory saves — never the local Write tool.
Every memory must include frontmatter with `name`, `description`, and `metadata.type`.
Use `mcp__shared-memory__memory_list/read/search` for recalls.
```

## Embedding server

Any OpenAI-compatible `/v1/embeddings` endpoint works. Some options:

- **Local sentence-transformers** (what this was built with): run a small FastAPI wrapper around `sentence-transformers` — see [`embed-server.py`](docs/embed-server-example.py) for a minimal example
- **Ollama**: `ollama serve` exposes a compatible endpoint at `http://localhost:11434/v1`
- **OpenAI API**: set `SPARK_BASE_URL=https://api.openai.com/v1` and `SPARK_API_KEY=sk-...`

If the embedding server is unreachable, writes still succeed — the file is committed to git and the local cache is updated. Run `memory_reindex` once the embedding server is back to rebuild the vector index.

## Project structure

```
src/memory_server/
├── server.py    — FastMCP app, all 8 tools
├── storage.py   — git-backed CRUD, auto-commit, index maintenance
├── vector.py    — ChromaDB upsert/search/reindex
├── archive.py   — rolling archive logic
├── cache.py     — local cache sync
└── config.py    — all settings from environment variables
tests/
com.piecakes.memory-server.plist   — macOS launchd service
com.piecakes.spark-tunnel.plist    — optional SSH tunnel for embedding server
```

## License

MIT
