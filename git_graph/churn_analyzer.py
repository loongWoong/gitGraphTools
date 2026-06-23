"""Code churn analysis — file-level change frequency and hotspot detection."""

from __future__ import annotations

from collections import defaultdict


def compute_churn_heatmap(file_changes: dict[str, int]) -> dict:
    """Aggregate file changes into directory-level heatmap data.

    Args:
        file_changes: {file_path: change_count} from git history.

    Returns:
        {dirs: [{path, count, hotspot: bool}], files: [{path, count, hotspot: bool}]}
    """
    # Aggregate by directory
    dir_counts: dict[str, int] = defaultdict(int)

    files_result: list[dict] = []
    for file_path, count in file_changes.items():
        files_result.append({
            "path": file_path,
            "count": count,
            "hotspot": False,
        })

        # Aggregate to parent directories
        parts = file_path.split("/")
        if len(parts) > 1:
            dir_key = parts[0]
            dir_counts[dir_key] += count
        else:
            dir_counts["(root)"] += count

    dirs_result: list[dict] = []
    for dir_path, count in sorted(dir_counts.items(), key=lambda x: -x[1]):
        dirs_result.append({
            "path": dir_path,
            "count": count,
            "hotspot": False,
        })

    # Mark hotspots (top 20% by change count)
    _mark_hotspots(dirs_result)
    _mark_hotspots(files_result)

    return {
        "dirs": dirs_result[:20],
        "files": files_result[:20],
    }


def _mark_hotspots(items: list[dict]) -> None:
    """Mark the top 20% of items as hotspots."""
    if not items:
        return
    threshold_idx = max(1, len(items) // 5)
    max_count = items[0]["count"]
    if max_count > 0:
        for i, item in enumerate(items):
            if i < threshold_idx or item["count"] > max_count * 0.7:
                item["hotspot"] = True


def detect_hotspots(
    file_changes: dict[str, int],
    bus_factor_warnings: list[dict],
) -> list[dict]:
    """Cross-reference churn data with bus factor warnings.

    Files that are both high-churn AND have bus factor issues are critical hotspots.
    """
    # Build bus factor lookup
    bf_lookup: dict[str, dict] = {}
    for w in bus_factor_warnings:
        bf_lookup[w.get("fp", "")] = w

    hotspots: list[dict] = []
    for file_path, count in file_changes.items():
        bf = bf_lookup.get(file_path)
        if bf:
            hotspots.append({
                "path": file_path,
                "count": count,
                "bus_factor": bf.get("bf", 1),
                "dominant_author": bf.get("da", ""),
                "dominant_pct": bf.get("dp", 0),
                "risk": "critical" if count > 10 else "high",
            })

    hotspots.sort(key=lambda h: -h["count"])
    return hotspots[:15]
