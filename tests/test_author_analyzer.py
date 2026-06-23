"""Tests for author analyzer."""

from git_graph.author_analyzer import compute_author_stats, compute_bus_factor


class TestAuthorStats:
    def test_basic_stats(self):
        commits = [
            {"a": "Alice", "t": "2025-01-01T00:00:00Z"},
            {"a": "Alice", "t": "2025-01-03T00:00:00Z"},
            {"a": "Bob", "t": "2025-01-02T00:00:00Z"},
        ]
        stats = compute_author_stats(commits, 3)
        assert len(stats) == 2
        alice = [s for s in stats if s["n"] == "Alice"][0]
        assert alice["cc"] == 2
        assert alice["pc"] == 66.7

    def test_empty_commits(self):
        stats = compute_author_stats([], 0)
        assert stats == []

    def test_sorted_by_commits(self):
        commits = [
            {"a": "Alice", "t": "2025-01-01T00:00:00Z"},
            {"a": "Bob", "t": "2025-01-02T00:00:00Z"},
            {"a": "Bob", "t": "2025-01-03T00:00:00Z"},
        ]
        stats = compute_author_stats(commits, 3)
        assert stats[0]["n"] == "Bob"  # Most commits first


class TestBusFactor:
    def test_high_dominance_triggered(self):
        file_data = {
            "src/main.py": {"Alice": 80, "Bob": 20},
        }
        warnings = compute_bus_factor(file_data, 100, threshold_pct=80.0)
        assert len(warnings) == 1
        assert warnings[0]["fp"] == "src/main.py"
        assert warnings[0]["da"] == "Alice"

    def test_below_threshold_not_triggered(self):
        file_data = {
            "src/main.py": {"Alice": 70, "Bob": 30},
        }
        warnings = compute_bus_factor(file_data, 100, threshold_pct=80.0)
        assert len(warnings) == 0

    def test_too_few_commits_skipped(self):
        file_data = {
            "src/main.py": {"Alice": 3},
        }
        warnings = compute_bus_factor(file_data, 100, min_commits=5)
        assert len(warnings) == 0

    def test_top_n_limit(self):
        file_data = {
            f"src/file{i}.py": {"Alice": 90, "Bob": 10}
            for i in range(15)
        }
        warnings = compute_bus_factor(file_data, 100, top_n=5)
        assert len(warnings) == 5
