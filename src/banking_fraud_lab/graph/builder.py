"""Deterministic builder that turns canonical generated tables into a graph."""

from __future__ import annotations

import networkx as nx
import pandas as pd

from banking_fraud_lab.graph.conventions import (
    ALERT,
    ALERT_PATTERN,
    DETECTION_PATTERN,
    DEVICE,
    EDGE_SPECS,
    NODE_SPECS,
)
from banking_fraud_lab.schema import (
    ACTIVITY_TYPE_TO_PATTERN,
    ALERTS,
    FOUNDATION_DETECTION_PATTERNS,
    SUSPICIOUS_ACTIVITIES,
)


def _node_key(node_type: str, key_value: object) -> tuple[str, object]:
    """Build a collision-free node identifier from a node type and key value."""
    return (node_type, key_value)


def _add_table_nodes(
    graph: nx.MultiDiGraph,
    node_type: str,
    key_column: str,
    table: pd.DataFrame,
) -> None:
    """Add one node per distinct key value found in a generated table column."""
    for value in table[key_column].tolist():
        # Skip null/NA keys so no phantom nodes (e.g. (device, NaN)) are added.
        if pd.isna(value):
            continue
        node_id = _node_key(node_type, value)
        if not graph.has_node(node_id):
            graph.add_node(node_id, node_type=node_type)


def _add_table_driven_edges(
    graph: nx.MultiDiGraph,
    edge_type: str,
    source_node_type: str,
    target_node_type: str,
    source_key_column: str,
    target_key_column: str,
    table: pd.DataFrame,
) -> None:
    """Add one typed edge per row, skipping rows with a null source or target key."""
    for row in table.itertuples(index=False):
        source_value = getattr(row, source_key_column)
        target_value = getattr(row, target_key_column)
        # Skip nullable foreign keys so no phantom edges are created.
        if pd.isna(source_value) or pd.isna(target_value):
            continue
        source_id = _node_key(source_node_type, source_value)
        target_id = _node_key(target_node_type, target_value)
        graph.add_edge(source_id, target_id, edge_type=edge_type)


def build_banking_graph(tables: dict[str, pd.DataFrame]) -> nx.MultiDiGraph:
    """Build a deterministic NetworkX graph purely from canonical generated tables.

    The graph is derived entirely from the passed-in ``tables`` dict (the shape
    returned by ``generate_minimal_banking_world(...)``). No separate graph-only
    dataset is produced and nothing is written to disk. Node and edge types follow
    the frozen conventions in :mod:`banking_fraud_lab.graph.conventions`.

    Node identifiers are ``(node_type, key_value)`` tuples so node types never
    collide even when they share key values. Edges are added by iterating the
    edge catalog and each source table in row order so the output is stable
    across repeated seeded runs.

    Args:
        tables: Mapping of canonical generated table name to its DataFrame. Only
            the tables referenced by the node/edge conventions are read; missing
            tables are skipped so partial inputs do not raise.

    Returns:
        A ``networkx.MultiDiGraph`` whose nodes carry a ``node_type`` attribute
        and whose edges carry an ``edge_type`` attribute.
    """
    graph: nx.MultiDiGraph = nx.MultiDiGraph()

    # Nodes: iterate the node catalog in a stable order. Detection pattern nodes
    # derive from the frozen schema vocabulary; device nodes derive from distinct
    # session fingerprints; all other nodes derive from a generated table.
    for spec in NODE_SPECS:
        if spec.node_type == DETECTION_PATTERN:
            for pattern in FOUNDATION_DETECTION_PATTERNS:
                node_id = _node_key(DETECTION_PATTERN, pattern.pattern_id)
                if not graph.has_node(node_id):
                    graph.add_node(node_id, node_type=DETECTION_PATTERN)
            continue
        table = tables.get(spec.source_table)
        if table is None or spec.key_column not in table.columns:
            continue
        if spec.node_type == DEVICE:
            # Devices have no dedicated table: one node per distinct fingerprint.
            fingerprints = (
                pd.Series(table[spec.key_column]).dropna().drop_duplicates().tolist()
            )
            for value in fingerprints:
                node_id = _node_key(DEVICE, value)
                if not graph.has_node(node_id):
                    graph.add_node(node_id, node_type=DEVICE)
        else:
            _add_table_nodes(graph, spec.node_type, spec.key_column, table)

    # Edges: iterate the edge catalog in a stable order. The ALERT_PATTERN edge is
    # derived because the pattern key does not live on the alerts table; the rest
    # are driven directly by foreign-key columns in their source table.
    for spec in EDGE_SPECS:
        if spec.edge_type == ALERT_PATTERN.edge_type:
            _add_alert_pattern_edges(graph, tables)
            continue
        table = tables.get(spec.source_table)
        if table is None:
            continue
        # Skip partial inputs whose table is missing a required edge column so
        # the builder degrades gracefully instead of raising at row iteration.
        required_columns = {spec.source_key_column, spec.target_key_column}
        if not required_columns.issubset(table.columns):
            continue
        _add_table_driven_edges(
            graph,
            edge_type=spec.edge_type,
            source_node_type=spec.source_node_type,
            target_node_type=spec.target_node_type,
            source_key_column=spec.source_key_column,
            target_key_column=spec.target_key_column,
            table=table,
        )

    return graph


def _add_alert_pattern_edges(graph: nx.MultiDiGraph, tables: dict[str, pd.DataFrame]) -> None:
    """Add scenario edges linking alerts to Detection patterns.

    The pattern key is not stored on the alerts table, so each alert's
    suspicious activity is resolved and its activity type mapped to a pattern
    through the activity-type vocabulary. Alerts whose activity type is not in
    the vocabulary are skipped.
    """
    alerts = tables.get(ALERTS)
    suspicious = tables.get(SUSPICIOUS_ACTIVITIES)
    if alerts is None or suspicious is None:
        return
    activity_by_id = dict(
        zip(
            suspicious["suspicious_activity_id"].tolist(),
            suspicious["activity_type"].tolist(),
            strict=True,
        )
    )
    for row in alerts.itertuples(index=False):
        activity_id = row.suspicious_activity_id
        activity_type = activity_by_id.get(activity_id)
        if activity_type is None:
            continue
        pattern_id = ACTIVITY_TYPE_TO_PATTERN.get(activity_type)
        if pattern_id is None:
            continue
        source_id = _node_key(ALERT, row.alert_id)
        target_id = _node_key(DETECTION_PATTERN, pattern_id)
        graph.add_edge(source_id, target_id, edge_type=ALERT_PATTERN.edge_type)


__all__ = ["build_banking_graph"]
