"""Tests for health analyzer."""

from git_graph.data_model import (
    Commit, BranchInfo, parse_commits, parse_refs, build_dag,
)
from git_graph.health_analyzer import (
    detect_branch_type,
    _calc_recency_score,
    _calc_divergence_score,
    _calc_lifetime_score,
    compute_repo_health,
    count_by_status,
    BranchHealth,
    set_language,
    _w,
)


class TestDetectBranchType:
    def test_main(self):
        assert detect_branch_type("main") == "main"
        assert detect_branch_type("master") == "main"
        assert detect_branch_type("MAIN") == "main"

    def test_develop(self):
        assert detect_branch_type("develop") == "develop"
        assert detect_branch_type("dev") == "develop"

    def test_release(self):
        assert detect_branch_type("release/v1.0") == "release"
        assert detect_branch_type("release-2.0") == "release"

    def test_hotfix(self):
        assert detect_branch_type("hotfix/fix-login") == "hotfix"
        assert detect_branch_type("fix/bug-123") == "hotfix"
        assert detect_branch_type("bugfix/edge-case") == "hotfix"

    def test_feature(self):
        assert detect_branch_type("feature/new-ui") == "feature"
        assert detect_branch_type("feat/dark-mode") == "feature"

    def test_other(self):
        assert detect_branch_type("random-branch") == "other"


class TestRecencyScore:
    def test_recent_main(self):
        score, days = _calc_recency_score("2026-06-20T00:00:00Z", "main")
        assert score == 100

    def test_aging_main(self):
        score, days = _calc_recency_score("2025-12-01T00:00:00Z", "main")
        assert score < 100

    def test_empty_date(self):
        score, days = _calc_recency_score("", "main")
        assert score == 0
        assert days == 999


class TestDivergenceScore:
    def test_main_always_100(self):
        assert _calc_divergence_score(500, "main") == 100

    def test_small_divergence(self):
        assert _calc_divergence_score(5, "feature") == 100

    def test_large_divergence(self):
        assert _calc_divergence_score(200, "feature") < 40


class TestLifetimeScore:
    def test_short_feature(self):
        assert _calc_lifetime_score(30, "feature") == 100

    def test_long_feature(self):
        assert _calc_lifetime_score(200, "feature") < 40


class TestRepoHealth:
    def test_empty_health_list(self):
        assert compute_repo_health([]) == 0

    def test_single_healthy(self):
        h = BranchHealth(
            branch_name="main", branch_type="main",
            score=100, status="healthy",
        )
        score = compute_repo_health([h])
        assert 90 <= score <= 100


class TestCountByStatus:
    def test_mixed_statuses(self):
        results = [
            BranchHealth(branch_name="main", branch_type="main", score=100, status="healthy"),
            BranchHealth(branch_name="old", branch_type="feature", score=30, status="aging"),
        ]
        counts = count_by_status(results)
        assert counts["healthy"] == 1
        assert counts["aging"] == 1


class TestI18n:
    def test_warning_en(self):
        set_language("en")
        msg = _w("no_update", days="99")
        assert "99 days" in msg

    def test_warning_zh(self):
        set_language("zh")
        msg = _w("no_update", days="99")
        assert "99天" in msg

    def test_warning_behind_main(self):
        set_language("en")
        msg = _w("behind_main", count="50")
        assert "50 commits" in msg
