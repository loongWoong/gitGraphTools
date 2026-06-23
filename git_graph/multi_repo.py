"""Multi-repository comparison — analyze multiple repos side-by-side."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class RepoSnapshot:
    """High-level metrics for a single repository."""
    path: str
    name: str = ""
    total_commits: int = 0
    total_branches: int = 0
    health_score: int = 0
    active_authors: int = 0
    most_active_month: str = ""
    dora: dict = field(default_factory=dict)


def compare_repos(
    repo_paths: list[str],
    results: list[dict],
) -> list[dict]:
    """Generate comparison snapshots for multiple repos.

    Args:
        repo_paths: List of repo paths.
        results: List of analysis result dicts, one per repo.
            Each should have: metadata, health_score, author_stats, dora.

    Returns:
        List of comparison dicts: [{p, n, tc, tb, hs, aa, dr}]
    """
    import os

    snapshots: list[dict] = []

    for i, (path, data) in enumerate(zip(repo_paths, results)):
        metadata = data.get("metadata", {})
        author_stats = data.get("author_stats", [])
        activity = data.get("activity_stats", {})
        dora = data.get("dora", {})

        name = os.path.basename(path) or path
        if not name:
            name = f"repo-{i + 1}"

        snapshots.append({
            "p": path,
            "n": name,
            "tc": metadata.get("total_commits", 0),
            "tb": metadata.get("total_branches", 0),
            "hs": data.get("repo_health_score", 0),
            "aa": len(author_stats),
            "ma": activity.get("most_active_month", {}).get("period", ""),
            "dr": dora,
        })

    return snapshots
