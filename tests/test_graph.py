"""Determinism, immutability, referential-integrity, and coverage tests for the graph layer."""

from __future__ import annotations

import dataclasses
from collections import Counter

import networkx as nx
import pytest

from banking_fraud_lab import (
    EDGE_CATEGORY_IDS,
    EDGE_SPECS,
    EDGE_TYPE_IDS,
    NODE_SPECS,
    NODE_TYPE_IDS,
    EdgeSpec,
    NodeSpec,
    build_banking_graph,
    generate_minimal_banking_world,
)
from banking_fraud_lab.graph import DEVICE_NODE, DETECTION_PATTERN_NODE

# PRD-listed node types. The session node is an additive representation of the
# login/session relationship; the eleven PRD node types are the required floor.
PRD_NODE_TYPES = {
    "partner",
    "client",
    "user",
    "banking_relationship",
    "account",
    "beneficiary",
    "device",
    "transaction",
    "alert",
    "case",
    "detection_pattern",
}

# The nine PRD-listed edge categories.
PRD_EDGE_CATEGORIES = {
    "ownership",
    "authorization",
    "login_session",
    "payment",
    "counterparty",
    "shared_device",
    "alert",
    "case",
    "scenario",
}

# Glossary display-name terms that must appear verbatim in the node catalog.
GLOSSARY_NODE_DISPLAY_NAMES = {"Partner", "Client", "User", "Banking relationship"}

# Edge-type -> category lookup derived from the frozen catalog.
EDGE_CATEGORY_BY_TYPE: dict[str, str] = {spec.edge_type: spec.category for spec in EDGE_SPECS}


def test_build_returns_multidigraph(tiny_banking_graph: nx.MultiDiGraph) -> None:
    """The builder must return a NetworkX MultiDiGraph."""
    assert isinstance(tiny_banking_graph, nx.MultiDiGraph)


def test_graph_is_deterministic_across_seeded_runs() -> None:
    """Repeated seed-42 tiny runs must produce identical node and edge structure."""
    first_tables = generate_minimal_banking_world(seed=42, scale="tiny")
    second_tables = generate_minimal_banking_world(seed=42, scale="tiny")
    first_graph = build_banking_graph(first_tables)
    second_graph = build_banking_graph(second_tables)

    assert first_graph.number_of_nodes() == second_graph.number_of_nodes()
    assert first_graph.number_of_edges() == second_graph.number_of_edges()
    assert set(first_graph.nodes()) == set(second_graph.nodes())

    def edge_signature(
        graph: nx.MultiDiGraph,
    ) -> Counter[tuple[object, object, str]]:
        # A Counter (multiset) preserves parallel-edge multiplicity, which a set
        # would collapse on a MultiDiGraph.
        return Counter(
            (source, target, data["edge_type"])
            for source, target, data in graph.edges(data=True)
        )

    assert edge_signature(first_graph) == edge_signature(second_graph)


def test_graph_contains_every_prd_node_type(tiny_banking_graph: nx.MultiDiGraph) -> None:
    """Every PRD-listed node type must be present in the tiny graph."""
    node_types = {data["node_type"] for _, data in tiny_banking_graph.nodes(data=True)}
    missing = PRD_NODE_TYPES - node_types
    assert not missing, f"Missing PRD node types: {sorted(missing)}"


def test_graph_covers_every_edge_category(tiny_banking_graph: nx.MultiDiGraph) -> None:
    """Every PRD-listed edge category must appear in the tiny graph."""
    edge_categories = {EDGE_CATEGORY_BY_TYPE[data["edge_type"]] for _, _, data in tiny_banking_graph.edges(data=True)}
    missing = PRD_EDGE_CATEGORIES - edge_categories
    assert not missing, f"Missing PRD edge categories: {sorted(missing)}"


def test_every_edge_references_existing_nodes(tiny_banking_graph: nx.MultiDiGraph) -> None:
    """Edge endpoints must always reference nodes that exist in the graph."""
    nodes = set(tiny_banking_graph.nodes())
    dangling = [
        (source, target)
        for source, target in tiny_banking_graph.edges()
        if source not in nodes or target not in nodes
    ]
    assert not dangling, f"Edges reference missing nodes: {dangling[:5]}"


def test_no_degenerate_self_loops(tiny_banking_graph: nx.MultiDiGraph) -> None:
    """No typed edge should connect a node to itself."""
    self_loops = [(u, v) for u, v in tiny_banking_graph.edges() if u == v]
    assert not self_loops, f"Found self-loop edges: {self_loops[:5]}"


def test_nodes_carry_node_type_attribute(tiny_banking_graph: nx.MultiDiGraph) -> None:
    """Every node must carry a node_type attribute matching its key prefix."""
    for (node_type, _key_value), data in tiny_banking_graph.nodes(data=True):
        assert data["node_type"] == node_type


def test_edges_carry_edge_type_attribute(tiny_banking_graph: nx.MultiDiGraph) -> None:
    """Every edge must carry an edge_type drawn from the frozen vocabulary."""
    for _source, _target, data in tiny_banking_graph.edges(data=True):
        assert data["edge_type"] in set(EDGE_TYPE_IDS)


@pytest.mark.parametrize("spec_class", [NodeSpec, EdgeSpec])
def test_convention_dataclasses_are_frozen(spec_class: type) -> None:
    """NodeSpec and EdgeSpec must be frozen dataclasses."""
    assert dataclasses.is_dataclass(spec_class)
    assert hasattr(spec_class, "__dataclass_params__")
    assert spec_class.__dataclass_params__.frozen is True


def test_node_spec_instance_is_immutable() -> None:
    """A NodeSpec instance must reject field assignment."""
    spec = NODE_SPECS[0]
    with pytest.raises(dataclasses.FrozenInstanceError):
        spec.node_type = "mutated"  # type: ignore[misc]


def test_edge_spec_instance_is_immutable() -> None:
    """An EdgeSpec instance must reject field assignment."""
    spec = EDGE_SPECS[0]
    with pytest.raises(dataclasses.FrozenInstanceError):
        spec.edge_type = "mutated"  # type: ignore[misc]


def test_node_type_ids_are_unique_and_complete() -> None:
    """NODE_TYPE_IDS must be unique and cover the PRD node vocabulary."""
    assert len(NODE_TYPE_IDS) == len(set(NODE_TYPE_IDS))
    assert PRD_NODE_TYPES <= set(NODE_TYPE_IDS)


def test_edge_type_ids_are_unique() -> None:
    """EDGE_TYPE_IDS must be unique."""
    assert len(EDGE_TYPE_IDS) == len(set(EDGE_TYPE_IDS))


def test_edge_categories_are_unique_and_complete() -> None:
    """EDGE_CATEGORY_IDS must be unique and cover the PRD edge categories."""
    assert len(EDGE_CATEGORY_IDS) == len(set(EDGE_CATEGORY_IDS))
    assert PRD_EDGE_CATEGORIES <= set(EDGE_CATEGORY_IDS)


def test_glossary_display_names_appear_in_node_catalog() -> None:
    """The glossary node display-name terms must appear verbatim in NODE_SPECS."""
    display_names = {spec.display_name for spec in NODE_SPECS}
    missing = GLOSSARY_NODE_DISPLAY_NAMES - display_names
    assert not missing, f"Missing glossary display names: {sorted(missing)}"


def test_device_node_documented_as_derived_from_sessions() -> None:
    """The device node must be documented as derived from session fingerprints."""
    assert DEVICE_NODE.source_table == "sessions"
    assert DEVICE_NODE.key_column == "device_fingerprint_hash"


def test_detection_pattern_node_documented_as_vocabulary_derived() -> None:
    """The Detection pattern node must derive from the frozen vocabulary, not a table."""
    assert DETECTION_PATTERN_NODE.key_column == "pattern_id"


def test_every_edge_spec_endpoints_are_known_node_types() -> None:
    """Every edge spec must connect node types present in NODE_TYPE_IDS."""
    node_types = set(NODE_TYPE_IDS)
    for spec in EDGE_SPECS:
        assert spec.source_node_type in node_types, f"{spec.edge_type} source unknown"
        assert spec.target_node_type in node_types, f"{spec.edge_type} target unknown"
