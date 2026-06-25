"""v0.6 acceptance-review and cross-version regression tests."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import networkx as nx
import pytest

from banking_fraud_lab import (
    GRAPH_FEATURE_FAMILIES,
    NODE_SPECS,
    build_all_graph_features,
    build_banking_graph,
    build_foundation_progressive_views,
    generate_minimal_banking_world,
    join_graph_features_to_view,
)

ROOT = Path(__file__).resolve().parents[1]
REVIEW_PATH = ROOT / "docs" / "release" / "v0.6-graph-acceptance-review.md"
PYPROJECT_PATH = ROOT / "pyproject.toml"
NOTEBOOKS_README = ROOT / "notebooks" / "README.md"


def _pyproject_text() -> str:
    return PYPROJECT_PATH.read_text(encoding="utf-8")


# --- Core graph-module presence -------------------------------------------


def test_graph_module_is_importable() -> None:
    """The v0.6 graph module must be importable from the package root."""
    import banking_fraud_lab.graph  # noqa: F401

    assert NODE_SPECS, "NODE_SPECS catalog must be non-empty"


def test_networkx_is_a_required_dependency() -> None:
    """networkx must be a required (non-optional) core dependency."""
    text = _pyproject_text()
    # networkx appears in the required dependencies array.
    dependencies_start = text.index("dependencies = [")
    dependencies_end = text.index("]", dependencies_start)
    dependencies_block = text[dependencies_start:dependencies_end]
    assert "networkx" in dependencies_block, "networkx missing from required dependencies"


def test_neo4j_is_optional_and_outside_dev() -> None:
    """neo4j must live only behind an optional extra, not in core or dev."""
    text = _pyproject_text()
    # The optional neo4j extra exists.
    assert 'neo4j = [' in text, "optional neo4j extra missing"
    # neo4j is NOT in the core dependencies block.
    dependencies_start = text.index("dependencies = [")
    dependencies_end = text.index("]", dependencies_start)
    dependencies_block = text[dependencies_start:dependencies_end]
    assert "neo4j" not in dependencies_block, "neo4j must not be a core dependency"
    # neo4j is NOT in the dev block.
    dev_start = text.index("dev = [")
    dev_end = text.index("]", dev_start)
    dev_block = text[dev_start:dev_end]
    assert "neo4j" not in dev_block, "neo4j must not be a dev dependency"


def test_neo4j_driver_not_imported_eagerly() -> None:
    """Importing the graph package must not require the optional Neo4j driver."""
    import banking_fraud_lab.graph

    # The package exposes the availability flag and import succeeded regardless.
    assert hasattr(banking_fraud_lab.graph, "NEO4J_DRIVER_AVAILABLE")


# --- New graph-native pattern IDs -----------------------------------------


def test_graph_native_pattern_ids_are_registered() -> None:
    """The v0.6 graph-native Detection pattern IDs must be in the registry."""
    from banking_fraud_lab.schema import PATTERN_IDS

    ids = set(PATTERN_IDS)
    assert "mule_ring" in ids
    assert "circular_funds_movement" in ids


def test_graph_feature_families_reference_known_patterns() -> None:
    """Every graph feature family must reference a Detection pattern in the registry."""
    from banking_fraud_lab.schema import PATTERN_IDS

    ids = set(PATTERN_IDS)
    for spec in GRAPH_FEATURE_FAMILIES:
        assert spec.detection_pattern_id in ids, (
            f"{spec.family_id} references unknown pattern {spec.detection_pattern_id}"
        )


# --- Progressive-view joins ------------------------------------------------


def test_graph_features_join_to_foundation_views() -> None:
    """Graph degree features must join onto both foundation Progressive views."""
    tables = generate_minimal_banking_world(seed=42, scale="tiny")
    graph = build_banking_graph(tables)
    views = build_foundation_progressive_views(tables)
    degree = build_all_graph_features(graph)["graph_node_degree"]

    for view_name in ("foundation_client_relationships", "foundation_alert_lifecycle"):
        view = views[view_name]
        joined = join_graph_features_to_view(degree, view)
        # Left join: no row loss.
        assert len(joined) == len(view), f"{view_name} lost rows in graph-feature join"


# --- No separate graph dataset --------------------------------------------


def test_graph_builds_from_canonical_tables_without_separate_dataset() -> None:
    """Graph construction must derive purely from canonical generated tables."""
    tables = generate_minimal_banking_world(seed=42, scale="tiny")
    graph = build_banking_graph(tables)
    assert isinstance(graph, nx.MultiDiGraph)
    assert graph.number_of_nodes() > 0
    assert graph.number_of_edges() > 0
    # The builder writes nothing to disk: only the in-memory graph is produced.
    # (A regression would be a committed graph dataset file, which the tree must not have.)
    graph_data_dirs = [ROOT / "data" / "graph", ROOT / "data" / "network"]
    assert not any(path.exists() for path in graph_data_dirs), (
        "Graph construction must not produce a separate committed graph dataset"
    )


# --- v0.6 notebooks linked -------------------------------------------------


def test_v06_notebooks_linked_from_notebooks_readme() -> None:
    """The v0.6 graph module must be placed in the learner path."""
    text = NOTEBOOKS_README.read_text(encoding="utf-8")
    assert "06_graph_network_fraud" in text
    assert "alpine_crest_graph_investigation.ipynb" in text
    assert "novabank_graph_investigation.ipynb" in text


# --- Cross-version regression: v0.3 / v0.4 / v0.5 notebooks still covered ---


V03_V04_V05_NOTEBOOK_TEST_MODULES = (
    "test_private_banking_notebook",          # v0.3 private-banking baseline
    "test_digital_scam_to_mule_notebook",     # v0.4 digital-banking baseline
    "test_alert_governance_notebook",         # v0.5 alert governance
    "test_private_banking_feature_engineering_notebook",  # v0.3/v0.4 feature engineering
    "test_digital_feature_engineering_notebook",
)


@pytest.mark.parametrize("module_name", V03_V04_V05_NOTEBOOK_TEST_MODULES)
def test_v03_v04_v05_notebook_regression_modules_exist(module_name: str) -> None:
    """Each v0.3/v0.4/v0.5 notebook smoke test must still be present.

    The graph additions must not regress the prior tracks. These modules execute
    the prior-version notebooks end-to-end on tiny data and are exercised by the
    full ``uv run pytest`` suite.
    """
    module_path = ROOT / "tests" / f"{module_name}.py"
    assert module_path.is_file(), f"v0.3/v0.4/v0.5 regression module missing: {module_path}"


def test_v03_v04_v05_notebook_test_modules_are_collectable() -> None:
    """The v0.3/v0.4/v0.5 notebook test modules must be importable (collectable).

    A broken import would silently drop cross-version notebook coverage from the
    suite even if the files exist.
    """
    for module_name in V03_V04_V05_NOTEBOOK_TEST_MODULES:
        assert importlib.util.find_spec(module_name) is not None, (
            f"notebook regression module not collectable: {module_name}"
        )


# --- Acceptance review artifact -------------------------------------------


def test_v06_acceptance_review_has_hitl_boundary_and_evidence() -> None:
    """The v0.6 review must state HITL status and link PRD deliverable evidence."""
    review = REVIEW_PATH.read_text(encoding="utf-8")

    required_terms = [
        "Status: draft for human review.",
        "<!-- HITL-REVIEW-REQUIRED:",
        "uv sync --extra dev",
        "uv run ruff check .",
        "uv run pytest",
        "networkx",
        "mule_ring",
        "circular_funds_movement",
    ]
    for term in required_terms:
        assert term in review, f"v0.6 acceptance review missing term: {term!r}"
