#!/usr/bin/env python3
"""git-graph: Generate an interactive repository intelligence dashboard.

Usage:
    python git_graph.py [REPO_PATH] [--output OUTPUT] [--max-commits N] [--open]

Examples:
    python git_graph.py .                          # Current repo -> git_graph.html
    python git_graph.py ~/my-project -o dashboard.html
    python git_graph.py . --max-commits 100 --open
"""

from __future__ import annotations

import argparse
import logging
import os
import sys
import webbrowser
from typing import Optional

logger = logging.getLogger("git_graph")

# Allow running as both `python git_graph.py` and `python -m git_graph`
try:
    from git_graph.git_reader import (
        get_all_commits,
        get_refs,
        get_head_state,
        get_commit_messages_batch,
        get_merged_branches,
        get_file_author_stats,
        GitError,
    )
    from git_graph.data_model import (
        Commit,
        GraphData,
        parse_commits,
        parse_refs,
        build_dag,
        assign_branch_labels,
        mark_refs,
    )
    from git_graph.layout_engine import layout
    from git_graph.health_analyzer import (
        compute_all_health,
        compute_repo_health,
        count_by_status,
        set_language,
    )
    from git_graph.temporal_analyzer import (
        compute_heatmap,
        compute_branch_lifetimes,
        compute_date_markers,
        compute_activity_stats,
        compute_timeline_branches,
    )
    from git_graph.author_analyzer import (
        compute_author_stats,
        compute_bus_factor,
    )
    from git_graph.html_builder import write_html
except ImportError:
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from git_graph.git_reader import (
        get_all_commits,
        get_refs,
        get_head_state,
        get_commit_messages_batch,
        get_merged_branches,
        get_file_author_stats,
        GitError,
    )
    from git_graph.data_model import (
        Commit,
        GraphData,
        parse_commits,
        parse_refs,
        build_dag,
        assign_branch_labels,
        mark_refs,
    )
    from git_graph.layout_engine import layout
    from git_graph.health_analyzer import (
        compute_all_health,
        compute_repo_health,
        count_by_status,
        set_language,
    )
    from git_graph.temporal_analyzer import (
        compute_heatmap,
        compute_branch_lifetimes,
        compute_date_markers,
        compute_activity_stats,
        compute_timeline_branches,
    )
    from git_graph.author_analyzer import (
        compute_author_stats,
        compute_bus_factor,
    )
    from git_graph.html_builder import write_html


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="git-graph",
        description="Generate an interactive repository intelligence dashboard.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  git-graph .                              Current repo -> git_graph.html
  git-graph ~/my-project -o dashboard.html Custom output path
  git-graph . --max-commits 100 --open     Limit + auto-open in browser
        """.strip(),
    )

    parser.add_argument(
        "repo_path",
        nargs="?",
        default=".",
        help="Path to the git repository (default: current directory).",
    )

    parser.add_argument(
        "-o", "--output",
        default="git_graph.html",
        help="Output HTML file path (default: git_graph.html).",
    )

    parser.add_argument(
        "-n", "--max-commits",
        type=int,
        default=None,
        help="Limit to the most recent N commits (default: unlimited).",
    )

    parser.add_argument(
        "--open",
        action="store_true",
        default=False,
        help="Open the generated HTML in the default browser.",
    )

    parser.add_argument(
        "--serve",
        action="store_true",
        default=False,
        help="Start a local HTTP server for on-demand diff viewing (port 8765).",
    )

    parser.add_argument(
        "--port",
        type=int,
        default=8765,
        help="Server port when --serve is used (default: 8765).",
    )

    parser.add_argument(
        "--mcp",
        action="store_true",
        default=False,
        help="Enable MCP server endpoint (POST /mcp) when --serve is active.",
    )

    parser.add_argument(
        "--watch",
        action="store_true",
        default=False,
        help="Enable live-reload via SSE when --serve is active.",
    )

    from git_graph import __version__

    parser.add_argument(
        "--version",
        action="version",
        version=f"git-graph {__version__}",
    )

    parser.add_argument(
        "--lang",
        choices=["en", "zh"],
        default="en",
        help="Language for warning messages (default: en).",
    )

    parser.add_argument(
        "--config",
        type=str,
        default=None,
        help="Path to JSON config file for overriding defaults.",
    )

    return parser


def _build_branch_commits_map(
    commits: list[Commit],
    commit_map: dict[str, Commit],
) -> dict[str, list[str]]:
    """Build a mapping: branch_name -> list of commit hashes on that branch."""
    result: dict[str, list[str]] = {}
    for c in commits:
        for branch_name in c.branches:
            result.setdefault(branch_name, []).append(c.hash)
    return result


def main(argv: Optional[list[str]] = None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)

    repo_path = os.path.abspath(args.repo_path)

    # ── Load configuration ──
    from git_graph.config import load_config
    config = load_config(args.config)
    config.lang = args.lang  # CLI arg overrides config file
    set_language(config.lang)

    # Override defaults from config if not explicitly set
    if args.output == "git_graph.html":
        args.output = config.default_output
    if args.port == 8765:
        args.port = config.default_port

    if not os.path.isdir(repo_path):
        print(f"Error: '{repo_path}' is not a valid directory.", file=sys.stderr)
        return 1

    git_dir = os.path.join(repo_path, ".git")
    if not os.path.exists(git_dir):
        print(
            f"Error: '{repo_path}' does not appear to be a git repository.",
            file=sys.stderr,
        )
        return 2

    try:
        logging.basicConfig(
            level=logging.INFO,
            format="%(message)s",
            stream=sys.stderr,
        )

        logger.info(f"Reading git history from: {repo_path}")

        # ── 1. Gather raw data ──
        logger.info("  - Fetching commits...")
        commit_lines = get_all_commits(repo_path, args.max_commits)

        logger.info("  - Fetching refs (branches + tags)...")
        ref_lines = get_refs(repo_path)

        logger.info("  - Reading HEAD state...")
        head_branch, head_hash = get_head_state(repo_path)
        head_detached = head_branch is None

        logger.info("  - Detecting merged branches...")
        merged_set = get_merged_branches(repo_path)

        # ── 2. Parse ──
        logger.info("  - Parsing commits...")
        commits = parse_commits(commit_lines)

        logger.info("  - Parsing refs...")
        branches = parse_refs(ref_lines)

        # Mark HEAD branch
        for b in branches:
            if b.name == head_branch:
                b.is_head = True

        # ── 3. Build DAG ──
        commit_map = build_dag(commits)
        assign_branch_labels(commits, commit_map, branches)
        mark_refs(commits, commit_map, branches)

        # ── 4. Fetch full commit messages ──
        logger.info("  - Fetching full commit messages...")
        commit_hashes = [c.hash for c in commits]
        full_msgs = get_commit_messages_batch(repo_path, commit_hashes)
        for c in commits:
            c.full_message = full_msgs.get(c.hash, c.subject)

        # ── 5. Build branch-commits mapping (used by analyzers) ──
        branch_commits_map = _build_branch_commits_map(commits, commit_map)

        # ── 6. DAG Layout ──
        logger.info(f"  - Computing DAG layout ({len(commits)} commits, {len(branches)} branches)...")
        graph_data = layout(
            repo_path=repo_path,
            commits=commits,
            branches=branches,
            head_branch=head_branch,
            head_hash=head_hash,
            head_detached=head_detached,
        )

        # ── 7. Intelligence Layer ──
        logger.info("  - Computing branch health scores...")
        health_results = compute_all_health(
            branches, commits, commit_map, merged_set, branch_commits_map,
        )
        repo_health = compute_repo_health(health_results)
        status_counts = count_by_status(health_results)

        graph_data.health = [
            {
                "n": h.branch_name,
                "bt": h.branch_type,
                "sc": h.score,
                "st": h.status,
                "fd": h.first_commit_date,
                "ld": h.last_commit_date,
                "ds": h.days_since_last_commit,
                "bh": h.commits_behind_main,
                "cc": h.commit_count,
                "uc": h.unique_commit_count,
                "ac": h.author_count,
                "mg": h.is_merged,
                "ldd": h.lifetime_days,
                "wn": h.warnings,
            }
            for h in health_results
        ]
        graph_data.repo_health_score = repo_health
        graph_data.status_counts = status_counts

        # Annotate branch_lifetimes with health status
        health_map = {h.branch_name: h.status for h in health_results}
        merged_map = {h.branch_name: h.is_merged for h in health_results}

        logger.info("  - Computing temporal data...")
        branch_lifetimes = compute_branch_lifetimes(
            branches, commits, commit_map, branch_commits_map,
        )
        for bl in branch_lifetimes:
            bl["st"] = health_map.get(bl["n"], "healthy")
            bl["mg"] = merged_map.get(bl["n"], False)
        graph_data.branch_lifetimes = branch_lifetimes

        graph_data.heatmap = compute_heatmap(commits)
        graph_data.date_markers = compute_date_markers(commits)
        graph_data.activity_stats = compute_activity_stats(commits)

        logger.info("  - Computing timeline fork/merge data...")
        graph_data.timeline = compute_timeline_branches(
            branches, commits, commit_map, branch_commits_map,
            graph_data.health, head_branch,
        )

        # ── 8. Author Layer ──
        logger.info("  - Computing author stats...")
        graph_data.author_stats = compute_author_stats(
            graph_data.commits, len(commits),
        )

        logger.info("  - Computing bus factor...")
        file_authors = get_file_author_stats(repo_path)
        graph_data.bus_factor_warnings = compute_bus_factor(
            file_authors, len(commits),
            top_n=config.bus_factor_top_n,
            threshold_pct=config.bus_factor_threshold_pct,
            min_commits=config.bus_factor_min_commits,
        )

        # ── 8b. Phase 1: Issue tracking + Sprints + Pulse ──
        logger.info("  - Detecting issue/branch links...")
        from git_graph.issue_tracker import link_issues_to_branches
        graph_data.issue_links = link_issues_to_branches(
            graph_data.branches, graph_data.health,
        )

        logger.info("  - Computing sprint analysis...")
        from git_graph.sprint_analyzer import compute_sprints, compute_burndown
        graph_data.sprints = compute_sprints(
            graph_data.branches, graph_data.commits,
            sprint_days=config.sprint_days,
        )
        burndown_data: dict[str, list] = {}
        for sp in graph_data.sprints[:4]:  # burndown for last 4 sprints
            burndown_data[sp["n"]] = compute_burndown(
                sp, graph_data.branches, graph_data.commits,
            )
        graph_data.burndown = burndown_data

        logger.info("  - Computing project pulse...")
        from git_graph.pulse_analyzer import compute_pulse
        graph_data.pulse = compute_pulse(
            graph_data.commits, graph_data.branches,
            graph_data.health, graph_data.issue_links,
            inactive_days=config.pulse_inactive_days,
            long_lived_days=config.pulse_long_lived_days,
            behind_warn=config.pulse_behind_warn,
        )

        # ── 8c. Phase 2: DORA + PR + Churn ──
        logger.info("  - Computing DORA metrics...")
        from git_graph.dora_analyzer import compute_all_dora, compute_pr_metrics
        graph_data.dora = compute_all_dora(
            graph_data.commits, graph_data.branches, merged_set,
        )
        graph_data.pr_metrics = compute_pr_metrics(
            graph_data.commits, merged_set,
        )

        logger.info("  - Computing code churn...")
        from git_graph.git_reader import get_file_change_frequency
        from git_graph.churn_analyzer import compute_churn_heatmap, detect_hotspots
        file_changes = get_file_change_frequency(repo_path)
        graph_data.churn = compute_churn_heatmap(file_changes)

        # ── 8d. Phase 3: AI Insights ──
        logger.info("  - Predicting conflict risks...")
        from git_graph.conflict_predictor import predict_conflicts
        graph_data.conflict_risks = predict_conflicts(
            graph_data.branches, graph_data.health, repo_path,
        )

        logger.info("  - Generating branch summaries...")
        from git_graph.summarizer import generate_branch_summary, generate_release_notes
        summaries: dict[str, str] = {}
        for b in graph_data.branches:
            name = b.get("n", "")
            if name:
                summaries[name] = generate_branch_summary(name, graph_data.commits)
        graph_data.branch_summaries = summaries
        graph_data.release_notes = generate_release_notes(
            graph_data.branches, graph_data.health,
        )

        # ── 8e. Phase 4: Dependencies + Cleanup ──
        logger.info("  - Computing dependency graph...")
        from git_graph.dependency_analyzer import compute_dependency_graph
        graph_data.dependency_graph = compute_dependency_graph(
            graph_data.branches,
            graph_data.timeline.get("branches", []),
            graph_data.health,
        )

        logger.info("  - Analyzing cleanup candidates...")
        from git_graph.cleanup_analyzer import analyze_cleanup_candidates
        graph_data.cleanup_suggestions = analyze_cleanup_candidates(
            graph_data.branches, graph_data.health,
        )

        # ── 9. Generate HTML ──
        logger.info("  - Generating HTML dashboard...")
        from git_graph.html_builder import build_html
        html_str = build_html(graph_data)

        if not args.serve:
            # Static file mode
            output_path = write_html(graph_data, args.output)
            logger.info(f"\n[OK] Dashboard generated: {output_path}")
        else:
            # Server mode — HTML is kept in memory
            output_path = os.path.abspath(args.output)
            logger.info(f"\n[OK] Dashboard ready (server mode)")

        logger.info(f"  {graph_data.metadata['total_commits']} commits")
        logger.info(f"  {graph_data.metadata['total_branches']} branches")
        logger.info(f"  {graph_data.metadata['total_lanes']} lanes")
        logger.info(f"  Repository health: {repo_health}/100")
        if status_counts:
            status_names = {
                "healthy": "healthy", "aging": "aging",
                "zombie_merged": "merged-zombie", "zombie_abandoned": "abandoned-zombie",
                "merged_stale": "merged-stale",
            }
            parts = [
                f'{status_counts.get(k, 0)} {status_names.get(k, k)}'
                for k in ["healthy", "aging", "merged_stale", "zombie_merged", "zombie_abandoned"]
            ]
            logger.info(f"  Status: {', '.join(parts)}")

        # ── 10. Server mode ──
        if args.serve:
            from git_graph.server import start_server
            start_server(
                dashboard_html=html_str,
                repo_path=repo_path,
                port=args.port,
                open_browser=not args.open,
                enable_mcp=args.mcp,
                enable_watch=args.watch,
                graph_data={
                    "commits": graph_data.commits,
                    "branches": graph_data.branches,
                    "health": graph_data.health,
                    "author_stats": graph_data.author_stats,
                    "dora": graph_data.dora,
                    "repo_health_score": graph_data.repo_health_score,
                },
            )
            return 0

        # ── 11. Open in browser (static mode) ──
        if args.open:
            url = f"file:///{output_path.replace(os.sep, '/')}"
            logger.info(f"  Opening in browser: {url}")
            webbrowser.open(url)

        return 0

    except GitError as e:
        print(f"Error: {e}", file=sys.stderr)
        return e.exit_code

    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
