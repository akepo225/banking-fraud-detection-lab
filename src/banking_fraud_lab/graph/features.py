"""Explainable graph feature builders and Progressive-view join helper."""

from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping

import networkx as nx
import pandas as pd

from banking_fraud_lab.graph.features_spec import (
    GRAPH_FEATURE_FAMILIES,
)

# Default per-node-type identifier columns used when joining graph features back
# to a tabular Progressive data view. Each maps a graph node type to the column
# name a Progressive view exposes for that entity.
NODE_TYPE_TO_VIEW_COLUMN: dict[str, str] = {
    "partner": "partner_id",
    "client": "client_id",
    "user": "user_id",
    "banking_relationship": "banking_relationship_id",
    "account": "account_id",
    "beneficiary": "payment_beneficiary_id",
    "transaction": "transaction_id",
    "alert": "alert_id",
    "case": "case_id",
    "session": "session_id",
    "device": "device_fingerprint_hash",
}


def _node_rows(graph: nx.MultiDiGraph) -> list[dict[str, object]]:
    """Flatten graph nodes into one dict row per node keyed by type and value."""
    rows: list[dict[str, object]] = []
    for (node_type, key_value), data in graph.nodes(data=True):
        rows.append(
            {
                "node_type": data.get("node_type", node_type),
                "node_key": key_value,
            }
        )
    return rows


def _base_node_frame(graph: nx.MultiDiGraph) -> pd.DataFrame:
    """Return a DataFrame with one stable row per graph node."""
    return pd.DataFrame(_node_rows(graph), columns=["node_type", "node_key"])


def build_connected_component_features(graph: nx.MultiDiGraph) -> pd.DataFrame:
    """Compute weakly-connected component membership for every node.

    Each node is labelled with a stable component id (the enumeration index of
    its weakly-connected component) and the component size, so analysts can size
    relationship clusters and isolate ring-shaped sub-networks.
    """
    undirected = nx.MultiGraph(graph)
    component_of: dict[tuple[str, object], int] = {}
    component_size: dict[int, int] = {}
    for index, component in enumerate(nx.connected_components(undirected)):
        for node in component:
            component_of[node] = index
        component_size[index] = len(component)

    base = _base_node_frame(graph)
    base["component_id"] = [component_of[node] for node in graph.nodes()]
    base["component_size"] = [component_size[cid] for cid in base["component_id"]]
    return base.sort_values(["component_id", "node_type", "node_key"], kind="stable").reset_index(
        drop=True
    )


def build_node_degree_features(graph: nx.MultiDiGraph) -> pd.DataFrame:
    """Count each node's direct relationships (degree)."""
    base = _base_node_frame(graph)
    base["node_degree"] = [graph.degree(node) for node in graph.nodes()]
    return base.sort_values(["node_type", "node_key"], kind="stable").reset_index(drop=True)


def build_centrality_features(graph: nx.MultiDiGraph) -> pd.DataFrame:
    """Compute degree centrality for every node.

    Centrality is computed on a collapsed simple graph so parallel edges do not
    inflate a node's degree above its true number of distinct neighbours.
    """
    base = _base_node_frame(graph)
    simple = nx.Graph()
    simple.add_nodes_from(graph.nodes(data=True))
    for source, target, data in graph.edges(data=True):
        simple.add_edge(source, target, **data)
    denominator = max(len(simple) - 1, 1)
    base["degree_centrality"] = [simple.degree(node) / denominator for node in graph.nodes()]
    return base.sort_values(["node_type", "node_key"], kind="stable").reset_index(drop=True)


def build_community_features(graph: nx.MultiDiGraph) -> pd.DataFrame:
    """Assign each node to a greedy-modularity community."""
    base = _base_node_frame(graph)
    simple = nx.Graph()
    simple.add_nodes_from(graph.nodes(data=True))
    for source, target, data in graph.edges(data=True):
        simple.add_edge(source, target, **data)
    communities = nx.community.greedy_modularity_communities(simple)
    community_of: dict[tuple[str, object], int] = {}
    for index, community in enumerate(communities):
        for node in community:
            community_of[node] = index
    base["community_id"] = [
        community_of.get(node, -1) for node in graph.nodes()
    ]
    return base.sort_values(["community_id", "node_type", "node_key"], kind="stable").reset_index(
        drop=True
    )


def build_path_length_features(
    graph: nx.MultiDiGraph,
    *,
    focus_nodes: Iterable[tuple[str, object]] | None = None,
) -> pd.DataFrame:
    """Measure shortest-path length from one or more focus nodes.

    Args:
        graph: The banking graph.
        focus_nodes: Optional iterable of node ids to measure from. When more
            than one is given, each node's shortest distance to the nearest
            focus node is reported. Defaults to the first node in the graph.

    The output reports, for each node, the nearest focus node's type and the
    shortest-path length (0 for the focus nodes themselves).
    """
    if len(graph) == 0:
        return pd.DataFrame(columns=["node_type", "node_key", "nearest_node_type", "shortest_path_length"])

    if focus_nodes is None:
        focus_nodes = [next(iter(graph.nodes()))]
    focus_list = list(focus_nodes)

    simple = nx.Graph()
    simple.add_nodes_from(graph.nodes(data=True))
    for source, target, data in graph.edges(data=True):
        simple.add_edge(source, target, **data)

    nearest_type: dict[tuple[str, object], str] = {}
    nearest_length: dict[tuple[str, object], float] = {}
    for focus in focus_list:
        if focus not in simple:
            continue
        lengths = nx.single_source_shortest_path_length(simple, focus)
        for node, length in lengths.items():
            if node not in nearest_length or length < nearest_length[node]:
                nearest_length[node] = length
                nearest_type[node] = graph.nodes[focus].get("node_type", focus[0])

    base = _base_node_frame(graph)
    base["nearest_node_type"] = [
        nearest_type.get(node, "") for node in graph.nodes()
    ]
    base["shortest_path_length"] = [
        nearest_length.get(node, -1) for node in graph.nodes()
    ]
    return base.sort_values(["shortest_path_length", "node_type", "node_key"], kind="stable").reset_index(
        drop=True
    )


def build_bridge_node_features(graph: nx.MultiDiGraph) -> pd.DataFrame:
    """Flag nodes that sit on bridge edges.

    A bridge edge is one whose removal would disconnect the network; its
    endpoints are single points through which funds pass between otherwise
    separate clusters.
    """
    base = _base_node_frame(graph)
    simple = nx.Graph()
    simple.add_nodes_from(graph.nodes(data=True))
    for source, target, data in graph.edges(data=True):
        simple.add_edge(source, target, **data)
    bridge_endpoints: set[tuple[str, object]] = set()
    for source, target in nx.bridges(simple):
        bridge_endpoints.add(source)
        bridge_endpoints.add(target)
    base["is_bridge_endpoint"] = [
        int(node in bridge_endpoints) for node in graph.nodes()
    ]
    return base.sort_values(["node_type", "node_key"], kind="stable").reset_index(drop=True)


# Map each graph feature family id to its builder. PATH_LENGTH takes an extra
# focus-nodes argument, so it is handled by callers directly.
GRAPH_FEATURE_BUILDERS: Mapping[str, Callable[[nx.MultiDiGraph], pd.DataFrame]] = {
    "graph_connected_component": build_connected_component_features,
    "graph_node_degree": build_node_degree_features,
    "graph_centrality": build_centrality_features,
    "graph_community": build_community_features,
    "graph_bridge_node": build_bridge_node_features,
}


def build_all_graph_features(
    graph: nx.MultiDiGraph,
    *,
    focus_nodes: Iterable[tuple[str, object]] | None = None,
) -> dict[str, pd.DataFrame]:
    """Build every graph feature family into a dict keyed by family id.

    Args:
        graph: The banking graph.
        focus_nodes: Optional focus nodes forwarded to the path-length builder.

    Returns:
        A mapping of family id to its feature DataFrame.
    """
    frames: dict[str, pd.DataFrame] = {}
    for spec in GRAPH_FEATURE_FAMILIES:
        if spec.family_id == "graph_path_length":
            frames[spec.family_id] = build_path_length_features(graph, focus_nodes=focus_nodes)
        else:
            builder = GRAPH_FEATURE_BUILDERS[spec.family_id]
            frames[spec.family_id] = builder(graph)
    return frames


def join_graph_features_to_view(
    feature_frame: pd.DataFrame,
    view: pd.DataFrame,
    *,
    node_types: Iterable[str] | None = None,
) -> pd.DataFrame:
    """Join graph features back onto a tabular Progressive data view.

    The join is performed per node type: for each node type whose view column is
    present, the feature rows of that node type are merged onto the view keyed by
    that column. Node types without a matching view column are skipped. The
    result carries one row per original view row plus the feature columns.

    Args:
        feature_frame: A graph feature DataFrame with ``node_type``,
            ``node_key`` and feature columns.
        view: A tabular Progressive data view (e.g.
            ``foundation_client_relationships`` or ``foundation_alert_lifecycle``).
        node_types: Optional override of which node types to join. Defaults to
            every node type in :data:`NODE_TYPE_TO_VIEW_COLUMN` whose view column
            exists in ``view``.

    Returns:
        The view augmented with the feature columns (left join, no row loss).
    """
    feature_columns = [
        column
        for column in feature_frame.columns
        if column not in {"node_type", "node_key"}
    ]
    candidate_types = list(node_types) if node_types else list(NODE_TYPE_TO_VIEW_COLUMN)

    result = view
    for node_type in candidate_types:
        column = NODE_TYPE_TO_VIEW_COLUMN.get(node_type)
        if column is None or column not in view.columns:
            continue
        sub = feature_frame[feature_frame["node_type"] == node_type]
        if sub.empty:
            continue
        renamed = sub.rename(columns={"node_key": column})[
            [column, *feature_columns]
        ]
        # Drop duplicate keys defensively so the merge stays one-to-many at worst.
        renamed = renamed.drop_duplicates(subset=[column], keep="first")
        suffixed = {col: f"{col}_{node_type}" for col in feature_columns}
        result = result.merge(
            renamed.rename(columns=suffixed),
            on=column,
            how="left",
        )
    return result


__all__ = [
    "GRAPH_FEATURE_BUILDERS",
    "NODE_TYPE_TO_VIEW_COLUMN",
    "build_all_graph_features",
    "build_bridge_node_features",
    "build_centrality_features",
    "build_community_features",
    "build_connected_component_features",
    "build_node_degree_features",
    "build_path_length_features",
    "join_graph_features_to_view",
]
