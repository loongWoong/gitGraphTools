"""Tests for data model parsing and DAG building."""

from git_graph.data_model import (
    Commit,
    BranchInfo,
    Edge,
    GraphData,
    parse_commits,
    parse_refs,
    build_dag,
    assign_branch_labels,
    mark_refs,
)


class TestParseCommits:
    def test_parse_commits_normal(self, sample_commit_lines):
        commits = parse_commits(sample_commit_lines)
        assert len(commits) == 4
        assert commits[0].short_hash == "a1b2c3d"
        assert commits[0].author == "Alice"
        assert commits[0].subject == "Initial commit"

    def test_parse_commits_root_has_no_parents(self, sample_commit_lines):
        commits = parse_commits(sample_commit_lines)
        assert commits[0].parent_hashes == []

    def test_parse_commits_merge_has_two_parents(self, sample_commit_lines):
        commits = parse_commits(sample_commit_lines)
        merge_commit = commits[3]
        assert len(merge_commit.parent_hashes) == 2
        assert "a1b2c3d4e5f6789012345678901234567890abc" in merge_commit.parent_hashes

    def test_parse_commits_empty_list(self):
        commits = parse_commits([])
        assert commits == []

    def test_parse_commits_malformed_line(self):
        commits = parse_commits(["short|only|three|fields"])
        assert len(commits) == 0

    def test_parse_commits_empty_parent_string(self):
        commits = parse_commits([
            "hash1| |2025-01-01T00:00:00Z|Alice|Root commit",
        ])
        assert len(commits) == 1
        assert commits[0].parent_hashes == []


class TestParseRefs:
    def test_parse_refs_local_branch(self, sample_ref_lines):
        branches = parse_refs(sample_ref_lines)
        assert len(branches) == 4
        main_branch = [b for b in branches if b.name == "main"][0]
        assert main_branch.kind == "local"
        assert main_branch.tip_hash == "d4e5f6789012345678901234567890abcd123"

    def test_parse_refs_remote(self, sample_ref_lines):
        branches = parse_refs(sample_ref_lines)
        remote = [b for b in branches if b.kind == "remote"][0]
        assert remote.name == "origin/main"

    def test_parse_refs_tag(self, sample_ref_lines):
        branches = parse_refs(sample_ref_lines)
        tags = [b for b in branches if b.kind == "tag"]
        assert len(tags) == 1
        assert tags[0].name == "v1.0"

    def test_parse_refs_empty(self):
        branches = parse_refs([])
        assert branches == []

    def test_parse_refs_malformed(self):
        branches = parse_refs(["incomplete"])
        assert branches == []


class TestBuildDAG:
    def test_build_dag_creates_lookup(self, sample_commit_lines):
        commits = parse_commits(sample_commit_lines)
        commit_map = build_dag(commits)
        assert len(commit_map) == 4
        assert "a1b2c3d4e5f6789012345678901234567890abc" in commit_map

    def test_children_are_populated(self, sample_commit_lines):
        commits = parse_commits(sample_commit_lines)
        commit_map = build_dag(commits)
        root = commit_map["a1b2c3d4e5f6789012345678901234567890abc"]
        assert len(root.children) == 2

    def test_empty_commits(self):
        commit_map = build_dag([])
        assert commit_map == {}


class TestAssignBranchLabels:
    def test_labels_are_assigned(self, sample_commit_lines, sample_ref_lines):
        commits = parse_commits(sample_commit_lines)
        commit_map = build_dag(commits)
        branches = parse_refs(sample_ref_lines)
        assign_branch_labels(commits, commit_map, branches)

        # The merge commit should have "main" label
        merge_commit = commits[3]
        assert "main" in merge_commit.branches


class TestMarkRefs:
    def test_tag_refs_marked(self, sample_commit_lines, sample_ref_lines):
        commits = parse_commits(sample_commit_lines)
        commit_map = build_dag(commits)
        branches = parse_refs(sample_ref_lines)
        mark_refs(commits, commit_map, branches)

        # The commit c3d... should have v1.0 tag
        tagged = commit_map["c3d4e5f6789012345678901234567890abcd12"]
        assert "v1.0" in tagged.refs
