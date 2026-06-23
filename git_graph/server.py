"""Lightweight HTTP server for the git graph dashboard.

Provides on-demand API endpoints for commit file lists and diffs,
plus optional MCP and SSE support.
Started via ``git_graph.py --serve``.
"""

from __future__ import annotations

import json
import os
import time
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler

from .git_reader import get_commit_files, get_commit_diff


class GitGraphHandler(BaseHTTPRequestHandler):
    """Handles dashboard and API requests."""

    # Set by the caller before starting the server
    dashboard_html: str = ""
    repo_path: str = ""
    mcp_handler: object | None = None  # MCPHandler instance
    enable_watch: bool = False

    def log_message(self, format, *args):
        """Suppress default stderr logging — use a cleaner format."""
        print(f"  [{self.command}] {args[0]}")

    def _send_json(self, data, status=200):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", len(body))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def _send_html(self, html_str, status=200):
        body = html_str.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", len(body))
        self.end_headers()
        self.wfile.write(body)

    def _send_error_json(self, message, status=404):
        self._send_json({"error": message}, status)

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path.rstrip("/")
        params = urllib.parse.parse_qs(parsed.query)

        # ── Dashboard ──
        if path == "" or path == "/":
            self._send_html(self.dashboard_html)
            return

        # ── API: commit file list ──
        if path.startswith("/api/files/"):
            commit_hash = path[len("/api/files/"):]
            if not commit_hash or len(commit_hash) < 7:
                self._send_error_json("Missing or invalid commit hash", 400)
                return
            try:
                files = get_commit_files(self.repo_path, commit_hash)
                self._send_json({"files": files, "commit": commit_hash})
            except Exception as e:
                self._send_error_json(str(e), 500)
            return

        # ── API: commit diff ──
        if path.startswith("/api/diff/"):
            commit_hash = path[len("/api/diff/"):]
            if not commit_hash or len(commit_hash) < 7:
                self._send_error_json("Missing or invalid commit hash", 400)
                return
            file_filter = params.get("file", [None])[0]
            try:
                diff_text = get_commit_diff(self.repo_path, commit_hash, file_filter)
                self._send_json({"diff": diff_text, "commit": commit_hash})
            except Exception as e:
                self._send_error_json(str(e), 500)
            return

        # ── API: SSE watch (live updates) ──
        if path == "/api/watch" and self.enable_watch:
            self._handle_sse_watch()
            return

        # ── 404 ──
        self._send_error_json("Not found", 404)

    def do_OPTIONS(self):
        """Handle CORS preflight."""
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_POST(self):
        """Handle POST requests (MCP)."""
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path.rstrip("/")

        if path == "/mcp" and self.mcp_handler is not None:
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length)
            try:
                response = self.mcp_handler.handle_request(body)
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Content-Length", len(response))
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(response)
            except Exception as e:
                self._send_error_json(str(e), 500)
            return

        self._send_error_json("Not found", 404)

    def _handle_sse_watch(self):
        """SSE endpoint that pushes updates when git refs change."""
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection", "keep-alive")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()

        refs_dir = os.path.join(self.repo_path, ".git", "refs", "heads")
        last_mtime = 0

        try:
            if os.path.exists(refs_dir):
                last_mtime = _get_refs_mtime(refs_dir)

            # Send initial connection event
            self.wfile.write(b"data: {\"type\": \"connected\"}\n\n")
            self.wfile.flush()

            while True:
                time.sleep(1)
                if os.path.exists(refs_dir):
                    current_mtime = _get_refs_mtime(refs_dir)
                    if current_mtime > last_mtime:
                        last_mtime = current_mtime
                        self.wfile.write(b"data: {\"type\": \"refs_changed\"}\n\n")
                        self.wfile.flush()
        except (BrokenPipeError, ConnectionResetError, OSError):
            pass  # Client disconnected


def _get_refs_mtime(refs_dir: str) -> float:
    """Get the most recent modification time of any file under refs_dir."""
    max_mtime = 0
    for root, dirs, files in os.walk(refs_dir):
        for f in files:
            try:
                mtime = os.path.getmtime(os.path.join(root, f))
                if mtime > max_mtime:
                    max_mtime = mtime
            except OSError:
                pass
    return max_mtime


def start_server(
    dashboard_html: str,
    repo_path: str,
    port: int = 8765,
    open_browser: bool = True,
    enable_mcp: bool = False,
    enable_watch: bool = False,
    graph_data: dict | None = None,
) -> None:
    """Start the HTTP server and block until interrupted.

    Args:
        dashboard_html: Pre-generated dashboard HTML string.
        repo_path: Path to the git repository for on-demand git queries.
        port: Port to listen on (default 8765).
        open_browser: If True, open the dashboard in the default browser.
    """
    # Inject server-mode flag into HTML so the frontend knows API is available
    # Replace the DATA assignment to include server info
    server_flag = '<script>window.__SERVER_MODE__=true;window.__SERVER_PORT__=' + str(port) + ';</script>'
    html_with_flag = dashboard_html.replace(
        "<script>",
        server_flag + "\n<script>",
        1,
    )

    GitGraphHandler.dashboard_html = html_with_flag
    GitGraphHandler.repo_path = os.path.abspath(repo_path)
    GitGraphHandler.enable_watch = enable_watch

    if enable_mcp and graph_data:
        from .mcp_server import MCPHandler
        GitGraphHandler.mcp_handler = MCPHandler(
            repo_path=os.path.abspath(repo_path),
            commits=graph_data.get("commits", []),
            branches=graph_data.get("branches", []),
            health=graph_data.get("health", []),
            author_stats=graph_data.get("author_stats", []),
            graph_data=graph_data,
        )
    else:
        GitGraphHandler.mcp_handler = None

    server = HTTPServer(("127.0.0.1", port), GitGraphHandler)
    url = f"http://127.0.0.1:{port}"

    print(f"\n  Server started: {url}")
    print(f"  Repository:     {GitGraphHandler.repo_path}")
    print(f"  Press Ctrl+C to stop.\n")

    if open_browser:
        import webbrowser
        webbrowser.open(url)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n  Server stopped.")
        server.shutdown()
