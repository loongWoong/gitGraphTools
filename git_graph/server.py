"""Lightweight HTTP server for the git graph dashboard.

Provides on-demand API endpoints for commit file lists and diffs.
Started via ``git_graph.py --serve``.
"""

from __future__ import annotations

import json
import os
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler

from .git_reader import get_commit_files, get_commit_diff


class GitGraphHandler(BaseHTTPRequestHandler):
    """Handles dashboard and API requests."""

    # Set by the caller before starting the server
    dashboard_html: str = ""
    repo_path: str = ""

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

        # ── 404 ──
        self._send_error_json("Not found", 404)

    def do_OPTIONS(self):
        """Handle CORS preflight."""
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()


def start_server(
    dashboard_html: str,
    repo_path: str,
    port: int = 8765,
    open_browser: bool = True,
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
