"""DORA metrics computation — deployment frequency, lead time, change failure rate, MTTR.

All metrics are computed heuristically from git history since this tool does not
have access to CI/CD pipeline data.  The heuristics are reasonable approximations
for teams that use trunk-based or GitHub-flow branching.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional


@dataclass
class DORAMetrics:
    """The four key DORA metrics."""
    deployment_frequency: float = 0.0   # deploys per week
    lead_time_median_hours: float = 0.0  # median hours from first commit to merge
    lead_time_p75_hours: float = 0.0
    lead_time_p95_hours: float = 0.0
    lead_time_raw: list[float] = field(default_factory=list)
    change_failure_rate: float = 0.0     # 0.0 - 1.0
    mttr_hours: float = 0.0              # mean time to recover (hours)


def compute_deployment_frequency(
    commits: list[dict],
    commit_map: dict,
    main_branch: str = "main",
) -> float:
    """Estimate deployment frequency as merges to main per week.

    Counts merge commits on the main branch (commits with >1 parent).
    """
    merge_dates: list[datetime] = []

    for c in commits:
        ph = c.get("ph", [])
        b = c.get("b", [])
        if len(ph) > 1 and main_branch in b:
            ts = c.get("t", "")
            if ts:
                try:
                    merge_dates.append(datetime.fromisoformat(ts[:19] if len(ts) > 10 else ts[:10]))
                except (ValueError, TypeError):
                    pass

    if not merge_dates:
        return 0.0

    merge_dates.sort()
    total_weeks = max(1, (merge_dates[-1] - merge_dates[0]).days / 7)
    return round(len(merge_dates) / total_weeks, 1)


def compute_lead_time(
    commits: list[dict],
    branches: list[dict],
    commit_map: dict,
    merged_branches_set: set[str],
) -> dict:
    """Estimate lead time: time from first commit on a feature branch to its merge into main.

    Returns:
        {med, p75, p95, raw: [...]}
    """
    lead_times: list[float] = []

    # For each merged local branch, find its first and last commit
    for b in branches:
        name = b.get("n", "")
        if name not in merged_branches_set:
            continue

        # Find the commits on this branch
        branch_commits: list[dict] = []
        for c in commits:
            cb = c.get("b", [])
            if name in cb:
                branch_commits.append(c)

        if len(branch_commits) < 2:
            continue

        # Sort by timestamp
        def _ts_key(c: dict) -> str:
            return c.get("t", "")

        branch_commits.sort(key=_ts_key)

        first_ts = branch_commits[0].get("t", "")
        last_ts = branch_commits[-1].get("t", "")

        if first_ts and last_ts:
            try:
                first_dt = datetime.fromisoformat(first_ts[:19] if len(first_ts) > 10 else first_ts[:10])
                last_dt = datetime.fromisoformat(last_ts[:19] if len(last_ts) > 10 else last_ts[:10])
                hours = (last_dt - first_dt).total_seconds() / 3600
                if hours >= 0:
                    lead_times.append(round(hours, 1))
            except (ValueError, TypeError):
                pass

    if not lead_times:
        return {"med": 0, "p75": 0, "p95": 0, "raw": []}

    lead_times.sort()
    n = len(lead_times)

    return {
        "med": lead_times[n // 2],
        "p75": lead_times[int(n * 0.75)],
        "p95": lead_times[int(n * 0.95)],
        "raw": lead_times,
    }


def compute_change_failure_rate(commits: list[dict]) -> float:
    """Estimate change failure rate from revert / hotfix commits.

    Looks for commits with 'revert' or 'hotfix' in the subject.
    """
    total = len(commits)
    if total == 0:
        return 0.0

    failure_count = 0
    for c in commits:
        subject = c.get("s", "").lower()
        if "revert" in subject or "hotfix" in subject:
            failure_count += 1

    return round(failure_count / total, 3)


def compute_mttr(commits: list[dict]) -> float:
    """Estimate MTTR from time between revert and the fix commit.

    Heuristic: finds revert commits and measures time to the next commit on the same branch.
    """
    revert_indices: list[int] = []

    for i, c in enumerate(commits):
        subject = c.get("s", "").lower()
        if "revert" in subject:
            revert_indices.append(i)

    recovery_times: list[float] = []

    for idx in revert_indices:
        if idx + 1 < len(commits):
            revert_ts = commits[idx].get("t", "")
            fix_ts = commits[idx + 1].get("t", "")

            if revert_ts and fix_ts:
                try:
                    r_dt = datetime.fromisoformat(revert_ts[:19] if len(revert_ts) > 10 else revert_ts[:10])
                    f_dt = datetime.fromisoformat(fix_ts[:19] if len(fix_ts) > 10 else fix_ts[:10])
                    hours = (f_dt - r_dt).total_seconds() / 3600
                    if 0 < hours < 720:  # cap at 30 days
                        recovery_times.append(round(hours, 1))
                except (ValueError, TypeError):
                    pass

    if not recovery_times:
        return 0.0

    return round(sum(recovery_times) / len(recovery_times), 1)


def compute_all_dora(
    commits: list[dict],
    branches: list[dict],
    merged_branches_set: set[str],
) -> dict:
    """Compute all four DORA metrics.

    Returns:
        DORA dict: {df, lt: {med, p75, p95, raw}, cfr, mttr}
    """
    from .data_model import build_dag

    # Deploy frequency
    df = compute_deployment_frequency(commits, {})

    # Lead time
    lt = compute_lead_time(commits, branches, {}, merged_branches_set)

    # Change failure rate
    cfr = compute_change_failure_rate(commits)

    # MTTR
    mttr = compute_mttr(commits)

    return {
        "df": df,
        "lt": lt,
        "cfr": cfr,
        "mttr": mttr,
    }


def compute_pr_metrics(
    commits: list[dict],
    merged_branches_set: set[str],
) -> dict:
    """Compute PR-related metrics from merge commits.

    Returns:
        {avg_size, size_dist, avg_cycle_hours, merge_methods}
    """
    merge_count = 0
    squash_count = 0
    rebase_count = 0

    for c in commits:
        s = c.get("s", "")

        # Detect merge method from commit message
        if s.startswith("Merge branch '"):
            merge_count += 1
        elif s.startswith("Merge pull request #"):
            merge_count += 1
        elif s.startswith("Squash") or "(squash" in s.lower():
            squash_count += 1
        elif "(rebased" in s.lower() or "rebase" in s.lower():
            rebase_count += 1

    total = max(1, merge_count + squash_count + rebase_count)

    return {
        "avg_size": 0,  # requires diff analysis
        "size_dist": [],
        "avg_cycle_hours": 0,
        "merge_methods": {
            "merge": merge_count,
            "squash": squash_count,
            "rebase": rebase_count,
        },
    }
