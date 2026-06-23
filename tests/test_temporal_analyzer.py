"""Tests for temporal analyzer."""

from datetime import datetime

from git_graph.data_model import Commit
from git_graph.temporal_analyzer import (
    compute_heatmap,
    compute_date_markers,
    compute_activity_stats,
)


class TestHeatmap:
    def test_week_buckets(self):
        commits = [
            Commit(hash="h0", short_hash="h0", parent_hashes=[],
                   timestamp="2025-01-06T10:00:00Z", author="Alice", subject="x"),
            Commit(hash="h1", short_hash="h1", parent_hashes=["h0"],
                   timestamp="2025-01-08T10:00:00Z", author="Bob", subject="y"),
        ]
        heatmap = compute_heatmap(commits, bucket="week")
        assert len(heatmap) >= 1
        assert "commits" in heatmap[0]
        assert "authors" in heatmap[0]

    def test_month_buckets(self):
        commits = [
            Commit(hash="h0", short_hash="h0", parent_hashes=[],
                   timestamp="2025-01-01T10:00:00Z", author="Alice", subject="x"),
            Commit(hash="h1", short_hash="h1", parent_hashes=["h0"],
                   timestamp="2025-02-15T10:00:00Z", author="Alice", subject="y"),
        ]
        heatmap = compute_heatmap(commits, bucket="month")
        assert len(heatmap) == 2

    def test_empty_commits(self):
        heatmap = compute_heatmap([])
        assert heatmap == []


class TestDateMarkers:
    def test_month_boundaries(self):
        commits = [
            Commit(hash="h0", short_hash="h0", parent_hashes=[],
                   timestamp="2025-01-15T00:00:00Z", author="A", subject="s",
                   row=0),
            Commit(hash="h1", short_hash="h1", parent_hashes=["h0"],
                   timestamp="2025-02-15T00:00:00Z", author="A", subject="s",
                   row=1),
        ]
        markers = compute_date_markers(commits)
        assert len(markers) == 2
        assert markers[0]["label"] == "2025-01"
        assert markers[1]["label"] == "2025-02"


class TestActivityStats:
    def test_basic_stats(self):
        commits = [
            Commit(hash="h0", short_hash="h0", parent_hashes=[],
                   timestamp="2025-01-01T00:00:00Z", author="Alice", subject="x"),
            Commit(hash="h1", short_hash="h1", parent_hashes=["h0"],
                   timestamp="2025-01-15T00:00:00Z", author="Bob", subject="y"),
        ]
        stats = compute_activity_stats(commits)
        assert stats["total_commits"] == 2
        assert stats["total_authors"] == 2
        assert stats["repo_age_days"] == 14

    def test_empty_commits(self):
        stats = compute_activity_stats([])
        assert stats == {}
