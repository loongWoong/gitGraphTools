"""DAG graph layout engine — lane assignment and coordinate computation.

The core algorithm assigns each commit to a vertical row (chronological within
topological constraints) and a horizontal lane (column).  The lane assignment is
a greedy pass similar to `git log --graph` / gitk:

1.  Allocate a lane when a new branch tip is encountered.
2.  Keep the lane occupied while traversing its ancestor chain.
3.  Free the lane when the branch ends (reaches first-parent's ancestor that is
    also on another tracked branch, i.e. the merge-base-ish terminus).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from .data_model import (
    Commit,
    BranchInfo,
    Edge,
    GraphData,
    build_dag,
    assign_branch_labels,
    mark_refs,
)


# ── Layout Constants ─────────────────────────────────────────────────

LANE_WIDTH = 24      # pixels between lane centres
MARGIN_LEFT = 200    # left margin (room for branch labels)
ROW_HEIGHT = 32      # pixels between commit rows
MARGIN_TOP = 40      # top margin
COMMIT_RADIUS = 5    # normal commit circle radius


# ── Lane Assignment ──────────────────────────────────────────────────


@dataclass
class _LaneState:
    """Runtime tracking for the greedy lane-assignment pass."""

    active: list[Optional[str]] = field(default_factory=list)
    # active[i] = branch_name occupying lane i, or None if free
    branch_lane: dict[str, int] = field(default_factory=dict)
    # branch_name -> lane index (stable across the graph)
    next_lane: int = 0

    def allocate(self, branch_name: str) -> int:
        """Allocate a (possibly reused) lane for *branch_name*."""
        if branch_name in self.branch_lane:
            return self.branch_lane[branch_name]

        # Find first free slot
        for i, occupant in enumerate(self.active):
            if occupant is None:
                self.active[i] = branch_name
                self.branch_lane[branch_name] = i
                return i

        # No free slot — append a new lane
        lane = len(self.active)
        self.active.append(branch_name)
        self.branch_lane[branch_name] = lane
        return lane

    def free(self, branch_name: str) -> None:
        """Mark *branch_name* as no longer active."""
        lane = self.branch_lane.get(branch_name)
        if lane is not None and lane < len(self.active):
            self.active[lane] = None

    def lane_of(self, branch_name: str) -> Optional[int]:
        return self.branch_lane.get(branch_name)


def _branch_tips_map(branches: list[BranchInfo]) -> dict[str, list[str]]:
    """Build mapping: commit_hash -> [branch_names that point here]."""
    tips: dict[str, list[str]] = {}
    for b in branches:
        tips.setdefault(b.tip_hash, []).append(b.name)
    return tips


def _assign_lanes(
    commits: list[Commit],
    commit_map: dict[str, Commit],
    branches: list[BranchInfo],
) -> None:
    """Greedy lane assignment.  Modifies ``Commit.lane`` in-place.

    Strategy
    --------
    * Walk commits in topo order (oldest → newest).
    * When we hit a branch tip we allocate a lane.
    * The lane stays occupied for every commit reachable from that tip via
      first-parent chains, until the chain hits a commit whose first-parent
      has *other* branches and we decide the branch "merged in".
    * A branch is freed when we pass its tip (we're now on its ancestors that
      are covered by other branches) OR when it merges into another lane.
    """

    # ── 1. collect branch tip commits ──
    branch_tips = _branch_tips_map(branches)

    # ── 2. for each commit, which branches "live" here? ──
    # A branch "lives" from its tip all the way down its first-parent chain
    # to the root, BUT we only paint it as "active" from tip down to the point
    # where another branch's chain "takes over" (i.e. merge-base region).

    # Simple heuristic: a branch is active on commit C if C is on the
    # first-parent chain from the branch tip AND C is not "covered" by a
    # higher-priority branch.  "Higher priority" = appeared earlier in the
    # sorted branch list (main comes first, then others).

    # Build first-parent ancestor set for each branch
    branch_ancestors: dict[str, set[str]] = {}
    for branch in branches:
        ancestors: set[str] = set()
        h = branch.tip_hash
        while h in commit_map:
            ancestors.add(h)
            c = commit_map[h]
            if c.parent_hashes:
                h = c.parent_hashes[0]   # follow first-parent only
            else:
                break
        branch_ancestors[branch.name] = ancestors

    # ── 3. determine dominant branch per commit (the one whose lane it uses) ──
    # Priority: main/master > local branches > remotes > tags
    def _branch_priority(name: str, kind: str) -> int:
        n = name.lower()
        if n in ("main", "master"):
            return 0
        if kind == "local":
            return 1
        if kind == "remote":
            return 2
        return 3  # tags

    sorted_branches = sorted(branches, key=lambda b: _branch_priority(b.name, b.kind))

    # For each commit, pick the highest-priority branch that covers it
    commit_dominant: dict[str, str] = {}
    for branch in sorted_branches:
        for h in branch_ancestors.get(branch.name, set()):
            if h not in commit_dominant:
                commit_dominant[h] = branch.name

    # ── 4. lane assignment pass ──
    state = _LaneState()

    # Pre-assign lanes for all branches in priority order
    for branch in sorted_branches:
        state.allocate(branch.name)

    for commit in commits:
        dominant = commit_dominant.get(commit.hash)
        if dominant is not None:
            lane = state.lane_of(dominant)
            if lane is not None:
                commit.lane = lane


def _topological_sort(commits: list[Commit]) -> None:
    """Assigns ``Commit.row`` in topo order (oldest = 0).

    The caller must provide commits already in ``--topo-order --reverse`` from
    git — we just enumerate them.
    """
    for i, commit in enumerate(commits):
        commit.row = i


def _build_edges(commits: list[Commit], commit_map: dict[str, Commit]) -> list[Edge]:
    """Generate visual edges between commits and their parents."""
    edges: list[Edge] = []

    for commit in commits:
        cl = commit.lane
        for parent_hash in commit.parent_hashes:
            parent = commit_map.get(parent_hash)
            if parent is None:
                continue
            pl = parent.lane

            # Determine edge kind
            if cl == pl:
                kind = "linear"
            elif len(commit.parent_hashes) > 1 and parent_hash != commit.parent_hashes[0]:
                kind = "merge"
            else:
                kind = "fork"

            edges.append(Edge(
                from_commit=commit.short_hash,
                to_commit=parent.short_hash,
                from_lane=cl,
                to_lane=pl,
                kind=kind,
            ))

    return edges


# ── Public API ───────────────────────────────────────────────────────


def layout(
    repo_path: str,
    commits: list[Commit],
    branches: list[BranchInfo],
    head_branch: Optional[str],
    head_hash: str,
    head_detached: bool,
) -> GraphData:
    """Run the full layout pipeline and return serialisable GraphData.

    Args:
        repo_path: Repository path (for metadata).
        commits: Parsed Commit objects (in --topo-order --reverse).
        branches: Parsed BranchInfo objects.
        head_branch: Branch name HEAD points to, or None if detached.
        head_hash: Full commit hash of HEAD.
        head_detached: True if HEAD is detached.

    Returns:
        GraphData ready for JSON serialisation.
    """
    # 1. Build DAG lookup
    commit_map = build_dag(commits)

    # 2. Annotate commits with branch labels
    assign_branch_labels(commits, commit_map, branches)

    # 3. Mark tag refs on commits
    mark_refs(commits, commit_map, branches)

    # 4. Mark HEAD
    head_short = head_hash[:7]
    if head_hash in commit_map:
        c = commit_map[head_hash]
        c.is_head = True
        c.is_detached = head_detached
        c.head_label = "HEAD (detached)" if head_detached else "HEAD"

    # 5. Assign rows (topo order)
    _topological_sort(commits)

    # 6. Assign lanes
    _assign_lanes(commits, commit_map, branches)

    # 7. Build edges
    edges = _build_edges(commits, commit_map)

    # 8. Serialise to compact dicts
    from datetime import datetime, timezone

    commit_dicts: list[dict] = []
    for c in commits:
        # Get short parent hashes
        short_parents = [p[:7] for p in c.parent_hashes]
        commit_dicts.append({
            "h": c.short_hash,
            "ph": short_parents,
            "r": c.row,
            "l": c.lane,
            "t": c.timestamp,
            "a": c.author,
            "s": c.subject,
            "fm": c.full_message,
            "b": c.branches,
            "dh": c.is_detached,
            "hd": c.is_head,
            "hl": c.head_label,
            "rf": c.refs,
        })

    edge_dicts: list[dict] = []
    for e in edges:
        edge_dicts.append({
            "f": e.from_commit,
            "to": e.to_commit,
            "fl": e.from_lane,
            "tl": e.to_lane,
            "k": e.kind,
        })

    branch_dicts: list[dict] = []
    for b in branches:
        branch_dicts.append({
            "n": b.name,
            "k": b.kind,
            "h": b.tip_hash[:7],
            "hd": b.is_head,
            # Find the lane for this branch
            "l": _lane_for_branch(b.name, commits, commit_map),
        })

    head_dict = {
        "h": head_short,
        "detached": head_detached,
        "branch": head_branch or "",
    }

    # Count unique lanes
    lanes = set(c.lane for c in commits)

    metadata = {
        "repo_path": repo_path,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "total_commits": len(commits),
        "total_branches": len(branches),
        "total_lanes": len(lanes),
        "total_rows": len(commits),
        "lane_width": LANE_WIDTH,
        "margin_left": MARGIN_LEFT,
        "row_height": ROW_HEIGHT,
        "margin_top": MARGIN_TOP,
        "commit_radius": COMMIT_RADIUS,
    }

    return GraphData(
        commits=commit_dicts,
        edges=edge_dicts,
        branches=branch_dicts,
        head=head_dict,
        metadata=metadata,
    )


def _lane_for_branch(
    name: str,
    commits: list[Commit],
    commit_map: dict[str, Commit],
) -> int:
    """Return the lane index used by *name* (lookup via its tip commit)."""
    # Find a commit that has this branch label
    for c in commits:
        if name in c.branches:
            return c.lane
    return 0
