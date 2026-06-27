from pathlib import Path
import os

MEMORIES_DIR = Path(os.getenv("MEMORIES_DIR", str(Path.home() / "memories")))
CHROMA_DIR = Path(os.getenv("CHROMA_DIR", str(Path.home() / "chroma")))
CACHE_DIR = Path(os.getenv("CACHE_DIR", str(Path.home() / ".memory-cache")))
SERVER_PORT = int(os.getenv("MEMORY_SERVER_PORT", "7777"))
ARCHIVE_THRESHOLD_BYTES = int(os.getenv("ARCHIVE_THRESHOLD_BYTES", str(3 * 1024)))
ARCHIVE_KEEP_BYTES = int(os.getenv("ARCHIVE_KEEP_BYTES", str(1024)))
SPARK_BASE_URL = os.getenv("SPARK_BASE_URL", "http://127.0.0.1:8000/v1")
SPARK_API_KEY = os.getenv("SPARK_API_KEY", "not-needed-for-local")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "nomic-embed-text")
