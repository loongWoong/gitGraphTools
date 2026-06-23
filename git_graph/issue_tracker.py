"""Issue tracker integration — detects issue references in branch names.

Parses branch naming conventions to extract issue keys and detect which
tracker (JIRA, GitHub, Linear) is in use.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional


# Branch name patterns for issue detection
ISSUE_PATTERNS = [
    # JIRA / Linear: feature/PROJ-123, fix/TEAM-456
    re.compile(r"(?:feature|fix|feat|bug|hotfix|chore|release|task)[-/]([A-Z]+-\d+)", re.IGNORECASE),
    # Generic with slash: PROJ-123/description, ISSUE-456/description
    re.compile(r"^([A-Z]+-\d+)/", re.IGNORECASE),
    # GitHub style: 123-feature-name
    re.compile(r"^(\d+)[-/]", re.IGNORECASE),
]


@dataclass
class IssueInfo:
    """Information about a linked issue."""
    key: str
    tracker: str = ""           # "jira", "github", "linear", "unknown"
    title: str = ""             # From API if available
    status: str = ""            # From API if available
    url: str = ""               # Link to the issue


def parse_branch_issue(branch_name: str) -> Optional[str]:
    """Extract an issue key from a branch name.

    Examples:
        "feature/PROJ-123-login" → "PROJ-123"
        "fix/ISSUE-456" → "ISSUE-456"
        "123-fix-bug" → "123"
        "main" → None
    """
    for pattern in ISSUE_PATTERNS:
        match = pattern.search(branch_name)
        if match:
            return match.group(1)
    return None


def detect_issue_tracker(branch_names: list[str]) -> str:
    """Detect which issue tracker is used based on branch naming patterns.

    Returns one of: "jira", "github", "linear", "none"
    """
    jira_count = 0
    github_count = 0
    linear_count = 0

    for name in branch_names:
        key = parse_branch_issue(name)
        if key is None:
            continue
        if key.isdigit():
            github_count += 1
        elif "-" in key:
            # JIRA and Linear both use PROJECT-NUMBER format
            prefix = key.split("-")[0]
            if len(prefix) >= 3:
                jira_count += 1
            else:
                linear_count += 1

    if jira_count >= github_count and jira_count >= linear_count and jira_count > 0:
        return "jira"
    if github_count >= jira_count and github_count >= linear_count and github_count > 0:
        return "github"
    if linear_count > 0:
        return "linear"
    return "none"


def link_issues_to_branches(
    branches: list[dict],
    health_list: list[dict],
) -> dict:
    """Create a mapping from issue keys to branch information.

    Args:
        branches: Branch dicts (serialized).
        health_list: Health dicts from health_analyzer.

    Returns:
        {issue_key: {"b": [branch_names], "st": inferred_status, "tr": tracker, "url": url}}
    """
    branch_names = [b.get("n", "") for b in branches]
    tracker = detect_issue_tracker(branch_names)

    # Build health lookup
    health_lookup: dict[str, dict] = {}
    for h in health_list:
        health_lookup[h.get("n", "")] = h

    issue_map: dict[str, dict] = {}

    for b in branches:
        name = b.get("n", "")
        key = parse_branch_issue(name)
        if key is None:
            continue

        if key not in issue_map:
            # Build URL based on tracker
            url = ""
            if tracker == "github":
                url = f"https://github.com/{key}"  # will need repo context
            elif tracker == "jira":
                url = f"https://{key}.atlassian.net/browse/{key}"
            elif tracker == "linear":
                url = f"https://linear.app/issue/{key}"

            issue_map[key] = {
                "b": [],
                "st": _infer_status(name, health_lookup.get(name, {})),
                "tr": tracker,
                "url": url,
            }

        issue_map[key]["b"].append(name)

    return issue_map


def _infer_status(branch_name: str, health: dict) -> str:
    """Infer the issue status from branch name and health data.

    Returns one of: "todo", "in_progress", "review", "done"
    """
    st = health.get("st", "")
    mg = health.get("mg", False)

    if st == "zombie_merged" or mg:
        return "done"
    if st == "zombie_abandoned":
        return "todo"
    if st == "aging":
        return "in_progress"
    if st == "healthy":
        # Check if it's a main/dev branch — those are "done"
        bt = health.get("bt", "")
        if bt in ("main", "develop"):
            return "done"
        return "in_progress"
    return "todo"
