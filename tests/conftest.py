"""Pytest fixtures for git-graph tests."""

from __future__ import annotations

import os
import shutil
import subprocess
import tempfile

import pytest


@pytest.fixture
def tmp_git_repo():
    """Create a temporary git repository with multiple branches and commits.

    Yields the path to the repo. Cleans up after the test.
    """
    tmpdir = tempfile.mkdtemp(prefix="git_graph_test_")
    repo_path = os.path.join(tmpdir, "repo")
    os.makedirs(repo_path)

    def _run(cmd: list[str], cwd: str = repo_path) -> str:
        result = subprocess.run(
            cmd, cwd=cwd, capture_output=True, text=True, encoding="utf-8",
        )
        if result.returncode != 0:
            raise RuntimeError(f"Command failed: {cmd}\n{result.stderr}")
        return result.stdout.strip()

    try:
        _run(["git", "init"])
        _run(["git", "config", "user.name", "Test User"])
        _run(["git", "config", "user.email", "test@example.com"])

        # Commit on main
        with open(os.path.join(repo_path, "README.md"), "w") as f:
            f.write("# Test Repo")
        _run(["git", "add", "README.md"])
        _run(["git", "commit", "-m", "Initial commit"])

        # Create a feature branch
        _run(["git", "checkout", "-b", "feature/test-feature"])
        with open(os.path.join(repo_path, "feature.py"), "w") as f:
            f.write("def hello(): pass\n")
        _run(["git", "add", "feature.py"])
        _run(["git", "commit", "-m", "Add feature"])

        with open(os.path.join(repo_path, "feature.py"), "w") as f:
            f.write("def hello():\n    return 'hi'\n")
        _run(["git", "add", "feature.py"])
        _run(["git", "commit", "-m", "Update feature"])

        # Back to main and create a hotfix
        _run(["git", "checkout", "main"])
        _run(["git", "checkout", "-b", "hotfix/fix-bug"])
        with open(os.path.join(repo_path, "bugfix.py"), "w") as f:
            f.write("# fix\n")
        _run(["git", "add", "bugfix.py"])
        _run(["git", "commit", "-m", "Fix critical bug"])

        # Merge hotfix back to main
        _run(["git", "checkout", "main"])
        _run(["git", "merge", "hotfix/fix-bug", "--no-ff", "-m", "Merge hotfix"])
        _run(["git", "branch", "-d", "hotfix/fix-bug"])

        # Create a tag
        _run(["git", "tag", "v1.0"])

        yield repo_path

    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


@pytest.fixture
def sample_commit_lines() -> list[str]:
    """Raw commit lines in git-graph format."""
    return [
        "a1b2c3d4e5f6789012345678901234567890abc| |2025-01-01T00:00:00+00:00|Alice|Initial commit",
        "b2c3d4e5f6789012345678901234567890abcd1|a1b2c3d4e5f6789012345678901234567890abc|2025-01-02T00:00:00+00:00|Bob|Add feature X",
        "c3d4e5f6789012345678901234567890abcd12|b2c3d4e5f6789012345678901234567890abcd1|2025-01-03T00:00:00+00:00|Alice|Fix bug in X",
        "d4e5f6789012345678901234567890abcd123|c3d4e5f6789012345678901234567890abcd12 a1b2c3d4e5f6789012345678901234567890abc|2025-01-04T00:00:00+00:00|Bob|Merge branch 'feature'",
    ]


@pytest.fixture
def sample_ref_lines() -> list[str]:
    """Raw ref lines in git-graph format."""
    return [
        "main|d4e5f6789012345678901234567890abcd123|refs/heads/main|commit",
        "feature/test|b2c3d4e5f6789012345678901234567890abcd1|refs/heads/feature/test|commit",
        "origin/main|d4e5f6789012345678901234567890abcd123|refs/remotes/origin/main|commit",
        "v1.0|c3d4e5f6789012345678901234567890abcd12|refs/tags/v1.0|tag",
    ]
