"""Tests for layout engine."""

from git_graph.data_model import (
    Commit, BranchInfo, parse_commits, parse_refs, build_dag,
)
from git_graph.layout_engine import (
    _LaneState,
    _branch_tips_map,
    _topological_sort,
    _assign_lanes,
    _build_edges,
    layout,
)


class TestLaneState:
    def test_allocate_new_lane(self):
        state = _LaneState()
        lane = state.allocate("main")
        assert lane == 0
        assert state.active[0] == "main"

    def test_allocate_second_lane(self):
        state = _LaneState()
        state.allocate("main")
        lane = state.allocate("feature")
        assert lane == 1

    def test_reuses_existing_lane(self):
        state = _LaneState()
        first = state.allocate("main")
        second = state.allocate("main")
        assert first == second

    def test_free_lane(self):
        state = _LaneState()
        state.allocate("main")
        state.free("main")
        assert state.active[0] is None

    def test_lane_of(self):
        state = _LaneState()
        state.allocate("main")
        assert state.lane_of("main") == 0
        assert state.lane_of("nonexistent") is None


class TestBranchTipsMap:
    def test_multiple_branches_at_same_commit(self):
        branches = [
            BranchInfo(name="main", kind="local", tip_hash="abc123"),
            BranchInfo(name="origin/main", kind="remote", tip_hash="abc123"),
        ]
        tips = _branch_tips_map(branches)
        assert len(tips["abc123"]) == 2


class TestTopologicalSort:
    def test_sorts_by_index(self):
        commits = [
            Commit(hash="h0", short_hash="h0", parent_hashes=[]),
            Commit(hash="h1", short_hash="h1", parent_hashes=["h0"]),
            Commit(hash="h2", short_hash="h2", parent_hashes=["h1"]),
        ]
        _topological_sort(commits)
        assert commits[0].row == 0
        assert commits[1].row == 1
        assert commits[2].row == 2


class TestAssignLanes:
    def test_simple_linear_lanes(self, sample_commit_lines, sample_ref_lines):
        commits = parse_commits(sample_commit_lines)
        commit_map = build_dag(commits)
        branches = parse_refs(sample_ref_lines)
        _assign_lanes(commits, commit_map, branches)
        # All commits should have a lane assigned
        for c in commits:
            assert c.lane >= 0


class TestBuildEdges:
    def test_linear_edge(self):
        commits = [
            Commit(hash="h0", short_hash="s0", parent_hashes=[], row=0, lane=0),
            Commit(hash="h1", short_hash="s1", parent_hashes=["h0"], row=1, lane=0),
        ]
        commit_map = build_dag(commits)
        edges = _build_edges(commits, commit_map)
        assert len(edges) == 1
        assert edges[0].kind == "linear"
