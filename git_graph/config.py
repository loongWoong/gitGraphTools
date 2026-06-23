"""Configuration management for git-graph.

All tunable thresholds, weights, and defaults are centralized here.
Can be overridden via a JSON config file passed with ``--config``.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Config:
    """Runtime configuration for git-graph.

    All fields have sensible defaults.  Override via a JSON file.
    """

    # ── Bus Factor ──────────────────────────────────────────────────
    bus_factor_threshold_pct: float = 80.0    # dominant author % to trigger warning
    bus_factor_min_commits: int = 5           # minimum commits per file to analyze
    bus_factor_top_n: int = 10                # max warnings to return

    # ── Health Scoring Weights ──────────────────────────────────────
    health_weights: dict = field(default_factory=lambda: {
        "main":    {"recency": 5,  "divergence": 20, "merged": 0,  "unique": 20, "lifetime": 0},
        "develop": {"recency": 10, "divergence": 15, "merged": 0,  "unique": 20, "lifetime": 0},
        "release": {"recency": 10, "divergence": 15, "merged": 0,  "unique": 15, "lifetime": 10},
        "hotfix":  {"recency": 20, "divergence": 5,  "merged": 25, "unique": 5,  "lifetime": 15},
        "feature": {"recency": 25, "divergence": 15, "merged": 20, "unique": 10, "lifetime": 15},
        "other":   {"recency": 20, "divergence": 15, "merged": 15, "unique": 10, "lifetime": 15},
    })

    # ── Recency Thresholds (days) ───────────────────────────────────
    recency_good_days: dict = field(default_factory=lambda: {
        "main": 30, "develop": 30, "release": 90, "hotfix": 7, "feature": 30, "other": 30,
    })

    # ── Lifetime Limits (days) ──────────────────────────────────────
    lifetime_limits: dict = field(default_factory=lambda: {
        "hotfix": 7, "feature": 60, "release": 180, "other": 90,
    })

    # ── Zombie Detection Thresholds ─────────────────────────────────
    zombie_merged_days: int = 60      # merged + no activity > N days → zombie_merged
    zombie_abandoned_days: int = 90   # unmerged + no activity > N days → zombie_abandoned
    zombie_abandoned_behind: int = 50 # also requires behind main > N commits

    # ── Risk Detection ──────────────────────────────────────────────
    pulse_inactive_days: int = 14     # no activity > N days → risk
    pulse_long_lived_days: int = 60   # lifetime > N days → risk
    pulse_behind_warn: int = 50       # behind main > N commits → risk

    # ── I18n ────────────────────────────────────────────────────────
    lang: str = "en"                  # "en" or "zh"

    # ── Output ──────────────────────────────────────────────────────
    default_output: str = "git_graph.html"
    default_port: int = 8765

    # ── Sprint Analyzer ─────────────────────────────────────────────
    sprint_days: int = 14              # default sprint length

    # ── PR Detection ────────────────────────────────────────────────
    merge_commit_patterns: list[str] = field(default_factory=lambda: [
        "Merge branch '", "Merge pull request #",
    ])

    def to_json_dict(self) -> dict:
        """Serialize to a JSON-compatible dict."""
        return {
            "bus_factor_threshold_pct": self.bus_factor_threshold_pct,
            "bus_factor_min_commits": self.bus_factor_min_commits,
            "bus_factor_top_n": self.bus_factor_top_n,
            "health_weights": self.health_weights,
            "recency_good_days": self.recency_good_days,
            "lifetime_limits": self.lifetime_limits,
            "zombie_merged_days": self.zombie_merged_days,
            "zombie_abandoned_days": self.zombie_abandoned_days,
            "zombie_abandoned_behind": self.zombie_abandoned_behind,
            "pulse_inactive_days": self.pulse_inactive_days,
            "pulse_long_lived_days": self.pulse_long_lived_days,
            "pulse_behind_warn": self.pulse_behind_warn,
            "lang": self.lang,
            "default_output": self.default_output,
            "default_port": self.default_port,
            "sprint_days": self.sprint_days,
            "merge_commit_patterns": self.merge_commit_patterns,
        }


def load_config(config_path: Optional[str] = None) -> Config:
    """Load configuration, optionally merging a JSON file over defaults.

    Args:
        config_path: Path to a JSON config file.  None = use defaults.

    Returns:
        A Config instance.
    """
    config = Config()

    if config_path:
        import json
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                overrides = json.load(f)
            _merge_overrides(config, overrides)
        except FileNotFoundError:
            import sys
            print(f"Warning: config file '{config_path}' not found, using defaults.", file=sys.stderr)
        except json.JSONDecodeError as e:
            import sys
            print(f"Warning: invalid JSON in config file: {e}, using defaults.", file=sys.stderr)

    return config


def _merge_overrides(config: Config, overrides: dict) -> None:
    """Apply JSON overrides to a Config instance in-place."""
    # Simple scalar fields
    for field_name in [
        "bus_factor_threshold_pct", "bus_factor_min_commits", "bus_factor_top_n",
        "zombie_merged_days", "zombie_abandoned_days", "zombie_abandoned_behind",
        "pulse_inactive_days", "pulse_long_lived_days", "pulse_behind_warn",
        "lang", "default_output", "default_port", "sprint_days",
    ]:
        if field_name in overrides:
            setattr(config, field_name, overrides[field_name])

    # Dict fields — merge rather than replace
    for field_name in ["health_weights", "recency_good_days", "lifetime_limits"]:
        if field_name in overrides:
            existing = getattr(config, field_name)
            existing.update(overrides[field_name])

    # List fields
    if "merge_commit_patterns" in overrides:
        config.merge_commit_patterns = overrides["merge_commit_patterns"]
