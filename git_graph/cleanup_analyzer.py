"""Cleanup analyzer — identifies branches that are safe to delete."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class CleanupSuggestion:
    """A branch deletion recommendation."""
    branch_name: str
    reason: str
    is_safe: bool = True
    delete_command: str = ""


def analyze_cleanup_candidates(
    branches: list[dict],
    health_list: list[dict],
) -> list[dict]:
    """Identify branches that can be safely deleted.

    Safe conditions:
        - Merged into main + no unique commits
        - Merged + behind main (>0 commits behind)
        - Zombie merged status

    Returns:
        List of cleanup suggestion dicts: [{n, reason, safe, cmd}]
    """
    health_lookup: dict[str, dict] = {h.get("n", ""): h for h in health_list}

    suggestions: list[dict] = []

    for b in branches:
        name = b.get("n", "")
        k = b.get("k", "")

        # Only local branches, not main/develop
        if k != "local":
            continue
        if name in ("main", "master", "develop", "dev"):
            continue

        h = health_lookup.get(name, {})
        if not h:
            continue

        st = h.get("st", "")
        mg = h.get("mg", False)
        uc = h.get("uc", 0)
        ldd = h.get("ldd", 0)
        ds = h.get("ds", 0)
        bh = h.get("bh", 0)
        bt = h.get("bt", "other")

        reason = ""
        is_safe = False

        # Safe: merged + no unique commits
        if mg and uc == 0:
            reason = "Merged to main, no unique commits"
            is_safe = True
        # Safe: merged + behind main
        elif mg and bh > 0:
            reason = f"Merged to main, {bh} commits behind"
            is_safe = True
        # Safe: merged stale / zombie
        elif st in ("zombie_merged", "merged_stale"):
            reason = f"Merged {ldd} days ago, {ds} days inactive"
            is_safe = True
        # Warning: abandoned zombie
        elif st == "zombie_abandoned":
            reason = f"Abandoned ({ds} days inactive), behind main by {bh}"
            is_safe = False
        # Warning: long-lived feature
        elif bt == "feature" and ldd > 60 and not mg:
            reason = f"Feature {ldd} days old, not merged"
            is_safe = False

        if reason:
            suggestions.append({
                "n": name,
                "reason": reason,
                "safe": is_safe,
                "cmd": f"git branch -d {name}" if is_safe else f"git branch -D {name}",
            })

    # Sort: safe first, then unsafe
    suggestions.sort(key=lambda s: (not s["safe"], s["n"]))
    return suggestions
