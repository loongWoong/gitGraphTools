"""Sprint / iteration analysis — groups branches into time-boxed sprints.

Computes sprint-level metrics including burndown charts and scope change detection.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional


@dataclass
class SprintInfo:
    """Analytics for a single sprint / iteration."""
    name: str
    start: str          # ISO date
    end: str            # ISO date
    planned_branches: int = 0
    completed_branches: int = 0
    commits: int = 0
    scope_change: int = 0   # branches added mid-sprint


def compute_sprints(
    branches: list[dict],
    commits: list[dict],
    sprint_days: int = 14,
) -> list[dict]:
    """Group branches and commits into sprint buckets.

    Args:
        branches: Serialized branch dicts with 'fd' (first_date) and 'ld' (last_date).
        commits: Serialized commit dicts with 't' (timestamp).
        sprint_days: Length of each sprint in days.

    Returns:
        List of sprint dicts: {n, st, ed, pb, cb, cc, sc}
    """
    if not branches:
        return []

    # Collect all dates to determine sprint range
    all_dates: list[datetime] = []
    for b in branches:
        fd = b.get("fd", "")
        if fd:
            try:
                all_dates.append(datetime.fromisoformat(fd[:10]))
            except (ValueError, TypeError):
                pass

    if not all_dates:
        return []

    date_min = min(all_dates)
    date_max = max(all_dates)

    # Generate sprints
    sprints: list[dict] = []
    current_start = date_min.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    sprint_idx = 0
    while current_start <= date_max + timedelta(days=sprint_days):
        current_end = current_start + timedelta(days=sprint_days - 1)

        # Count branches that were active during this sprint
        planned = 0
        completed = 0
        scope_changes = 0

        for b in branches:
            fd = b.get("fd", "")
            ld = b.get("ld", "")
            st = b.get("st", "")
            mg = b.get("mg", False)

            if not fd:
                continue

            try:
                fd_dt = datetime.fromisoformat(fd[:10])
            except (ValueError, TypeError):
                continue

            # Branch started before or during this sprint
            if fd_dt <= current_end:
                if fd_dt >= current_start:
                    planned += 1
                elif fd_dt < current_start:
                    scope_changes += 1

                # Check if completed (merged) during this sprint
                if mg and ld:
                    try:
                        ld_dt = datetime.fromisoformat(ld[:10])
                        if current_start <= ld_dt <= current_end:
                            completed += 1
                    except (ValueError, TypeError):
                        pass

        # Count commits in this sprint
        sprint_commits = 0
        for c in commits:
            ts = c.get("t", "")
            if ts:
                try:
                    commit_dt = datetime.fromisoformat(ts[:10])
                    if current_start <= commit_dt <= current_end:
                        sprint_commits += 1
                except (ValueError, TypeError):
                    pass

        sprints.append({
            "n": f"Sprint {sprint_idx + 1}",
            "st": current_start.strftime("%Y-%m-%d"),
            "ed": current_end.strftime("%Y-%m-%d"),
            "pb": planned,
            "cb": completed,
            "cc": sprint_commits,
            "sc": scope_changes,
        })

        current_start = current_end + timedelta(days=1)
        sprint_idx += 1

    # Filter empty sprints at the end
    while sprints and sprints[-1]["cc"] == 0 and sprints[-1]["pb"] == 0:
        sprints.pop()

    return sprints


def compute_burndown(
    sprint: dict,
    branches: list[dict],
    commits: list[dict],
) -> list[dict]:
    """Compute daily burndown data for a single sprint.

    Returns:
        List of {d: date, r: remaining_branches} dicts.
    """
    try:
        start = datetime.fromisoformat(sprint["st"])
        end = datetime.fromisoformat(sprint["ed"])
    except (ValueError, TypeError):
        return []

    # Total active branches (planned + scope change) as of sprint start
    active_before = 0
    for b in branches:
        fd = b.get("fd", "")
        if fd:
            try:
                fd_dt = datetime.fromisoformat(fd[:10])
                if fd_dt <= end:
                    active_before += 1
            except (ValueError, TypeError):
                pass

    # Compute daily completion
    days_in_range = (end - start).days + 1
    if days_in_range <= 0:
        return []

    result: list[dict] = []
    remaining = active_before
    current_day = start

    for _ in range(min(days_in_range, 60)):  # max 60 days
        # Count branches merged on this day
        merged_today = 0
        for b in branches:
            mg = b.get("mg", False)
            ld = b.get("ld", "")
            if mg and ld:
                try:
                    ld_dt = datetime.fromisoformat(ld[:10])
                    if ld_dt.date() == current_day.date():
                        merged_today += 1
                except (ValueError, TypeError):
                    pass

        remaining = max(0, remaining - merged_today)
        result.append({
            "d": current_day.strftime("%Y-%m-%d"),
            "r": remaining,
        })

        current_day += timedelta(days=1)

    return result
