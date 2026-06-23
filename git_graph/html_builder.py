"""HTML builder — serialises GraphData (including intelligence layers) to JSON and injects into the template."""

from __future__ import annotations

import json
import os

from .data_model import GraphData
from .__template__ import HTML_TEMPLATE


def build_html(graph_data: GraphData) -> str:
    """Generate a complete standalone HTML document.

    Args:
        graph_data: The fully populated graph data including intelligence layers.

    Returns:
        Complete HTML string with embedded JSON data, CSS, and JS.
    """
    payload = {
        "metadata": graph_data.metadata,
        "head": graph_data.head,
        "commits": graph_data.commits,
        "edges": graph_data.edges,
        "branches": graph_data.branches,
        # ── Intelligence layers ──
        "health": graph_data.health,
        "heatmap": graph_data.heatmap,
        "author_stats": graph_data.author_stats,
        "bus_factor_warnings": graph_data.bus_factor_warnings,
        "branch_lifetimes": graph_data.branch_lifetimes,
        "date_markers": graph_data.date_markers,
        "activity_stats": graph_data.activity_stats,
        "repo_health_score": graph_data.repo_health_score,
        "status_counts": graph_data.status_counts,
        "timeline": graph_data.timeline,
        # ── Phase 1-5 additions ──
        "il": graph_data.issue_links,
        "sp": graph_data.sprints,
        "bd": graph_data.burndown,
        "pu": graph_data.pulse,
        "dr": graph_data.dora,
        "pr": graph_data.pr_metrics,
        "ch": graph_data.churn,
        "cr": graph_data.conflict_risks,
        "bs": graph_data.branch_summaries,
        "rn": graph_data.release_notes,
        "dg": graph_data.dependency_graph,
        "cl": graph_data.cleanup_suggestions,
        "mc": graph_data.multi_repo,
    }

    json_str = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))

    return HTML_TEMPLATE.replace("{{GRAPH_DATA}}", json_str)


def write_html(graph_data: GraphData, output_path: str) -> str:
    """Build HTML and write to *output_path*.

    Returns the absolute path of the written file.
    """
    html = build_html(graph_data)
    abs_path = os.path.abspath(output_path)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)

    return abs_path
