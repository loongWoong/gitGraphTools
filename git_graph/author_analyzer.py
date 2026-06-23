"""Author-level analysis: contribution stats and bus factor detection."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class AuthorStats:
    """Per-author contribution summary."""

    name: str
    commit_count: int = 0
    first_commit_date: str = ""
    last_commit_date: str = ""
    files_touched: int = 0
    percentage: float = 0.0   # of total commits


@dataclass
class BusFactorWarning:
    """A file or directory where one author dominates."""

    file_path: str
    dominant_author: str
    dominant_pct: float       # e.g. 94.0
    total_authors: int
    bus_factor: int           # always 1 if dominant_pct > 80%


# ── Author Stats ──────────────────────────────────────────────────────


def compute_author_stats(
    commits: list[dict],
    total_commits: int,
) -> list[dict]:
    """Compute per-author contribution statistics.

    Args:
        commits: List of commit dicts (serialized) with 'a' (author) and 't' (timestamp).
        total_commits: Total number of commits.

    Returns:
        List of author stat dicts sorted by commit count descending.
    """
    author_data: dict[str, dict] = defaultdict(lambda: {
        "name": "",
        "commits": 0,
        "first_date": "",
        "last_date": "",
    })

    for c in commits:
        author = c.get("a", "Unknown")
        ts = c.get("t", "")

        ad = author_data[author]
        ad["name"] = author
        ad["commits"] += 1

        if ts:
            if not ad["first_date"] or ts < ad["first_date"]:
                ad["first_date"] = ts
            if not ad["last_date"] or ts > ad["last_date"]:
                ad["last_date"] = ts

    results = []
    for name, data in author_data.items():
        results.append({
            "n": name,
            "cc": data["commits"],
            "fd": data["first_date"],
            "ld": data["last_date"],
            "pc": round(data["commits"] / total_commits * 100, 1) if total_commits else 0,
        })

    results.sort(key=lambda x: -x["cc"])
    return results


# ── Bus Factor Computation ────────────────────────────────────────────


def compute_bus_factor(
    file_author_data: dict[str, dict[str, int]],
    total_commits: int,
    top_n: int = 10,
    threshold_pct: float = 80.0,
    min_commits: int = 5,
) -> list[dict]:
    """Compute bus factor warnings from file-level author statistics.

    Args:
        file_author_data: {file_path: {author_name: commit_count}}
                          Produced from `git log --all --format='' --name-only`
                          or equivalent.
        total_commits: Total commit count (for relative threshold).
        top_n: Max number of warnings to return.

    Returns:
        List of bus factor warning dicts, highest-risk first.
    """
    warnings: list[dict] = []

    for file_path, author_counts in file_author_data.items():
        total_file = sum(author_counts.values())
        if total_file < min_commits:
            continue  # skip files with too few commits for meaningful analysis

        authors = sorted(author_counts.items(), key=lambda x: -x[1])
        dominant = authors[0]

        pct = round(dominant[1] / total_file * 100, 1)

        if pct >= threshold_pct and len(authors) >= 1:
            warnings.append({
                "fp": file_path,
                "da": dominant[0],          # dominant author
                "dp": pct,                   # dominant percentage
                "ta": len(authors),          # total authors
                "bf": 1,                     # bus factor
            })

    # Sort by risk (higher % = more risky)
    warnings.sort(key=lambda w: (-w["dp"], -w["ta"]))
    return warnings[:top_n]
