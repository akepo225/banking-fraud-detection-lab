"""Tests that keep the Dependabot configuration for pinned GitHub Actions explicit.

Mirrors the approach in ``tests/test_ci_quality_gates.py``: parse the config
file directly and assert the structural expectations from issue #132 so that
the "config validates" acceptance criterion is checked in CI rather than only
at merge time.
"""

from __future__ import annotations

from pathlib import Path

import yaml


REPO_ROOT = Path(__file__).resolve().parents[1]
DEPENDABOT_PATH = REPO_ROOT / ".github" / "dependabot.yml"

# Ecosystems explicitly out of scope for issue #132. Listing them here guards
# against future scope drift (e.g. someone adding a ``pip`` entry by mistake).
# Note: ``github-actions`` is the one in-scope ecosystem and is asserted separately.
OUT_OF_SCOPE_ECOSYSTEMS = frozenset(
    {
        "pip",
        "uv",
        "npm",
        "gomod",
        "cargo",
        "composer",
        "nuget",
        "docker",
        "terraform",
        "maven",
        "gradle",
        "devcontainers",
    }
)


def _load_dependabot_config() -> dict:
    """Parse the Dependabot config and return it as a dict."""
    return yaml.safe_load(DEPENDABOT_PATH.read_text(encoding="utf-8"))


def test_dependabot_config_targets_github_actions_only() -> None:
    """Dependabot must be enabled for github-actions and no out-of-scope ecosystem."""
    config = _load_dependabot_config()

    assert config["version"] == 2, "Dependabot config must use the version 2 schema."

    updates = config["updates"]
    assert updates, "Dependabot config must define at least one update entry."

    ecosystems = {entry["package-ecosystem"] for entry in updates}
    assert "github-actions" in ecosystems, (
        "Dependabot config must target the github-actions ecosystem."
    )

    forbidden = ecosystems & OUT_OF_SCOPE_ECOSYSTEMS
    assert not forbidden, (
        f"Dependabot config must not add out-of-scope ecosystems: {sorted(forbidden)}. "
        "Issue #132 limits scope to github-actions."
    )


def test_github_actions_entry_is_weekly_and_rooted() -> None:
    """The github-actions entry must cover the workflow directory on a weekly schedule."""
    config = _load_dependabot_config()

    github_actions_entries = [
        entry
        for entry in config["updates"]
        if entry["package-ecosystem"] == "github-actions"
    ]
    assert github_actions_entries, "Expected a github-actions update entry."

    for entry in github_actions_entries:
        assert entry["directory"] == "/", (
            "The github-actions entry must use directory '/' so Dependabot scans "
            ".github/workflows/."
        )
        assert entry["schedule"]["interval"] == "weekly", (
            "The github-actions entry must update on a weekly schedule."
        )
