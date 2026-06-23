"""Subprocess wrappers for git commands. Zero external dependencies — stdlib only."""

import subprocess
import sys
from typing import Optional


class GitError(Exception):
    """Raised when a git command fails in an expected way (not a repo, empty repo, etc.)."""

    def __init__(self, message: str, exit_code: int = 2):
        super().__init__(message)
        self.exit_code = exit_code


def _run_git(args: list[str], cwd: str, allow_failure: bool = False) -> str:
    """Run a git command and return stdout. Raises GitError on failure unless allow_failure.

    Args:
        args: Git subcommand arguments (e.g. ['log', '--all']).
        cwd: Working directory (the repo path).
        allow_failure: If True, return empty string on non-zero exit instead of raising.

    Returns:
        stdout as string, decoded as UTF-8.

    Raises:
        GitError: When git exits non-zero and allow_failure is False.
    """
    try:
        result = subprocess.run(
            ["git"] + args,
            cwd=cwd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
    except FileNotFoundError:
        raise GitError(
            "git command not found. Please install git and ensure it is on your PATH."
        )

    if result.returncode != 0:
        if allow_failure:
            return ""
        stderr = result.stderr.strip()
        if "not a git repository" in stderr.lower():
            raise GitError(
                f"Not a git repository: {cwd}\nEnsure the path points to a valid git working tree."
            )
        raise GitError(f"git {' '.join(args)} failed:\n{stderr}")

    return result.stdout


def get_all_commits(repo_path: str, max_commits: Optional[int] = None) -> list[str]:
    """Get all commits across all branches in topological order (parents before children).

    Returns a list of raw lines in format: <full_hash>|<parent_hashes>|<iso_date>|<author>|<subject>

    Args:
        repo_path: Path to the git repository.
        max_commits: If set, limit to the most recent N commits (after topological sort).

    Returns:
        List of raw commit lines.

    Raises:
        GitError: If the repository has no commits.
    """
    format_str = "%H|%P|%aI|%an|%s"
    args = ["log", "--all", "--topo-order", "--reverse", f"--format={format_str}"]

    if max_commits is not None and max_commits > 0:
        # Apply limit after topological sort — get last N commits
        args.append(f"-n{max_commits}")

    output = _run_git(args, repo_path)

    if not output.strip():
        raise GitError(
            "Repository has no commits. Cannot generate a graph for an empty repository.",
            exit_code=2,
        )

    return [line for line in output.strip().split("\n") if line.strip()]


def get_refs(repo_path: str) -> list[str]:
    """Get all branch and tag references.

    Returns raw lines in format: <refname_short>|<objectname>|<full_refname>|<objecttype>

    Includes: refs/heads/, refs/remotes/, refs/tags/
    """
    format_str = "%(refname:short)|%(objectname)|%(refname)|%(objecttype)"
    output = _run_git(
        ["for-each-ref", f"--format={format_str}", "refs/heads/", "refs/remotes/", "refs/tags/"],
        repo_path,
    )
    return [line for line in output.strip().split("\n") if line.strip()]


def get_head_state(repo_path: str) -> tuple[Optional[str], str]:
    """Get HEAD state.

    Returns:
        (branch_name | None, commit_hash)
        - If HEAD points to a branch, branch_name is the branch name (e.g. "main").
        - If HEAD is detached, branch_name is None.
        - commit_hash is always the current HEAD commit hash.
    """
    # Try to get the symbolic ref (branch name)
    branch_output = _run_git(["symbolic-ref", "-q", "HEAD"], repo_path, allow_failure=True)

    branch_name: Optional[str] = None
    if branch_output.strip():
        # Output is like "refs/heads/main"
        raw_ref = branch_output.strip()
        if raw_ref.startswith("refs/heads/"):
            branch_name = raw_ref[len("refs/heads/"):]
        else:
            branch_name = raw_ref

    # Get the commit hash HEAD points to
    commit_hash = _run_git(["rev-parse", "HEAD"], repo_path).strip()

    return branch_name, commit_hash


def get_full_message(repo_path: str, commit_hash: str) -> str:
    """Get the full commit message for a given commit hash."""
    output = _run_git(
        ["log", "--format=%B", "-1", commit_hash],
        repo_path,
        allow_failure=True,
    )
    return output.strip()


def get_commit_messages_batch(repo_path: str, hashes: list[str]) -> dict[str, str]:
    """Get full commit messages for a batch of commit hashes efficiently.

    Uses a single git log invocation with all hashes.
    """
    if not hashes:
        return {}

    # Use git log with multiple hashes separated by spaces
    result = {}
    # Process in smaller batches to avoid command-line length limits
    batch_size = 100
    for i in range(0, len(hashes), batch_size):
        batch = hashes[i:i + batch_size]
        try:
            output = _run_git(
                ["log", "--format=%H%n%B%n---GITGRAPHMSG---", "-1"] + batch,
                repo_path,
                allow_failure=True,
            )
            # Parse the output: each commit is separated by ---GITGRAPHMSG---
            if output.strip():
                blocks = output.split("---GITGRAPHMSG---")
                for block in blocks:
                    block = block.strip()
                    if not block:
                        continue
                    lines = block.split("\n", 1)
                    if len(lines) >= 1:
                        h = lines[0].strip()
                        msg = lines[1].strip() if len(lines) > 1 else ""
                        result[h] = msg
        except GitError:
            pass

    return result


def get_merged_branches(repo_path: str) -> set[str]:
    """Get the set of local branch names that are fully merged to HEAD.

    Uses ``git branch --merged HEAD``.
    """
    output = _run_git(
        ["branch", "--merged", "HEAD", "--format=%(refname:short)"],
        repo_path,
        allow_failure=True,
    )
    merged: set[str] = set()
    for line in output.strip().split("\n"):
        name = line.strip()
        if name:
            merged.add(name)
    return merged


def get_file_author_stats(repo_path: str) -> dict[str, dict[str, int]]:
    """Get per-file author commit counts for bus factor analysis.

    Uses ``git log --all --format='%an' --name-only``.

    Returns:
        {file_path: {author_name: commit_count}}
    """
    output = _run_git(
        ["log", "--all", "--format=COMMIT_AUTHOR:%an", "--name-only"],
        repo_path,
        allow_failure=True,
    )

    file_authors: dict[str, dict[str, int]] = {}
    current_author = "Unknown"

    for line in output.split("\n"):
        line = line.strip()
        if not line:
            continue
        if line.startswith("COMMIT_AUTHOR:"):
            current_author = line[len("COMMIT_AUTHOR:"):].strip()
        else:
            # File path line
            file_authors.setdefault(line, {}).setdefault(current_author, 0)
            file_authors[line][current_author] += 1

    return file_authors


def get_commit_files(repo_path: str, commit_hash: str) -> list[dict]:
    """Get the list of changed files for a commit.

    Uses ``git diff-tree --no-commit-id --numstat -r <hash>``.

    Returns:
        List of {path, status, added, deleted} dicts.
        status is one of: A (added), M (modified), D (deleted), R (renamed).
    """
    # --name-status gives us the status letter per file
    name_output = _run_git(
        ["diff-tree", "--no-commit-id", "--name-status", "-r", commit_hash],
        repo_path,
        allow_failure=True,
    )
    # --numstat gives us the line counts
    numstat_output = _run_git(
        ["diff-tree", "--no-commit-id", "--numstat", "-r", commit_hash],
        repo_path,
        allow_failure=True,
    )

    files: list[dict] = []

    # Parse --name-status lines:  M\tpath
    name_lines = [l for l in name_output.strip().split("\n") if l.strip()]
    numstat_lines = [l for l in numstat_output.strip().split("\n") if l.strip()]

    # Build a dict from numstat: path -> (added, deleted)
    numstat_map: dict[str, tuple[int, int]] = {}
    for line in numstat_lines:
        parts = line.split("\t")
        if len(parts) >= 3:
            try:
                added = int(parts[0]) if parts[0] != "-" else 0
                deleted = int(parts[1]) if parts[1] != "-" else 0
            except ValueError:
                added, deleted = 0, 0
            numstat_map[parts[2]] = (added, deleted)

    for line in name_lines:
        parts = line.split("\t")
        if len(parts) < 2:
            continue
        status = parts[0][0]  # first char is the status
        path = parts[-1]       # last field is the path (handles renames with \t)
        added, deleted = numstat_map.get(path, (0, 0))
        files.append({
            "path": path,
            "status": status,
            "added": added,
            "deleted": deleted,
        })

    return files


def get_commit_diff(
    repo_path: str,
    commit_hash: str,
    file_path: str | None = None,
) -> str:
    """Get the unified diff for a commit, optionally filtered to a single file.

    Uses ``git show <hash> --format="" --patch [-- <path>]``.
    """
    args = ["show", commit_hash, "--format=", "--patch"]
    if file_path:
        args.extend(["--", file_path])

    output = _run_git(args, repo_path, allow_failure=True)
    return output
