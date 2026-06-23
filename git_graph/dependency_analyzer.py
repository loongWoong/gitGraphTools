"""Branch dependency graph computation.

Builds a parent-child relationship tree between branches using fork/merge data.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class DepNode:
    """A node in the dependency graph."""
    name: str
    kind: str = "other"      # main, feature, release, hotfix, other
    status: str = "healthy"
    children: list[str] = field(default_factory=list)


def compute_dependency_graph(
    branches: list[dict],
    timeline_branches: list[dict],
    health_list: list[dict],
) -> dict:
    """Build a branch dependency tree from timeline fork data.

    Uses the 'pb' (parent branch) field from timeline data to construct the tree.

    Returns:
        {ns: [{n, k, st, ch: [names]}], es: [{f, to}]}
    """
    # Build health lookup
    health_lookup: dict[str, dict] = {h.get("n", ""): h for h in health_list}

    # Build nodes
    nodes: dict[str, DepNode] = {}
    for tb in timeline_branches:
        name = tb.get("n", "")
        if not name:
            continue

        h = health_lookup.get(name, {})
        node = DepNode(
            name=name,
            kind=_classify_kind(name, h.get("bt", "other")),
            status=h.get("st", "healthy"),
        )
        nodes[name] = node

    # Build parent-child relationships
    for tb in timeline_branches:
        name = tb.get("n", "")
        parent = tb.get("pb", "")
        if parent and parent in nodes and name in nodes:
            if name not in nodes[parent].children:
                nodes[parent].children.append(name)

    # Serialize
    ns = []
    es: list[dict] = []

    for name, node in nodes.items():
        ns.append({
            "n": node.name,
            "k": node.kind,
            "st": node.status,
            "ch": node.children,
        })

        for child in node.children:
            es.append({
                "f": name,
                "to": child,
            })

    return {"ns": ns, "es": es}


def _classify_kind(name: str, branch_type: str) -> str:
    """Classify branch for dependency graph display."""
    if branch_type in ("main", "develop"):
        return "main"
    if branch_type == "release":
        return "release"
    if branch_type == "hotfix":
        return "hotfix"
    if branch_type == "feature":
        return "feature"
    return "other"
