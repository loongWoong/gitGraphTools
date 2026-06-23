"""Temporal analysis: commit heatmap and branch lifetime spans."""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from typing import Optional

from .data_model import Commit, BranchInfo


# ── Heatmap Data ──────────────────────────────────────────────────────


def compute_heatmap(
    commits: list[Commit],
    bucket: str = "week",
) -> list[dict]:
    """Aggregate commits into time buckets for a GitHub-style heatmap.

    Args:
        commits: All commits with timestamps.
        bucket: "week" or "month".

    Returns:
        List of {period: "2026-W01", count: N, authors: M} dicts,
        sorted chronologically.
    """
    if not commits:
        return []

    buckets: dict[str, dict[str, int]] = defaultdict(lambda: {"commits": 0, "authors": set()})

    for c in commits:
        if not c.timestamp:
            continue
        try:
            dt = datetime.fromisoformat(c.timestamp)
        except (ValueError, TypeError):
            continue

        if bucket == "month":
            key = dt.strftime("%Y-%m")
        else:
            # ISO week
            key = dt.strftime("%Y-W%W")

        buckets[key]["commits"] += 1
        if c.author:
            buckets[key]["authors"].add(c.author)

    result = []
    for key in sorted(buckets.keys()):
        data = buckets[key]
        result.append({
            "period": key,
            "commits": data["commits"],
            "authors": len(data["authors"]),
        })

    return result


# ── Branch Lifetime Spans ─────────────────────────────────────────────


def compute_branch_lifetimes(
    branches: list[BranchInfo],
    commits: list[Commit],
    commit_map: dict[str, Commit],
    branch_commits_map: dict[str, list[str]],
) -> list[dict]:
    """Compute start/end dates and durations for each branch.

    Returns:
        List of {
            "n": branch_name,
            "fd": first_date (ISO),
            "ld": last_date (ISO),
            "dur": duration_days,
            "cc": commit_count,
            "st": health_status,
            "mg": is_merged,
        }
    """
    results = []

    for branch in branches:
        hashes = branch_commits_map.get(branch.name, [])
        branch_commits_list = [commit_map[h] for h in hashes if h in commit_map]

        if not branch_commits_list:
            continue

        dates = sorted(
            c.timestamp for c in branch_commits_list if c.timestamp
        )

        if not dates:
            continue

        first_date = dates[0]
        last_date = dates[-1]

        duration = 0
        try:
            fd = datetime.fromisoformat(first_date)
            ld = datetime.fromisoformat(last_date)
            duration = (ld - fd).days
        except (ValueError, TypeError):
            pass

        results.append({
            "n": branch.name,
            "fd": first_date,
            "ld": last_date,
            "dur": duration,
            "cc": len(branch_commits_list),
            "st": "",   # filled in later by health data
            "mg": False,  # filled in later
        })

    # Sort by start date
    results.sort(key=lambda x: x["fd"])
    return results


# ── Date Markers for Timeline Axis ────────────────────────────────────


def compute_date_markers(
    commits: list[Commit],
) -> list[dict]:
    """Generate date axis labels at month boundaries.

    Returns:
        List of {row: int, label: "2026-01"} dicts suitable for rendering
        on the left edge of the DAG graph.
    """
    if not commits:
        return []

    markers: list[dict] = []
    last_month = ""

    for i, commit in enumerate(commits):
        if not commit.timestamp:
            continue
        try:
            dt = datetime.fromisoformat(commit.timestamp)
        except (ValueError, TypeError):
            continue

        month_key = dt.strftime("%Y-%m")
        if month_key != last_month:
            markers.append({"r": commit.row, "label": month_key})
            last_month = month_key

    # Thin out if too many markers (keep every Nth)
    if len(markers) > 24:
        step = len(markers) // 12
        markers = markers[::step]

    return markers


# ── Activity Stats ────────────────────────────────────────────────────


def compute_activity_stats(
    commits: list[Commit],
) -> dict:
    """Compute high-level activity statistics.

    Returns:
        {
            "total_commits": int,
            "total_authors": int,
            "first_commit_date": str,
            "last_commit_date": str,
            "repo_age_days": int,
            "most_active_month": {"period": str, "commits": int},
            "avg_commits_per_week": float,
        }
    """
    if not commits:
        return {}

    authors: set[str] = set()
    dates: list[datetime] = []

    for c in commits:
        if c.author:
            authors.add(c.author)
        if c.timestamp:
            try:
                dates.append(datetime.fromisoformat(c.timestamp))
            except (ValueError, TypeError):
                pass

    dates.sort()

    first_date = dates[0].isoformat() if dates else ""
    last_date = dates[-1].isoformat() if dates else ""
    repo_age = (dates[-1] - dates[0]).days if len(dates) >= 2 else 0

    # Most active month
    month_counts: dict[str, int] = defaultdict(int)
    for dt in dates:
        month_counts[dt.strftime("%Y-%m")] += 1

    most_active = max(month_counts.items(), key=lambda x: x[1]) if month_counts else ("", 0)

    # Avg commits per week
    weeks = max(1, repo_age / 7)
    avg_per_week = round(len(commits) / weeks, 1)

    return {
        "total_commits": len(commits),
        "total_authors": len(authors),
        "first_commit_date": first_date,
        "last_commit_date": last_date,
        "repo_age_days": repo_age,
        "most_active_month": {"period": most_active[0], "commits": most_active[1]},
        "avg_commits_per_week": avg_per_week,
    }


def compute_timeline_branches(
    branches: list[BranchInfo],
    commits: list[Commit],
    commit_map: dict[str, Commit],
    branch_commits_map: dict[str, list[str]],
    health_list: list[dict],
    head_branch: str | None,
) -> dict:
    """Compute timeline branch data for the fork/merge relationship view.

    Only local branches, showing start dot (fork point) and end dot (tip).
    Returns a dict with date range, sorted branch list with X positions, and
    parent/merge relationship info.
    """
    from datetime import datetime

    # 1. Filter local branches with commits
    local_branches = [b for b in branches if b.kind == "local"]
    branch_data: list[dict] = []

    # Collect date range
    all_dates: list[datetime] = []
    for c in commits:
        if c.timestamp:
            try:
                all_dates.append(datetime.fromisoformat(c.timestamp))
            except (ValueError, TypeError):
                pass
    all_dates.sort()

    if not all_dates:
        return {"date_min": "", "date_max": "", "branches": []}

    date_min = all_dates[0]
    date_max = all_dates[-1]
    total_seconds = max(1, (date_max - date_min).total_seconds())

    # Build health lookup
    health_map: dict[str, dict] = {h.get("n", ""): h for h in health_list}

    # Build first-parent chain for each local branch
    def _first_parent_chain(tip_hash: str) -> list[str]:
        """Walk the first-parent chain from tip to root, return ordered list of hashes."""
        chain: list[str] = []
        seen: set[str] = set()
        current = tip_hash
        while current and current in commit_map and current not in seen:
            seen.add(current)
            chain.append(current)
            c = commit_map[current]
            if c.parent_hashes:
                current = c.parent_hashes[0]
            else:
                break
        return chain

    branch_chains: dict[str, list[str]] = {}
    for branch in local_branches:
        branch_chains[branch.name] = _first_parent_chain(branch.tip_hash)

    # Helper: find fork point between child and parent branches
    def _find_fork(child_name: str, parent_name: str) -> tuple[str, str]:
        """Return (fork_commit_hash, parent_of_fork_hash) for child forking from parent.

        The fork commit is the first commit in child's chain not in parent's chain.
        parent_of_fork is its parent (the last common commit).
        Returns ("", "") if no fork found (child is ancestor of parent).
        """
        child_chain = branch_chains.get(child_name, [])
        parent_set = set(branch_chains.get(parent_name, []))
        if not child_chain:
            return ("", "")

        for c_hash in child_chain:
            if c_hash not in parent_set:
                # This is the first commit unique to child — it forked here
                c = commit_map.get(c_hash)
                if c and c.parent_hashes:
                    p_hash = c.parent_hashes[0]
                    if p_hash in parent_set:
                        return (c_hash, p_hash)
                return (c_hash, "")
        return ("", "")

    # 2. For each local branch, compute first/last commit + parent branch
    for branch in local_branches:
        hashes = branch_commits_map.get(branch.name, [])
        if not hashes:
            continue

        branch_commits_obj = []
        for h in hashes:
            c = commit_map.get(h)
            if c and c.timestamp:
                branch_commits_obj.append(c)

        if not branch_commits_obj:
            continue

        # Sort by timestamp
        branch_commits_obj.sort(key=lambda c: c.timestamp)

        first_c = branch_commits_obj[0]
        last_c = branch_commits_obj[-1]

        # Find parent branch: the one with the longest shared chain
        parent_branch = ""
        fork_hash = ""
        max_shared = 0
        for other in local_branches:
            if other.name == branch.name:
                continue
            fh, ph = _find_fork(branch.name, other.name)
            if fh and ph:
                # Count shared commits (how far back the fork is)
                other_set = set(branch_chains.get(other.name, []))
                child_chain = branch_chains.get(branch.name, [])
                shared = sum(1 for h in child_chain if h in other_set)
                # Prefer main/master, then by shared count
                score = shared + (1000 if other.name in ("main", "master") else 0)
                if score > max_shared:
                    max_shared = score
                    parent_branch = other.name
                    fork_hash = fh

        # Get the fork commit (or first commit if no parent)
        start_commit = commit_map.get(fork_hash) if fork_hash else first_c

        # Compute X positions from fork commit (not first commit)
        try:
            fd = datetime.fromisoformat(start_commit.timestamp)
            ld = datetime.fromisoformat(last_c.timestamp)
            sx = max(0, (fd - date_min).total_seconds() / total_seconds)
            ex = min(1, (ld - date_min).total_seconds() / total_seconds)
        except (ValueError, TypeError):
            sx, ex = 0, 1

        h = health_map.get(branch.name, {})
        branch_data.append({
            "n": branch.name,
            "sx": round(sx, 4),
            "ex": round(ex, 4),
            "fd": start_commit.timestamp[:10] if start_commit else first_c.timestamp[:10],
            "ld": last_c.timestamp[:10],
            "st": h.get("st", "healthy"),
            "pb": parent_branch,
            "mg": h.get("mg", False),
            "mt": "main" if h.get("mg") else "",
            "sh": start_commit.short_hash if start_commit else first_c.short_hash,
            "eh": last_c.short_hash,
        })

    # 3. Sort and assign rows
    # main first, HEAD second, then by last commit date descending
    def sort_key(d: dict) -> tuple:
        name = d["n"]
        if name in ("main", "master"):
            return (0, "")
        if name == head_branch:
            return (1, "")
        return (2, d.get("ld", ""))

    branch_data.sort(key=sort_key)

    for i, bd in enumerate(branch_data):
        bd["row"] = i

    return {
        "date_min": date_min.strftime("%Y-%m-%d"),
        "date_max": date_max.strftime("%Y-%m-%d"),
        "branches": branch_data,
    }
