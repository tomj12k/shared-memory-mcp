import pytest
import subprocess
from pathlib import Path


@pytest.fixture
def memories_dir(tmp_path):
    """A temporary git-backed memories directory."""
    d = tmp_path / "memories"
    d.mkdir()
    subprocess.run(["git", "init"], cwd=d, check=True, capture_output=True)
    subprocess.run(
        ["git", "config", "user.email", "test@test.com"], cwd=d, check=True
    )
    subprocess.run(
        ["git", "config", "user.name", "Test"], cwd=d, check=True
    )
    return d
