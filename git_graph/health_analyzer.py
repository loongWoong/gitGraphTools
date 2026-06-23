"""Branch health scoring and zombie detection.

Computes health scores using role-aware weighting (main/release/feature/hotfix
have different expectations) and classifies branches into health tiers.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

from .data_model import Commit, BranchInfo


# ── I18n Warning Messages ──────────────────────────────────────────


WARNING_MESSAGES = {
    "en": {
        "no_update": "{days} days without update",
        "behind_main": "{count} commits behind main",
        "merged_not_deleted": "Merged but not deleted",
        "no_unique_commits": "No unique commits (identical to main)",
        "long_lived": "Branch alive for {days} days (recommend <{limit} days)",
    },
    "zh": {
        "no_update": "{days}天未更新",
        "behind_main": "已被main超前{count}个commits",
        "merged_not_deleted": "已合并但未删除",
        "no_unique_commits": "无独立提交（与main完全一致）",
        "long_lived": "分支存活{days}天（建议<{limit}天）",
    },
}


# Current language setting (set by main() via --lang)
_current_lang = "en"


def set_language(lang: str) -> None:
    """Set the language for warning messages.  ``lang`` must be 'en' or 'zh'."""
    global _current_lang
    if lang in WARNING_MESSAGES:
        _current_lang = lang


def _w(key: str, **kwargs) -> str:
    """Get a warning message in the current language."""
    msg = WARNING_MESSAGES.get(_current_lang, WARNING_MESSAGES["en"]).get(key, key)
    if kwargs:
        msg = msg.format(**kwargs)
    return msg


# ── Branch Type Detection ────────────────────────────────────────────


def detect_branch_type(branch_name: str) -> str:
    """Classify a branch by naming convention.

    Returns one of: main, develop, release, hotfix, feature, other
    """
    name = branch_name.lower()

    if name in ("main", "master"):
        return "main"
    if name in ("develop", "dev", "development"):
        return "develop"
    if name.startswith(("release/", "release-")):
        return "release"
    if name.startswith(("hotfix/", "hotfix-", "fix/", "bugfix/")):
        return "hotfix"
    if name.startswith(("feature/", "feat/", "feature-")):
        return "feature"
    return "other"


# ── Health Score Weights ─────────────────────────────────────────────

# Weights per branch type (sum to 55).  The remaining 45 points come from
# the per-dimension scoring functions which each return 0-~100 scaled to
# their weight.
WEIGHTS = {
    "main":     {"recency": 5,  "divergence": 20, "merged": 0,  "unique": 20, "lifetime": 0},
    "develop":  {"recency": 10, "divergence": 15, "merged": 0,  "unique": 20, "lifetime": 0},
    "release":  {"recency": 10, "divergence": 15, "merged": 0,  "unique": 15, "lifetime": 10},
    "hotfix":   {"recency": 20, "divergence": 5,  "merged": 25, "unique": 5,  "lifetime": 15},
    "feature":  {"recency": 25, "divergence": 15, "merged": 20, "unique": 10, "lifetime": 15},
    "other":    {"recency": 20, "divergence": 15, "merged": 15, "unique": 10, "lifetime": 15},
}

# Days threshold for "good" recency per branch type
RECENCY_GOOD_DAYS = {
    "main": 30, "develop": 30, "release": 90, "hotfix": 7, "feature": 30, "other": 30,
}


@dataclass
class BranchHealth:
    """Health analysis result for a single branch."""

    branch_name: str
    branch_type: str                # main / develop / release / hotfix / feature / other
    score: int                      # 0-100
    status: str                     # healthy | aging | zombie_merged | zombie_abandoned | merged_stale

    # Raw metrics
    first_commit_date: str = ""     # ISO date
    last_commit_date: str = ""      # ISO date
    days_since_last_commit: int = 0
    commits_behind_main: int = 0
    commit_count: int = 0
    unique_commit_count: int = 0    # commits not in main
    author_count: int = 0
    is_merged: bool = False
    lifetime_days: int = 0

    # Warnings (human-readable, Chinese)
    warnings: list[str] = field(default_factory=list)


# ── Scoring Functions ─────────────────────────────────────────────────


def _calc_recency_score(last_date_str: str, branch_type: str) -> tuple[int, int]:
    """Return (score 0-100, days_since_last_commit)."""
    if not last_date_str:
        return 0, 999

    try:
        last_dt = datetime.fromisoformat(last_date_str)
        now = datetime.now(timezone.utc)
        days = (now - last_dt).days
    except (ValueError, TypeError):
        return 0, 999

    good = RECENCY_GOOD_DAYS.get(branch_type, 30)
    if days <= good:
        return 100, days
    if days <= good * 2:
        return 70, days
    if days <= good * 4:
        return 40, days
    if days <= good * 8:
        return 15, days
    return 0, days


def _calc_divergence_score(behind: int, branch_type: str) -> int:
    """Score based on how far behind main the branch is."""
    if branch_type in ("main", "develop"):
        return 100  # doesn't apply
    if behind <= 10:
        return 100
    if behind <= 50:
        return 75
    if behind <= 150:
        return 40
    if behind <= 500:
        return 10
    return 0


def _calc_lifetime_score(lifetime_days: int, branch_type: str) -> int:
    """Score based on how long the branch has existed."""
    limits = {"hotfix": 7, "feature": 60, "release": 180, "other": 90}
    limit = limits.get(branch_type, 90)

    if lifetime_days <= limit:
        return 100
    if lifetime_days <= limit * 2:
        return 60
    if lifetime_days <= limit * 4:
        return 25
    return 0


def compute_health(
    branch: BranchInfo,
    commits: list[Commit],
    commit_map: dict[str, Commit],
    main_tip_hash: str,
    merged_set: set[str],
    branch_commits_map: dict[str, list[str]],
) -> BranchHealth:
    """Compute health score and status for a single branch.

    Args:
        branch: The branch to analyze.
        commits: All commits (for author counting).
        commit_map: Hash → Commit lookup.
        main_tip_hash: The default branch's tip commit hash.
        merged_set: Set of branch names that are merged to the default branch.
        branch_commits_map: branch_name → list of commit hashes on that branch.

    Returns:
        BranchHealth with score, status, and warnings.
    """
    branch_type = detect_branch_type(branch.name)
    weights = WEIGHTS.get(branch_type, WEIGHTS["other"])
    warnings: list[str] = []

    # Collect commits on this branch
    branch_hashes = branch_commits_map.get(branch.name, [])
    branch_commits = [commit_map[h] for h in branch_hashes if h in commit_map]

    commit_count = len(branch_commits)

    # First / last commit dates
    first_date = ""
    last_date = ""
    if branch_commits:
        dates = sorted(c.timestamp for c in branch_commits if c.timestamp)
        if dates:
            first_date = dates[0]
            last_date = dates[-1]

    # Unique commits (not reachable from main)
    main_ancestors: set[str] = set()
    if main_tip_hash and main_tip_hash in commit_map:
        # Walk first-parent chain of main to collect ancestors
        visited: set[str] = set()
        stack = [main_tip_hash]
        while stack:
            h = stack.pop()
            if h in visited or h not in commit_map:
                continue
            visited.add(h)
            main_ancestors.add(h)
            for p in commit_map[h].parent_hashes:
                if p not in visited:
                    stack.append(p)

    unique_hashes = [h for h in branch_hashes if h not in main_ancestors]
    unique_count = len(unique_hashes)

    # Author count
    authors: set[str] = set()
    for c in branch_commits:
        if c.author:
            authors.add(c.author)
    author_count = len(authors)

    # Is merged?
    is_merged = branch.name in merged_set

    # Days since last commit
    recency_score, days_since = _calc_recency_score(last_date, branch_type)

    # Commits behind main
    behind = 0
    if branch_type != "main" and main_tip_hash and branch.tip_hash:
        behind = _count_behind(branch.tip_hash, main_tip_hash, commit_map)

    behind_score = _calc_divergence_score(behind, branch_type)

    # Lifetime
    lifetime_days = 0
    if first_date and last_date:
        try:
            first_dt = datetime.fromisoformat(first_date)
            last_dt = datetime.fromisoformat(last_date)
            lifetime_days = (last_dt - first_dt).days
        except (ValueError, TypeError):
            pass
    lifetime_score = _calc_lifetime_score(lifetime_days, branch_type)

    # Merged score
    merged_score = 100 if is_merged else 0

    # Unique commits score
    if branch_type in ("main", "develop"):
        unique_score = 100
    elif unique_count >= 1:
        unique_score = 80
    else:
        unique_score = 0  # no unique commits = already fully in main

    # Weighted total
    total = 0
    total += recency_score * weights["recency"] / 100
    total += behind_score * weights["divergence"] / 100
    total += merged_score * weights["merged"] / 100
    total += unique_score * weights["unique"] / 100
    total += lifetime_score * weights["lifetime"] / 100

    # Scale to 0-100
    max_possible = sum(weights.values())
    score = min(100, max(0, round(total / max_possible * 100)))

    # Build warnings
    if days_since > 90:
        warnings.append(_w("no_update", days=days_since))
    if behind > 100:
        warnings.append(_w("behind_main", count=str(behind)))
    if is_merged and branch_type != "main":
        warnings.append(_w("merged_not_deleted"))
    if unique_count == 0 and branch_type not in ("main", "develop"):
        warnings.append(_w("no_unique_commits"))
    if lifetime_days > 120 and branch_type in ("feature", "hotfix"):
        warnings.append(_w("long_lived", days=str(lifetime_days), limit="60"))

    # Determine status
    if branch_type in ("main", "develop"):
        status = "healthy"
    elif is_merged and days_since > 60:
        status = "zombie_merged"
    elif not is_merged and days_since > 90 and behind > 50:
        status = "zombie_abandoned"
    elif score >= 70:
        status = "healthy"
    elif score >= 40:
        status = "aging"
    elif is_merged:
        status = "merged_stale"
    else:
        status = "aging"

    return BranchHealth(
        branch_name=branch.name,
        branch_type=branch_type,
        score=score,
        status=status,
        first_commit_date=first_date,
        last_commit_date=last_date,
        days_since_last_commit=days_since,
        commits_behind_main=behind,
        commit_count=commit_count,
        unique_commit_count=unique_count,
        author_count=author_count,
        is_merged=is_merged,
        lifetime_days=lifetime_days,
        warnings=warnings,
    )


def _count_behind(
    branch_tip: str,
    main_tip: str,
    commit_map: dict[str, Commit],
) -> int:
    """Count how many commits the branch tip is behind main tip.

    Walks from main_tip backward; counts steps until we reach branch_tip
    or run out of history.  This is a heuristic — a proper merge-base
    would be more accurate but slower.
    """
    if branch_tip == main_tip:
        return 0
    if branch_tip not in commit_map or main_tip not in commit_map:
        return 0

    # Walk main's first-parent chain
    count = 0
    current = main_tip
    visited: set[str] = set()
    while current and current in commit_map and current not in visited:
        visited.add(current)
        if current == branch_tip:
            return count
        count += 1
        c = commit_map[current]
        if c.parent_hashes:
            current = c.parent_hashes[0]
        else:
            break
    return count


def compute_all_health(
    branches: list[BranchInfo],
    commits: list[Commit],
    commit_map: dict[str, Commit],
    merged_set: set[str],
    branch_commits_map: dict[str, list[str]],
) -> list[BranchHealth]:
    """Compute health scores for all branches.

    Also computes a composite repository health score (average, weighted by
    branch type importance).
    """
    # Find main branch tip
    main_tip = ""
    for b in branches:
        if detect_branch_type(b.name) == "main":
            main_tip = b.tip_hash
            break

    results: list[BranchHealth] = []
    for branch in branches:
        h = compute_health(
            branch, commits, commit_map, main_tip, merged_set, branch_commits_map,
        )
        results.append(h)

    # Sort: healthy first, then aging, then zombies
    status_order = {
        "healthy": 0, "aging": 1, "merged_stale": 2,
        "zombie_merged": 3, "zombie_abandoned": 4,
    }
    results.sort(key=lambda h: (status_order.get(h.status, 99), -h.score))

    return results


def compute_repo_health(health_results: list[BranchHealth]) -> int:
    """Compute an overall repository health score (0-100).

    Main branches weighted more heavily than feature branches.
    """
    if not health_results:
        return 0

    type_weights = {
        "main": 5, "develop": 4, "release": 3, "hotfix": 2, "feature": 1, "other": 1,
    }
    total_weight = 0
    weighted_sum = 0

    for h in health_results:
        w = type_weights.get(h.branch_type, 1)
        weighted_sum += h.score * w
        total_weight += w

    return round(weighted_sum / total_weight) if total_weight else 0


def count_by_status(health_results: list[BranchHealth]) -> dict[str, int]:
    """Count branches per status category."""
    counts: dict[str, int] = {}
    for h in health_results:
        counts[h.status] = counts.get(h.status, 0) + 1
    return counts
