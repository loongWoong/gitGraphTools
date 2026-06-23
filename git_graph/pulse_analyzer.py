"""Pulse analysis — weekly project health dashboard.

Computes activity summaries, trend detection, and risk markers for a
Linear-style Pulse overview.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta


@dataclass
class PulseData:
    """Weekly pulse metrics for the repository."""
    weekly_summary: dict = field(default_factory=dict)  # {week_key: {commits, branches, authors}}
    risk_branches: list = field(default_factory=list)    # [{n, reason, severity}]
    trends: dict = field(default_factory=dict)           # {commits_change_pct, branches_change_pct}


def compute_pulse(
    commits: list[dict],
    branches: list[dict],
    health_list: list[dict],
    issue_links: dict,
    inactive_days: int = 14,
    long_lived_days: int = 60,
    behind_warn: int = 50,
) -> dict:
    """Compute pulse metrics for the repository.

    Args:
        commits: Serialized commit dicts.
        branches: Serialized branch dicts.
        health_list: Health analysis results.
        issue_links: Issue-to-branch mapping (from issue_tracker).
        inactive_days: Threshold for inactivity risk.
        long_lived_days: Threshold for long-lived branch risk.
        behind_warn: Threshold for behind-main risk.

    Returns:
        Pulse dict: {ws, rb, tr}
    """
    now = datetime.now()

    # ── Weekly summaries (last 4 weeks) ──
    weekly: dict[str, dict] = {}
    for week_offset in range(3, -1, -1):
        week_start = now - timedelta(days=7 * (week_offset + 1))
        week_end = now - timedelta(days=7 * week_offset) if week_offset > 0 else now
        week_key = week_start.strftime("%Y-W%W")

        week_commits = 0
        week_authors: set[str] = set()
        for c in commits:
            ts = c.get("t", "")
            if ts:
                try:
                    dt = datetime.fromisoformat(ts[:19] if len(ts) > 10 else ts[:10])
                    if week_start <= dt <= week_end:
                        week_commits += 1
                        a = c.get("a", "")
                        if a:
                            week_authors.add(a)
                except (ValueError, TypeError):
                    pass

        week_branches = 0
        for b in branches:
            fd = b.get("fd", "")
            ld = b.get("ld", "")
            for date_str in [fd, ld]:
                if date_str:
                    try:
                        dt = datetime.fromisoformat(date_str[:10])
                        if week_start <= dt <= week_end:
                            week_branches += 1
                            break
                    except (ValueError, TypeError):
                        pass

        weekly[week_key] = {
            "commits": week_commits,
            "branches": week_branches,
            "authors": len(week_authors),
        }

    # ── Risk branches ──
    risks: list[dict] = []
    health_lookup = {h.get("n", ""): h for h in health_list}

    for h in health_list:
        name = h.get("n", "")
        st = h.get("st", "")
        bt = h.get("bt", "")

        if bt in ("main", "develop"):
            continue  # main branches aren't "risks"

        reasons: list[str] = []
        severity = "low"

        # Inactive
        ds = h.get("ds", 0)
        if ds > inactive_days:
            reasons.append(f"No activity for {ds} days")
            if ds > inactive_days * 2:
                severity = "high"
            else:
                severity = "medium"

        # Long-lived
        ldd = h.get("ldd", 0)
        if ldd > long_lived_days:
            reasons.append(f"Long-lived ({ldd} days)")

        # Behind main
        bh = h.get("bh", 0)
        if bh > behind_warn:
            reasons.append(f"Behind main by {bh} commits")

        # Not linked to any issue
        has_issue = False
        for key, info in issue_links.items():
            if name in info.get("b", []):
                has_issue = True
                break
        if not has_issue and bt != "other":
            reasons.append("Not linked to any issue")

        # Merged but not deleted
        if h.get("mg") and bt not in ("main", "develop"):
            reasons.append("Merged but not deleted")
            severity = "medium"

        if reasons:
            if severity == "low" and len(reasons) >= 3:
                severity = "medium"
            risks.append({
                "n": name,
                "reason": "; ".join(reasons),
                "severity": severity,
            })

    # Sort by severity
    severity_order = {"high": 0, "medium": 1, "low": 2}
    risks.sort(key=lambda r: severity_order.get(r["severity"], 99))

    # ── Trends (compare current week vs previous week) ──
    week_keys = sorted(weekly.keys())
    trends = {"commits_change_pct": 0, "branches_change_pct": 0}
    if len(week_keys) >= 2:
        curr_commits = weekly[week_keys[-1]]["commits"]
        prev_commits = weekly[week_keys[-2]]["commits"]
        if prev_commits > 0:
            trends["commits_change_pct"] = round(
                (curr_commits - prev_commits) / prev_commits * 100, 1,
            )

        curr_branches = weekly[week_keys[-1]]["branches"]
        prev_branches = weekly[week_keys[-2]]["branches"]
        if prev_branches > 0:
            trends["branches_change_pct"] = round(
                (curr_branches - prev_branches) / prev_branches * 100, 1,
            )

    return {
        "ws": weekly,
        "rb": risks,
        "tr": trends,
    }
