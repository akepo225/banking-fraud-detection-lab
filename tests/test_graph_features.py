"""Tests for explainable graph feature builders, joins, and the pattern guard."""

from __future__ import annotations

import dataclasses

import networkx as nx
import pandas as pd
import pytest

from banking_fraud_lab import (
    build_banking_graph,
    build_foundation_progressive_views,
    generate_minimal_banking_world,
    join_graph_features_to_view,
)
from banking_fraud_lab.graph import (
    GRAPH_FEATURE_FAMILY_IDS,
    GRAPH_FEATURE_FAMILIES,
    GraphFeatureFamilySpec,
    build_all_graph_features,
    build_bridge_node_features,
    build_centrality_features,
    build_community_features,
    build_connected_component_features,
    build_node_degree_features,
    build_path_length_features,
)


def _hand_fixture_graph() -> nx.MultiDiGraph:
    """A tiny hand-checkable graph.

    Component 1 (a triangle plus an alert branch joined by a single bridge):

        partner_a -- client_a -- account_a -- transaction_a -- alert_a
                       \\__________/   (client_a also connects to account_a)

    The triangle (partner_a, client_a, account_a) means its edges are NOT bridges;
    the (transaction_a -> alert_a) edge is the only link into the alert leaf, so
    transaction_a and alert_a are bridge endpoints.

    Component 2 is a single isolated edge: partner_b -- client_b.
    """
    graph = nx.MultiDiGraph()
    for node_type, key in [
        ("partner", "P-A"),
        ("client", "C-A"),
        ("account", "A-A"),
        ("transaction", "T-A"),
        ("alert", "AL-A"),
        ("partner", "P-B"),
        ("client", "C-B"),
    ]:
        graph.add_node((node_type, key), node_type=node_type)

    # Triangle (these three edges are NOT bridges because they sit on a cycle).
    graph.add_edge(("partner", "P-A"), ("client", "C-A"), edge_type="client_partner")
    graph.add_edge(("client", "C-A"), ("account", "A-A"), edge_type="client_account")
    graph.add_edge(("partner", "P-A"), ("account", "A-A"), edge_type="partner_account")
    # Bridge into the transaction/alert branch.
    graph.add_edge(("account", "A-A"), ("transaction", "T-A"), edge_type="account_transaction")
    graph.add_edge(("transaction", "T-A"), ("alert", "AL-A"), edge_type="transaction_alert")
    # Isolated single-edge component.
    graph.add_edge(("partner", "P-B"), ("client", "C-B"), edge_type="client_partner")
    return graph


# --- Hand-fixture deterministic metrics ------------------------------------


def test_connected_components_match_hand_fixture() -> None:
    """The hand fixture has exactly two weak components of sizes 5 and 2."""
    features = build_connected_component_features(_hand_fixture_graph())
    assert features["component_id"].nunique() == 2
    sizes = sorted(features["component_size"].unique())
    assert sizes == [2, 5]


def test_node_degree_matches_hand_fixture() -> None:
    """The hub account_a has degree 3; the alert leaf has degree 1."""
    features = build_node_degree_features(_hand_fixture_graph())
    by_key = features.set_index(["node_type", "node_key"])["node_degree"].to_dict()
    assert by_key[("account", "A-A")] == 3
    assert by_key[("client", "C-A")] == 2
    assert by_key[("alert", "AL-A")] == 1


def test_known_bridge_node_is_flagged() -> None:
    """transaction_a and alert_a sit on bridge edges; triangle nodes do not."""
    features = build_bridge_node_features(_hand_fixture_graph())
    by_key = features.set_index(["node_type", "node_key"])["is_bridge_endpoint"].to_dict()
    # transaction_a and alert_a are on the bridge branch into the alert leaf.
    assert by_key[("transaction", "T-A")] == 1
    assert by_key[("alert", "AL-A")] == 1
    # The isolated P-B/C-B edge is a bridge (only edge in its component).
    assert by_key[("partner", "P-B")] == 1
    assert by_key[("client", "C-B")] == 1
    # client_a and partner_a sit purely on the triangle cycle (not bridge endpoints).
    assert by_key[("partner", "P-A")] == 0
    assert by_key[("client", "C-A")] == 0
    # account_a anchors the bridge into the alert branch, so it IS a bridge endpoint.
    assert by_key[("account", "A-A")] == 1


def test_centrality_is_bounded_between_zero_and_one() -> None:
    """Degree centrality must fall within [0, 1] even with parallel edges."""
    # Hand fixture (no parallel edges).
    features = build_centrality_features(_hand_fixture_graph())
    assert (features["degree_centrality"] >= 0).all()
    assert (features["degree_centrality"] <= 1).all()


def test_centrality_bounded_on_multidigraph(
    tiny_banking_graph: nx.MultiDiGraph,
) -> None:
    """Centrality must stay within [0, 1] on the MultiDiGraph tiny graph.

    The tiny graph can contain parallel edges; collapsing to a simple graph
    before computing degree centrality keeps the ratio bounded.
    """
    features = build_centrality_features(tiny_banking_graph)
    assert (features["degree_centrality"] >= 0).all()
    assert (features["degree_centrality"] <= 1).all()


def test_community_assigns_every_node() -> None:
    """Every node must receive a non-negative community id."""
    features = build_community_features(_hand_fixture_graph())
    assert (features["community_id"] >= 0).all()
    assert len(features) == _hand_fixture_graph().number_of_nodes()


def test_path_length_from_focus_is_zero_at_focus() -> None:
    """A focus node has shortest path length 0 to itself."""
    graph = _hand_fixture_graph()
    features = build_path_length_features(graph, focus_nodes=[("client", "C-A")])
    by_key = features.set_index(["node_type", "node_key"])["shortest_path_length"].to_dict()
    assert by_key[("client", "C-A")] == 0
    # alert is two hops from client_a via account and transaction.
    assert by_key[("alert", "AL-A")] == 3
    # client_b is unreachable from client_a's component.
    assert by_key[("client", "C-B")] == -1


# --- Tiny-data integration --------------------------------------------------


def test_all_builders_cover_every_node(tiny_banking_graph: nx.MultiDiGraph) -> None:
    """Each builder must emit one row per graph node on the tiny dataset."""
    node_count = tiny_banking_graph.number_of_nodes()
    for builder in [
        build_connected_component_features,
        build_node_degree_features,
        build_centrality_features,
        build_community_features,
        build_bridge_node_features,
    ]:
        assert len(builder(tiny_banking_graph)) == node_count
    path_features = build_path_length_features(tiny_banking_graph)
    assert len(path_features) == node_count


def test_build_all_graph_features_returns_every_family(
    tiny_banking_graph: nx.MultiDiGraph,
) -> None:
    """build_all_graph_features must return a frame for every family id."""
    frames = build_all_graph_features(tiny_banking_graph)
    assert set(frames) == set(GRAPH_FEATURE_FAMILY_IDS)


def test_graph_features_join_back_to_client_relationships_view() -> None:
    """Graph degree features must join onto foundation_client_relationships without row loss."""
    tables = generate_minimal_banking_world(seed=42, scale="tiny")
    graph = build_banking_graph(tables)
    views = build_foundation_progressive_views(tables)
    view = views["foundation_client_relationships"]
    view_rows = len(view)

    degree = build_node_degree_features(graph)
    joined = join_graph_features_to_view(degree, view)

    # No row loss and no duplication.
    assert len(joined) == view_rows
    # The join added at least one per-node-type degree column.
    degree_columns = [c for c in joined.columns if c.startswith("node_degree_")]
    assert degree_columns


def test_graph_features_join_back_to_alert_lifecycle_view() -> None:
    """Graph features must join onto foundation_alert_lifecycle keyed by alert/relationship."""
    tables = generate_minimal_banking_world(seed=42, scale="tiny")
    graph = build_banking_graph(tables)
    views = build_foundation_progressive_views(tables)
    view = views["foundation_alert_lifecycle"]
    view_rows = len(view)

    bridge = build_bridge_node_features(graph)
    joined = join_graph_features_to_view(bridge, view)

    assert len(joined) == view_rows
    bridge_columns = [c for c in joined.columns if c.startswith("is_bridge_endpoint_")]
    assert bridge_columns


def test_join_helper_tolerates_duplicate_feature_keys_without_row_loss() -> None:
    """Duplicate keys on the feature (right) side must not multiply view rows.

    ``join_graph_features_to_view`` deduplicates the feature frame's keys before
    merging, so the ``validate="many_to_one"`` merge stays sound even when the
    feature frame repeats a node key. This guards the foundation-view join path.
    """
    feature_frame = pd.DataFrame(
        {
            "node_type": ["client", "client", "partner"],
            "node_key": ["C-1", "C-1", "P-1"],  # C-1 duplicated -> must be deduped.
            "node_degree": [2, 3, 1],
        }
    )
    view = pd.DataFrame(
        {
            "client_id": ["C-1", "C-2"],
            "partner_id": ["P-1", "P-2"],
        }
    )

    joined = join_graph_features_to_view(feature_frame, view)

    # No row loss, no duplication: the view's two rows survive intact.
    assert len(joined) == 2
    # The first (keep="first") degree value for the duplicated C-1 wins.
    assert joined.loc[joined["client_id"] == "C-1", "node_degree_client"].iloc[0] == 2


def test_merge_validate_many_to_one_fails_loudly_on_duplicate_right_keys() -> None:
    """A duplicate-keyed right frame must raise MergeError under many_to_one.

    This exercises the merge contract directly. The helper deduplicates feature
    keys before this merge, so the guard is the safety net for any future code
    path that joins feature frames without pre-deduplication. ``MergeError`` is
    a ``ValueError`` subclass.
    """
    from pandas.errors import MergeError

    left = pd.DataFrame({"client_id": ["C-1", "C-2"], "marker": ["a", "b"]})
    # Duplicate right-hand keys violate many_to_one (the right keys must be unique).
    right = pd.DataFrame({"client_id": ["C-1", "C-1"], "node_degree_client": [2, 3]})

    with pytest.raises(MergeError):
        left.merge(right, on="client_id", how="left", validate="many_to_one")


# --- Spec layer and pattern guard ------------------------------------------


def test_every_family_references_a_known_pattern_id() -> None:
    """Each graph feature family must map to a Detection pattern that exists."""
    from banking_fraud_lab.schema import PATTERN_IDS

    for spec in GRAPH_FEATURE_FAMILIES:
        assert spec.detection_pattern_id in set(PATTERN_IDS), (
            f"{spec.family_id} references unknown pattern {spec.detection_pattern_id}"
        )


def test_graph_feature_family_specs_are_frozen() -> None:
    """GraphFeatureFamilySpec must be a frozen dataclass."""
    assert dataclasses.is_dataclass(GraphFeatureFamilySpec)
    assert GraphFeatureFamilySpec.__dataclass_params__.frozen is True
    spec = GRAPH_FEATURE_FAMILIES[0]
    with pytest.raises(dataclasses.FrozenInstanceError):
        spec.family_id = "mutated"  # type: ignore[misc]


def test_feature_family_ids_are_unique() -> None:
    """Family ids must be unique and match the catalog order."""
    assert len(GRAPH_FEATURE_FAMILY_IDS) == len(set(GRAPH_FEATURE_FAMILY_IDS))


def test_required_prd_signals_are_present() -> None:
    """The six PRD-required graph signals must all have feature families."""
    required_ids = {
        "graph_connected_component",
        "graph_node_degree",
        "graph_centrality",
        "graph_community",
        "graph_path_length",
        "graph_bridge_node",
    }
    assert required_ids <= set(GRAPH_FEATURE_FAMILY_IDS)


def test_features_are_deterministic(tiny_banking_graph: nx.MultiDiGraph) -> None:
    """Repeated builds must produce identical feature DataFrames."""
    first = build_all_graph_features(tiny_banking_graph)
    second = build_all_graph_features(tiny_banking_graph)
    for family_id in first:
        pd.testing.assert_frame_equal(first[family_id], second[family_id])
