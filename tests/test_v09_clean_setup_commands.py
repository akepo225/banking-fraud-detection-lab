"""Clean-setup command validation for the v0.9 beta (issue #231).

Proves the beta is reproducible: the commands the beta checklist and
troubleshooting doc claim "work from a clean setup" actually run, and the CI
commands the checklist references match the canonical gate manifest. Reuses the
CI quality-gate meta-test pattern from tests/test_ci_quality_gates.py.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
BETA_CHECKLIST = REPO_ROOT / "docs" / "release" / "v0.9-beta-checklist.md"
TROUBLESHOOTING = REPO_ROOT / "docs" / "capstone" / "troubleshooting.md"
CI_WORKFLOW = REPO_ROOT / ".github" / "workflows" / "ci.yml"

CANONICAL_CI_COMMANDS = (
    "uv sync --extra dev",
    "uv run ruff check .",
    "uv run pytest",
)


def test_beta_checklist_references_canonical_ci_commands() -> None:
    """The beta checklist must reference the fixed CI commands, not redefine them."""
    text = BETA_CHECKLIST.read_text(encoding="utf-8")
    for command in CANONICAL_CI_COMMANDS:
        assert command in text, f"beta checklist missing canonical CI command {command!r}"


def test_beta_checklist_does_not_redefine_ci_commands() -> None:
    """Where the checklist names the canonical CI commands, they must match CI exactly.

    The checklist may document additional *manual* learner commands (e.g. the
    capstone CLI), but anywhere it references the three fixed CI commands it must
    not alter or filter them.
    """
    workflow = yaml.safe_load(CI_WORKFLOW.read_text(encoding="utf-8"))
    ci_run_commands = tuple(
        step["run"].strip() for step in workflow["jobs"]["test"]["steps"] if "run" in step
    )
    assert ci_run_commands == CANONICAL_CI_COMMANDS
    checklist_text = BETA_CHECKLIST.read_text(encoding="utf-8")
    for command in CANONICAL_CI_COMMANDS:
        assert command in checklist_text, (
            f"beta checklist must reference the fixed CI command {command!r}"
        )
    forbidden_filters = (" -k ", " -m ", " --ignore", " --deselect")
    pytest_line = next(
        line for line in checklist_text.splitlines() if "uv run pytest" in line
    )
    assert not any(f in pytest_line for f in forbidden_filters), (
        f"beta checklist filters the pytest command: {pytest_line!r}"
    )


def test_beta_checklist_carries_hitl_marker_and_beta_framing() -> None:
    """The beta checklist is a maintainer artifact, not a publication announcement."""
    text = BETA_CHECKLIST.read_text(encoding="utf-8")
    assert "<!-- HITL-REVIEW-REQUIRED" in text
    assert "Status: accepted for v0.9 beta with bounded v1.0 follow-ups." in text
    assert "Final Beta Decision" in text
    assert "beta" in text.lower()
    assert "private" in text.lower()
    for banned in ("we shipped", "publicly released", "is now published"):
        assert banned not in text.lower(), f"beta checklist uses banned phrase {banned!r}"


def test_troubleshooting_doc_covers_common_failures() -> None:
    """The troubleshooting doc covers the common setup/execution failures learners hit."""
    text = TROUBLESHOOTING.read_text(encoding="utf-8").lower()
    required_topics = (
        "uv",            # uv install / sync
        "notebook",      # notebook execution
        "sqlite",        # SQLite loading
        "protected",     # protected-key confusion
        "scale",         # scale-profile selection
    )
    for topic in required_topics:
        assert topic in text, f"troubleshooting doc missing common-failure topic {topic!r}"


def test_documented_capstone_cli_command_runs(tmp_path: Path) -> None:
    """The capstone CLI command documented in the beta checklist runs from a clean setup."""
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "banking_fraud_lab.capstone",
            "--track",
            "both",
            "--seed",
            "42",
            "--scale",
            "tiny",
            "--learner-facing",
            "--output",
            str(tmp_path),
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    for track in ("private_banking", "digital_banking"):
        track_dir = tmp_path / track
        assert track_dir.is_dir()
        assert any(track_dir.glob("*.csv")), f"no CSVs generated for {track} track"
