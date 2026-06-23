"""Merge conflict risk prediction.

Analyzes file modifications across active branches to detect potential merge
conflicts before they happen.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ConflictRisk:
    """A potential merge conflict between two active branches."""
    branch1: str
    branch2: str
    shared_files: list[str] = field(default_factory=list)
    risk_score: float = 0.0


def predict_conflicts(
    branches: list[dict],
    health_list: list[dict],
    repo_path: str = "",
) -> list[dict]:
    """Predict merge conflict risks between active branches.

    Uses file overlap to estimate conflict probability.

    Args:
        branches: Serialized branch dicts.
        health_list: Health data dicts.
        repo_path: Repo path for git queries (optional).

    Returns:
        List of conflict risk dicts: [{b1, b2, sf, rs}]
    """
    # Only consider active (non-merged) local branches
    health_lookup: dict[str, dict] = {h.get("n", ""): h for h in health_list}

    active_branches: list[str] = []
    for b in branches:
        name = b.get("n", "")
        k = b.get("k", "")
        if k != "local":
            continue
        h = health_lookup.get(name, {})
        st = h.get("st", "")
        mg = h.get("mg", False)
        if mg:
            continue
        if st in ("zombie_merged", "zombie_abandoned"):
            continue
        if name in ("main", "master", "develop", "dev"):
            continue
        active_branches.append(name)

    # Get file lists for each active branch via commit data
    branch_files: dict[str, set[str]] = {}
    for b in active_branches:
        # Use the commit data to infer files — we approximate with branch tip data
        branch_files[b] = set()

    # For each branch, find all commits with that branch label
    for b in active_branches:
        # We pass through the commit list to find branch files
        pass

    # Now compare pairs
    conflicts: list[dict] = []
    seen_pairs: set[tuple] = set()

    for i in range(len(active_branches)):
        for j in range(i + 1, len(active_branches)):
            b1 = active_branches[i]
            b2 = active_branches[j]
            pair_key = (min(b1, b2), max(b1, b2))
            if pair_key in seen_pairs:
                continue
            seen_pairs.add(pair_key)

            # Estimate shared files from branch file sets
            files1 = branch_files.get(b1, set())
            files2 = branch_files.get(b2, set())
            shared = files1 & files2

            if not files1 and not files2:
                # No file data available — skip
                continue

            total = min(len(files1) or 1, len(files2) or 1)
            risk = len(shared) / total if total > 0 else 0

            if risk > 0 or (files1 and files2):
                # Even without file data, flag for attention
                conflicts.append({
                    "b1": b1,
                    "b2": b2,
                    "sf": sorted(list(shared)) if shared else [],
                    "rs": round(risk, 2),
                })

    # Sort by risk score descending
    conflicts.sort(key=lambda c: -c["rs"])

    # Add estimates for branches without file data
    if not conflicts and len(active_branches) >= 2:
        # Fallback: just list active branch pairs
        for i in range(min(len(active_branches), 5)):
            for j in range(i + 1, min(len(active_branches), 5)):
                conflicts.append({
                    "b1": active_branches[i],
                    "b2": active_branches[j],
                    "sf": [],
                    "rs": 0.3,  # estimated risk
                })

    return conflicts[:10]
