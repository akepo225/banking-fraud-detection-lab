"""Optional Neo4j export path for the banking graph (non-core, optional extra).

This module is deliberately **optional**. It serializes the ``MultiDiGraph``
produced by :func:`banking_fraud_lab.graph.build_banking_graph` into
Neo4j-ingestible artifacts (a Cypher script and ``LOAD CSV`` input files) that a
learner can run against a local Neo4j instance. It never requires a live
database for the serialization helpers.

The Neo4j Python driver is an optional dependency declared behind the ``neo4j``
extra in ``pyproject.toml``. ``uv sync --extra dev`` and CI do not install it.
All driver imports are guarded so ``import banking_fraud_lab.graph`` succeeds
when the driver is absent. The optional :func:`push_graph_to_neo4j` helper
degrades gracefully (raising a clear ``RuntimeError`` with install guidance)
when the driver is not installed.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import networkx as nx
import pandas as pd

NEO4J_DRIVER_AVAILABLE = False
try:  # pragma: no cover - exercised only when the optional driver is installed
    from neo4j import GraphDatabase  # type: ignore[import-not-found]

    NEO4J_DRIVER_AVAILABLE = True
except ImportError:  # pragma: no cover - the default environment lacks the driver
    GraphDatabase = None  # type: ignore[assignment]


def _node_label(node_type: str) -> str:
    """Map a frozen node-type id to a CamelCase Neo4j label."""
    return "".join(part.capitalize() for part in node_type.split("_"))


def _edge_type(edge_type: str) -> str:
    """Map a frozen edge-type id to an UPPER_SNAKE Neo4j relationship type."""
    return edge_type.upper()


def _escape_cypher_string(value: object) -> str:
    """Escape a value for inclusion in a Cypher single-quoted string literal."""
    if pd.isna(value):
        return ""
    return str(value).replace("\\", "\\\\").replace("'", "\\'")


def _node_key_value(node_id: tuple[str, object]) -> str:
    """Render the key value portion of a node id as a stable Cypher-safe token."""
    _node_type, key_value = node_id
    return _escape_cypher_string(key_value)


def export_graph_to_cypher(graph: nx.MultiDiGraph) -> str:
    """Serialize a banking graph to a runnable Cypher script (no driver needed).

    The script creates one node per graph node (labelled by node type, keyed by
    its key value) and one relationship per graph edge (typed by edge type). The
    output is a plain string a learner can paste into Neo4j Browser or ``cypher-shell``.

    Args:
        graph: The ``MultiDiGraph`` returned by ``build_banking_graph``.

    Returns:
        A newline-delimited Cypher script as a string.
    """
    lines: list[str] = ["// Auto-generated Neo4j Cypher export of the banking graph."]

    # Nodes: one MERGE per node so re-running the script is idempotent.
    for node_id, data in graph.nodes(data=True):
        node_type = data.get("node_type", "node")
        label = _node_label(node_type)
        key_value = _node_key_value(node_id)
        lines.append(
            f"MERGE (n:{label} {{node_type: '{node_type}', key: '{key_value}'}});"
        )

    # Edges: MATCH the two endpoints and MERGE the typed relationship.
    for source, target, edge_data in graph.edges(data=True):
        edge_type = edge_data.get("edge_type", "edge")
        source_label = _node_label(graph.nodes[source].get("node_type", "node"))
        target_label = _node_label(graph.nodes[target].get("node_type", "node"))
        source_key = _node_key_value(source)
        target_key = _node_key_value(target)
        rel_type = _edge_type(edge_type)
        lines.append(
            f"MATCH (a:{source_label} {{key: '{source_key}'}}), "
            f"(b:{target_label} {{key: '{target_key}'}}) "
            f"MERGE (a)-[:{rel_type}]->(b);"
        )

    return "\n".join(lines) + "\n"


def export_graph_to_neo4j_csvs(
    graph: nx.MultiDiGraph,
    output_dir: str | Path,
) -> dict[str, Path]:
    """Write the banking graph to Neo4j ``LOAD CSV`` input files (no driver needed).

    Produces ``nodes.csv`` (one row per node) and ``edges.csv`` (one row per
    edge), suitable for Neo4j's ``LOAD CSV WITH HEADERS`` ingest.

    Args:
        graph: The ``MultiDiGraph`` returned by ``build_banking_graph``.
        output_dir: Directory to write the CSV files into. Created if absent.

    Returns:
        A mapping of artifact name to written file path (``nodes`` and ``edges``).
    """
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    nodes_path = out / "nodes.csv"
    edges_path = out / "edges.csv"

    node_rows: list[dict[str, Any]] = []
    for node_id, data in graph.nodes(data=True):
        node_type = data.get("node_type", "node")
        _node_type, key_value = node_id
        node_rows.append({"node_type": node_type, "key": "" if pd.isna(key_value) else key_value})

    edge_rows: list[dict[str, Any]] = []
    for source, target, edge_data in graph.edges(data=True):
        edge_type = edge_data.get("edge_type", "edge")
        source_key = _node_key_value(source)
        target_key = _node_key_value(target)
        edge_rows.append(
            {
                "edge_type": edge_type,
                "source_node_type": graph.nodes[source].get("node_type", "node"),
                "source_key": source_key,
                "target_node_type": graph.nodes[target].get("node_type", "node"),
                "target_key": target_key,
            }
        )

    pd.DataFrame(node_rows, columns=["node_type", "key"]).to_csv(
        nodes_path, index=False, encoding="utf-8"
    )
    pd.DataFrame(
        edge_rows,
        columns=["edge_type", "source_node_type", "source_key", "target_node_type", "target_key"],
    ).to_csv(edges_path, index=False, encoding="utf-8")

    return {"nodes": nodes_path, "edges": edges_path}


def push_graph_to_neo4j(
    graph: nx.MultiDiGraph,
    uri: str,
    *,
    auth: tuple[str, str] | None = None,
    database: str | None = None,
) -> int:
    """Optionally push the banking graph to a live Neo4j database.

    This helper requires the optional ``neo4j`` extra (``uv sync --extra neo4j``).
    It degrades gracefully when the driver is absent by raising a clear
    ``RuntimeError`` with install guidance, so the core learner path never breaks.

    Args:
        graph: The ``MultiDiGraph`` returned by ``build_banking_graph``.
        uri: Neo4j connection URI (e.g. ``bolt://localhost:7687``).
        auth: Optional ``(username, password)`` tuple.
        database: Optional target database name.

    Returns:
        The number of relationships created.

    Raises:
        RuntimeError: If the optional Neo4j driver is not installed.
    """
    if not NEO4J_DRIVER_AVAILABLE:  # pragma: no cover - default env lacks the driver
        raise RuntimeError(
            "The optional Neo4j driver is not installed. Install it with "
            "'uv sync --extra neo4j' before calling push_graph_to_neo4j()."
        )

    cypher = export_graph_to_cypher(graph)
    relationship_count = graph.number_of_edges()

    driver = GraphDatabase.driver(uri, auth=auth)  # type: ignore[union-attr]
    try:  # pragma: no cover - requires a live database
        with driver.session(database=database) as session:
            for statement in cypher.splitlines():
                statement = statement.strip()
                if statement and not statement.startswith("//"):
                    session.run(statement)
    finally:  # pragma: no cover - requires a live database
        driver.close()

    return relationship_count


__all__ = [
    "NEO4J_DRIVER_AVAILABLE",
    "export_graph_to_cypher",
    "export_graph_to_neo4j_csvs",
    "push_graph_to_neo4j",
]
