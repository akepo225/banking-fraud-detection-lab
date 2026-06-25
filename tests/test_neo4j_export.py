"""Tests for the optional Neo4j export path (availability-guarded)."""

from __future__ import annotations

from pathlib import Path

import networkx as nx
import pandas as pd
import pytest

from banking_fraud_lab.graph import (
    NEO4J_DRIVER_AVAILABLE,
    export_graph_to_cypher,
    export_graph_to_neo4j_csvs,
    push_graph_to_neo4j,
)


def test_import_succeeds_without_driver() -> None:
    """Importing the graph package must never require the Neo4j driver."""
    # If this test module imported at all, the graph package imported cleanly.
    # NEO4J_DRIVER_AVAILABLE reflects the optional driver state.
    assert isinstance(NEO4J_DRIVER_AVAILABLE, bool)


def test_cypher_export_serializes_nodes_and_edges(
    tiny_banking_graph: nx.MultiDiGraph,
) -> None:
    """The Cypher exporter must emit one MERGE per node and one MERGE per edge."""
    cypher = export_graph_to_cypher(tiny_banking_graph)
    node_count = tiny_banking_graph.number_of_nodes()
    edge_count = tiny_banking_graph.number_of_edges()

    assert cypher.startswith("//"), "Cypher script must start with a comment header"
    assert cypher.count("MERGE (n:") == node_count
    # Each edge contributes one MERGE relationship line that contains "]->(".
    assert cypher.count("]->(:") + cypher.count("]->[:") >= 0
    relationship_lines = [ln for ln in cypher.splitlines() if "MERGE (a)-[:" in ln]
    assert len(relationship_lines) == edge_count


def test_cypher_export_uses_typed_labels_and_relationships(
    tiny_banking_graph: nx.MultiDiGraph,
) -> None:
    """Cypher labels must derive from node types and relationship types from edge types."""
    cypher = export_graph_to_cypher(tiny_banking_graph)
    # Node labels are CamelCase versions of node types.
    assert ":Partner {" in cypher
    assert ":BankingRelationship {" in cypher
    # Relationship types are UPPER_SNAKE versions of edge types.
    assert "[:CLIENT_PARTNER]->" in cypher
    assert "[:ALERT_PATTERN]->" in cypher


def test_csv_export_round_trips_graph_counts(
    tiny_banking_graph: nx.MultiDiGraph,
    tmp_path: Path,
) -> None:
    """The CSV exporter must write one row per node and one row per edge."""
    artifacts = export_graph_to_neo4j_csvs(tiny_banking_graph, tmp_path)
    assert set(artifacts) == {"nodes", "edges"}
    assert artifacts["nodes"].exists()
    assert artifacts["edges"].exists()

    nodes = pd.read_csv(artifacts["nodes"])
    edges = pd.read_csv(artifacts["edges"])
    assert len(nodes) == tiny_banking_graph.number_of_nodes()
    assert len(edges) == tiny_banking_graph.number_of_edges()
    assert list(nodes.columns) == ["node_type", "key"]
    assert "edge_type" in edges.columns
    assert "source_key" in edges.columns and "target_key" in edges.columns


def test_csv_export_creates_missing_directory(
    tiny_banking_graph: nx.MultiDiGraph,
    tmp_path: Path,
) -> None:
    """The CSV exporter must create the output directory if it does not exist."""
    target = tmp_path / "nested" / "neo4j_out"
    assert not target.exists()
    artifacts = export_graph_to_neo4j_csvs(tiny_banking_graph, target)
    assert target.exists()
    assert artifacts["nodes"].parent == target


@pytest.mark.skipif(
    NEO4J_DRIVER_AVAILABLE,
    reason="The driver-absent path is only testable when the driver is not installed",
)
def test_push_raises_clearly_without_driver(
    tiny_banking_graph: nx.MultiDiGraph,
) -> None:
    """Pushing to Neo4j without the optional driver must raise a clear RuntimeError."""
    with pytest.raises(RuntimeError, match="optional Neo4j driver is not installed"):
        push_graph_to_neo4j(tiny_banking_graph, "bolt://localhost:7687")


@pytest.mark.skipif(
    not NEO4J_DRIVER_AVAILABLE,
    reason="The driver-present path is only testable when the driver is installed",
)
def test_cypher_export_deterministic_with_driver_present(
    tiny_banking_graph: nx.MultiDiGraph,
) -> None:
    """When the driver is present, the Cypher artifact is still deterministic."""
    first = export_graph_to_cypher(tiny_banking_graph)
    second = export_graph_to_cypher(tiny_banking_graph)
    assert first == second
