"""MCP (Model Context Protocol) Server for git-graph.

Provides a JSON-RPC endpoint that external AI agents (Claude, Cursor, etc.)
can use to query git repository data.

Protocol: JSON-RPC 2.0 over HTTP POST /mcp
"""

from __future__ import annotations

import json
from typing import Any, Callable


class MCPHandler:
    """Handles JSON-RPC MCP requests for git repository data."""

    def __init__(self, repo_path: str, commits: list[dict], branches: list[dict],
                 health: list[dict], author_stats: list[dict],
                 graph_data: dict | None = None):
        self.repo_path = repo_path
        self.commits = commits
        self.branches = branches
        self.health = health
        self.author_stats = author_stats
        self.graph_data = graph_data or {}

        # Build lookup maps
        self.health_lookup: dict[str, dict] = {}
        for h in health:
            self.health_lookup[h.get("n", "")] = h

        # Tool definitions and handlers
        self._tools: dict[str, dict] = {
            "get_branches": {
                "description": "Get all branches with their health status",
                "handler": self._get_branches,
            },
            "get_commits": {
                "description": "Get commits, optionally filtered by branch, hash, or author",
                "handler": self._get_commits,
            },
            "get_commit_detail": {
                "description": "Get detailed info for a specific commit",
                "handler": self._get_commit_detail,
            },
            "get_health_report": {
                "description": "Get the full branch health analysis report",
                "handler": self._get_health_report,
            },
            "get_author_stats": {
                "description": "Get author contribution statistics",
                "handler": self._get_author_stats,
            },
            "get_dora_metrics": {
                "description": "Get DORA metrics (deployment frequency, lead time, CFR, MTTR)",
                "handler": self._get_dora_metrics,
            },
        }

    def handle_request(self, request_body: bytes) -> bytes:
        """Handle a JSON-RPC request.

        Returns bytes suitable for an HTTP response body.
        """
        try:
            rpc = json.loads(request_body)
        except json.JSONDecodeError:
            return _jsonrpc_error(None, -32700, "Parse error")

        method = rpc.get("method", "")
        req_id = rpc.get("id")

        if method == "initialize":
            return _jsonrpc_result(req_id, {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": {
                    "name": "git-graph",
                    "version": "2.0.0",
                },
            })

        if method == "tools/list":
            tools = [
                {
                    "name": name,
                    "description": info["description"],
                    "inputSchema": {"type": "object", "properties": {}},
                }
                for name, info in self._tools.items()
            ]
            return _jsonrpc_result(req_id, {"tools": tools})

        if method == "tools/call":
            params = rpc.get("params", {})
            tool_name = params.get("name", "")
            tool_args = params.get("arguments", {})

            if tool_name in self._tools:
                try:
                    result = self._tools[tool_name]["handler"](tool_args)
                    return _jsonrpc_result(req_id, {
                        "content": [{"type": "text", "text": json.dumps(result, ensure_ascii=False, indent=2)}],
                    })
                except Exception as e:
                    return _jsonrpc_error(req_id, -32000, str(e))

            return _jsonrpc_error(req_id, -32601, f"Unknown tool: {tool_name}")

        return _jsonrpc_error(req_id, -32601, f"Unknown method: {method}")

    # ── Tool Handlers ──────────────────────────────────────────────

    def _get_branches(self, args: dict) -> list[dict]:
        result = []
        for b in self.branches:
            name = b.get("n", "")
            h = self.health_lookup.get(name, {})
            result.append({
                "name": name,
                "kind": b.get("k", ""),
                "health_status": h.get("st", "unknown"),
                "health_score": h.get("sc", 0),
                "is_merged": h.get("mg", False),
                "commit_count": h.get("cc", 0),
                "days_since_last_commit": h.get("ds", 0),
            })
        return result

    def _get_commits(self, args: dict) -> list[dict]:
        branch = args.get("branch", "")
        author = args.get("author", "")
        limit = args.get("limit", 50)
        offset = args.get("offset", 0)

        result = []
        for c in self.commits:
            if branch and branch not in c.get("b", []):
                continue
            if author and c.get("a", "").lower() != author.lower():
                continue
            result.append({
                "hash": c.get("h", ""),
                "subject": c.get("s", ""),
                "author": c.get("a", ""),
                "timestamp": c.get("t", ""),
                "branches": c.get("b", []),
            })

        return result[offset:offset + limit]

    def _get_commit_detail(self, args: dict) -> dict | None:
        hash_val = args.get("hash", "")
        for c in self.commits:
            if c.get("h", "") == hash_val:
                return {
                    "hash": c.get("h", ""),
                    "subject": c.get("s", ""),
                    "author": c.get("a", ""),
                    "timestamp": c.get("t", ""),
                    "full_message": c.get("fm", ""),
                    "branches": c.get("b", []),
                    "is_head": c.get("hd", False),
                }
        return None

    def _get_health_report(self, args: dict) -> dict:
        return {
            "branches": [
                {
                    "name": h.get("n", ""),
                    "type": h.get("bt", ""),
                    "status": h.get("st", ""),
                    "score": h.get("sc", 0),
                    "warnings": h.get("wn", []),
                }
                for h in self.health
            ],
            "repo_health_score": self.graph_data.get("repo_health_score", 0),
        }

    def _get_author_stats(self, args: dict) -> list[dict]:
        return [
            {
                "name": a.get("n", ""),
                "commits": a.get("cc", 0),
                "percentage": a.get("pc", 0),
                "first_commit": a.get("fd", ""),
                "last_commit": a.get("ld", ""),
            }
            for a in self.author_stats
        ]

    def _get_dora_metrics(self, args: dict) -> dict:
        return self.graph_data.get("dora", {})


def _jsonrpc_result(req_id, result: Any) -> bytes:
    return json.dumps({
        "jsonrpc": "2.0",
        "id": req_id,
        "result": result,
    }, ensure_ascii=False).encode("utf-8")


def _jsonrpc_error(req_id, code: int, message: str) -> bytes:
    return json.dumps({
        "jsonrpc": "2.0",
        "id": req_id,
        "error": {"code": code, "message": message},
    }, ensure_ascii=False).encode("utf-8")
