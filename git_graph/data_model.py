"""Data models for git graph visualization. Zero external dependencies."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Commit:
    """A single git commit node in the DAG."""

    hash: str                     # Full 40-char SHA
    short_hash: str               # 7-char abbreviation
    parent_hashes: list[str]      # Full parent SHAs (empty for root/orphan)
    children: list[str] = field(default_factory=list)  # Populated during DAG build
    timestamp: str = ""           # ISO 8601
    author: str = ""              # Author name
    subject: str = ""             # Commit subject line (first line)
    full_message: str = ""        # Full commit message (for detail panel)
    # Layout fields (populated by layout_engine)
    row: int = 0                  # Vertical position (0 = oldest)
    lane: int = 0                 # Horizontal lane/column
    # Annotation fields
    branches: list[str] = field(default_factory=list)   # Branch names passing through
    refs: list[str] = field(default_factory=list)       # Tags at this commit
    is_head: bool = False         # HEAD points here
    is_detached: bool = False     # HEAD is detached at this commit
    head_label: str = ""          # "HEAD" or "HEAD (detached)"


@dataclass
class BranchInfo:
    """Metadata about a git branch, remote ref, or tag."""

    name: str                     # Short name (e.g. "main", "origin/main", "v1.0")
    kind: str                     # "local", "remote", "tag"
    tip_hash: str                 # Full commit hash at tip
    is_head: bool = False         # HEAD points to this branch


@dataclass
class Edge:
    """A visual edge (line) connecting two commits in the graph."""

    from_commit: str              # Child commit short hash
    to_commit: str                # Parent commit short hash
    from_lane: int                # Source lane
    to_lane: int                  # Target lane
    kind: str                     # "linear" (same lane), "fork" (different lanes, child forks), "merge" (child merges from parents)


@dataclass
class GraphData:
    """Complete graph data, serializable to JSON for the HTML frontend."""

    commits: list[dict] = field(default_factory=list)
    edges: list[dict] = field(default_factory=list)
    branches: list[dict] = field(default_factory=list)
    head: dict = field(default_factory=dict)
    metadata: dict = field(default_factory=dict)

    # ── Intelligence data (populated by analyzers) ─────────────
    health: list[dict] = field(default_factory=list)
    heatmap: list[dict] = field(default_factory=list)
    author_stats: list[dict] = field(default_factory=list)
    bus_factor_warnings: list[dict] = field(default_factory=list)
    branch_lifetimes: list[dict] = field(default_factory=list)
    date_markers: list[dict] = field(default_factory=list)
    activity_stats: dict = field(default_factory=dict)
    repo_health_score: int = 0
    status_counts: dict = field(default_factory=dict)
    timeline: dict = field(default_factory=dict)    # fork/merge relationship data

    # ── Phase 1-4: New intelligence data ────────────────
    issue_links: dict = field(default_factory=dict)     # issue key → branch mapping
    sprints: list[dict] = field(default_factory=list)    # sprint analysis data
    burndown: dict = field(default_factory=dict)         # burndown chart data
    pulse: dict = field(default_factory=dict)            # pulse metrics
    dora: dict = field(default_factory=dict)             # DORA metrics
    pr_metrics: dict = field(default_factory=dict)       # PR analysis data
    churn: dict = field(default_factory=dict)            # code churn heatmap
    conflict_risks: list[dict] = field(default_factory=list)  # merge conflict predictions
    branch_summaries: dict = field(default_factory=dict)      # branch summary texts
    release_notes: str = ""                                   # auto-generated release notes
    dependency_graph: dict = field(default_factory=dict)      # branch dependency tree
    cleanup_suggestions: list[dict] = field(default_factory=list)  # safe delete suggestions
    multi_repo: list[dict] = field(default_factory=list)     # multi-repo comparison


# ── Parsing Functions ────────────────────────────────────────────────


def parse_commits(raw_lines: list[str]) -> list[Commit]:
    """Parse raw git log output lines into Commit objects.

    Input format: <full_hash>|<parent_hashes>|<iso_date>|<author>|<subject>

    parent_hashes is space-separated (empty string for root commits).
    """
    commits: list[Commit] = []

    for line in raw_lines:
        parts = line.split("|", 4)
        if len(parts) < 5:
            continue

        full_hash = parts[0].strip()
        parent_str = parts[1].strip()
        timestamp = parts[2].strip()
        author = parts[3].strip()
        subject = parts[4].strip()

        parent_hashes = [p for p in parent_str.split() if p] if parent_str else []

        commits.append(Commit(
            hash=full_hash,
            short_hash=full_hash[:7],
            parent_hashes=parent_hashes,
            timestamp=timestamp,
            author=author,
            subject=subject,
        ))

    return commits


def parse_refs(raw_lines: list[str]) -> list[BranchInfo]:
    """Parse raw git for-each-ref output lines into BranchInfo objects.

    Input format: <refname_short>|<objectname>|<full_refname>|<objecttype>
    """
    branches: list[BranchInfo] = []

    for line in raw_lines:
        parts = line.split("|", 3)
        if len(parts) < 4:
            continue

        short_name = parts[0].strip()
        object_hash = parts[1].strip()
        full_ref = parts[2].strip()
        obj_type = parts[3].strip()

        # Determine kind
        if full_ref.startswith("refs/heads/"):
            kind = "local"
        elif full_ref.startswith("refs/remotes/"):
            kind = "remote"
        elif full_ref.startswith("refs/tags/"):
            kind = "tag"
        else:
            kind = "other"

        branches.append(BranchInfo(
            name=short_name,
            kind=kind,
            tip_hash=object_hash,
        ))

    return branches


def build_dag(commits: list[Commit]) -> dict[str, Commit]:
    """Build a lookup dict and populate children references.

    Returns:
        Dict mapping full commit hash → Commit object.
        The Commit objects' children lists are populated in-place.
    """
    commit_map: dict[str, Commit] = {}

    for commit in commits:
        commit_map[commit.hash] = commit

    # Populate children based on parent references
    for commit in commits:
        for parent_hash in commit.parent_hashes:
            if parent_hash in commit_map:
                commit_map[parent_hash].children.append(commit.hash)

    return commit_map


def assign_branch_labels(
    commits: list[Commit],
    commit_map: dict[str, Commit],
    branches: list[BranchInfo],
) -> None:
    """Walk parent chains from each branch tip and mark commits with branch names.

    A commit can belong to multiple branches (shared ancestry, merge points).
    Modifies Commit.branches in-place.
    """
    # For each branch tip, walk the first-parent chain
    for branch in branches:
        current = branch.tip_hash
        while current in commit_map:
            commit = commit_map[current]
            if branch.name not in commit.branches:
                commit.branches.append(branch.name)
            # Follow first parent to continue the chain
            if commit.parent_hashes:
                current = commit.parent_hashes[0]
            else:
                break

    # Also walk non-first-parent chains to catch merged-in branch commits
    # For merge commits, the non-first parents represent merged branches
    for commit in commits:
        if len(commit.parent_hashes) > 1:
            # Non-first parents: walk them to mark merged-in branch commits
            for parent_hash in commit.parent_hashes[1:]:
                _walk_chain(parent_hash, commit_map, set())


def _walk_chain(
    start_hash: str,
    commit_map: dict[str, Commit],
    visited: set[str],
    depth: int = 0,
    max_depth: int = 1000,
) -> None:
    """Walk a parent chain, marking commits with branches from their descendants."""
    if start_hash not in commit_map or start_hash in visited or depth > max_depth:
        return

    visited.add(start_hash)
    commit = commit_map[start_hash]

    # If downstream commits have branch labels, propagate upstream
    for child_hash in commit.children:
        if child_hash in commit_map:
            child = commit_map[child_hash]
            for branch_name in child.branches:
                if branch_name not in commit.branches:
                    commit.branches.append(branch_name)

    # Continue walking up
    for parent_hash in commit.parent_hashes:
        _walk_chain(parent_hash, commit_map, visited, depth + 1, max_depth)


def mark_refs(commits: list[Commit], commit_map: dict[str, Commit], branches: list[BranchInfo]) -> None:
    """Mark commits with tag refs."""
    for branch in branches:
        if branch.kind == "tag" and branch.tip_hash in commit_map:
            commit = commit_map[branch.tip_hash]
            commit.refs.append(branch.name)
