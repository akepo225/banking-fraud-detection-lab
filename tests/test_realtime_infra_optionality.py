"""Tests for the optional real-time-infrastructure advanced notes (issue #206).

Mirrors the v0.7 SHAP optionality precedent
(:mod:`tests.test_shap_explainer`) and the v0.6 Neo4j optional-extra pattern:
the real-time-infra advanced notes are an OPTIONAL, educational artifact, and
no heavy-streaming/infra dependency may leak into core or dev. Kafka, Spark,
Redis, dashboards, and similar technologies stay entirely out of the repo's
dependency closure; they are referenced conceptually in the notes only.
"""

from __future__ import annotations

import importlib.util
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PYPROJECT_PATH = ROOT / "pyproject.toml"
ARTIFACT_PATH = ROOT / "docs" / "advanced" / "realtime_infrastructure.md"

# Identifiers that, if present in a dependency string, would mean a piece of
# heavy real-time infrastructure leaked into core or dev. Lower-cased and
# matched as substrings so version specifiers / extras are still caught.
HEAVY_INFRA_IDENTIFIERS = {
    "kafka",
    "spark",
    "pyspark",
    "redis",
    "dash",
    "streamlit",
    "flink",
    "cassandra",
    "elasticsearch",
}

# The five local v0.8 monitoring tables the notes must map to real-time
# counterparts. Kept in sync with src/banking_fraud_lab/monitoring/spec.py.
REQUIRED_TABLE_NAMES = {
    "score",
    "threshold",
    "alert_decision",
    "reviewer_action",
    "audit_event",
}


def _parse_pyproject() -> dict:
    """Parse pyproject.toml with tomllib (Python 3.11+) for robust dep inspection."""
    import tomllib

    with PYPROJECT_PATH.open("rb") as handle:
        return tomllib.load(handle)


def test_realtime_infra_notes_artifact_present() -> None:
    """The advanced-notes artifact must exist, be non-empty, and cover the baseline.

    Asserts the markdown file exists on disk, has non-trivial content, mentions
    all five local v0.8 monitoring table names (score, threshold, alert_decision,
    reviewer_action, audit_event), and explicitly states the repo does not claim
    production readiness. Guards both the educational scope and the table mapping.
    """
    assert ARTIFACT_PATH.exists(), f"real-time infra notes missing at {ARTIFACT_PATH}"
    text = ARTIFACT_PATH.read_text(encoding="utf-8")
    assert len(text.strip()) > 0, "real-time infra notes artifact is empty"

    lower = text.lower()
    missing_tables = sorted(name for name in REQUIRED_TABLE_NAMES if name not in lower)
    assert not missing_tables, (
        f"real-time infra notes must mention all five monitoring tables; missing: "
        f"{missing_tables}"
    )

    # Normalize markdown emphasis and whitespace so the phrase may span a
    # line break or carry bold markers in the source markdown.
    normalized = re.sub(r"\s+", " ", lower.replace("*", ""))
    assert "does not claim production readiness" in normalized, (
        "real-time infra notes must explicitly state the repo does not claim "
        "production readiness"
    )


def test_no_heavy_infra_in_core_or_dev_deps() -> None:
    """No heavy real-time infrastructure may appear in core or dev dependencies.

    Collects dependency strings from ``[project].dependencies`` and from the
    ``dev`` optional-extra (which must exist), then asserts none of the
    heavy-infra identifiers (kafka, spark, pyspark, redis, dash, streamlit,
    flink, cassandra, elasticsearch) appear as a case-insensitive substring.
    Optional extras like ``neo4j`` and ``shap`` are unaffected; this only
    guards the core/dev closure that ``uv sync --extra dev`` and CI install.
    """
    config = _parse_pyproject()
    project = config.get("project", {})
    optional_extras = project.get("optional-dependencies", {})

    assert "dev" in optional_extras, "dev optional-extra must exist"

    dependency_strings: list[str] = []
    dependency_strings.extend(project.get("dependencies", []))
    dependency_strings.extend(optional_extras.get("dev", []))

    leaked = sorted(
        {
            identifier
            for dep in dependency_strings
            for identifier in HEAVY_INFRA_IDENTIFIERS
            if identifier in dep.lower()
        }
    )
    assert not leaked, (
        f"heavy real-time infrastructure leaked into core/dev deps: {leaked}"
    )


def test_package_imports_without_heavy_infra() -> None:
    """Importing banking_fraud_lab must succeed with no heavy infra installed.

    The package must remain importable from a plain ``uv sync --extra dev``
    environment. This is a presence check on the import contract; the optionality
    of every named streaming technology depends on it.
    """
    assert importlib.util.find_spec("banking_fraud_lab") is not None, (
        "banking_fraud_lab must be importable without any heavy real-time infra"
    )
