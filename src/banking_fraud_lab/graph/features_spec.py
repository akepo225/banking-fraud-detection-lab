"""Graph-feature-family metadata mapping graph signals to Detection patterns."""

from __future__ import annotations

from dataclasses import dataclass

from banking_fraud_lab.schema import PATTERN_IDS


@dataclass(frozen=True)
class GraphFeatureFamilySpec:
    """Structured metadata for one explainable graph feature family."""

    family_id: str
    display_name: str
    description: str
    detection_pattern_id: str
    node_focus: str
    output_columns: tuple[str, ...]


CONNECTED_COMPONENT = GraphFeatureFamilySpec(
    family_id="graph_connected_component",
    display_name="Connected-component membership",
    description=(
        "Records the weakly-connected component each node belongs to so analysts "
        "can size relationship clusters and isolate ring-shaped sub-networks."
    ),
    detection_pattern_id="mule_ring",
    node_focus="any",
    output_columns=("component_id", "component_size"),
)

NODE_DEGREE = GraphFeatureFamilySpec(
    family_id="graph_node_degree",
    display_name="Node degree",
    description=(
        "Counts each node's direct relationships so highly connected Partners, "
        "Users, or beneficiaries stand out as potential hubs in a network."
    ),
    detection_pattern_id="mule_ring",
    node_focus="any",
    output_columns=("node_degree",),
)

CENTRALITY = GraphFeatureFamilySpec(
    family_id="graph_centrality",
    display_name="Degree centrality",
    description=(
        "Normalises node degree against the largest possible degree so hub "
        "Clients, Users, and Banking relationships are comparable across "
        "networks of different sizes."
    ),
    detection_pattern_id="circular_funds_movement",
    node_focus="any",
    output_columns=("degree_centrality",),
)

COMMUNITY = GraphFeatureFamilySpec(
    family_id="graph_community",
    display_name="Community membership",
    description=(
        "Assigns each node to a greedy-modularity community so funds moving "
        "through layered counterparties can be grouped into suspect clusters."
    ),
    detection_pattern_id="circular_funds_movement",
    node_focus="any",
    output_columns=("community_id",),
)

PATH_LENGTH = GraphFeatureFamilySpec(
    family_id="graph_path_length",
    display_name="Network path length",
    description=(
        "Measures shortest-path distances from a focus node so circular funds "
        "movement that returns to a starting account is visible as a short cycle."
    ),
    detection_pattern_id="circular_funds_movement",
    node_focus="any",
    output_columns=("nearest_node_type", "shortest_path_length"),
)

BRIDGE_NODE = GraphFeatureFamilySpec(
    family_id="graph_bridge_node",
    display_name="Bridge-edge endpoint (suspicious bridge node)",
    description=(
        "Flags nodes sitting on bridge edges whose removal would disconnect the "
        "network, highlighting single points through which funds pass between "
        "otherwise separate clusters."
    ),
    detection_pattern_id="circular_funds_movement",
    node_focus="any",
    output_columns=("is_bridge_endpoint",),
)

GRAPH_FEATURE_FAMILIES: tuple[GraphFeatureFamilySpec, ...] = (
    CONNECTED_COMPONENT,
    NODE_DEGREE,
    CENTRALITY,
    COMMUNITY,
    PATH_LENGTH,
    BRIDGE_NODE,
)

GRAPH_FEATURE_FAMILY_IDS: tuple[str, ...] = tuple(
    spec.family_id for spec in GRAPH_FEATURE_FAMILIES
)

# --- Module-load integrity guard -------------------------------------------
# Every graph feature family must reference a Detection pattern that exists in
# the schema vocabulary, mirroring the feature-family guard in features/specs.py.

_UNKNOWN_PATTERN_IDS = sorted(
    {spec.detection_pattern_id for spec in GRAPH_FEATURE_FAMILIES} - set(PATTERN_IDS)
)
if _UNKNOWN_PATTERN_IDS:
    raise ValueError(
        "Graph feature families reference unknown Detection pattern IDs: "
        f"{_UNKNOWN_PATTERN_IDS}"
    )


__all__ = [
    "BRIDGE_NODE",
    "CENTRALITY",
    "COMMUNITY",
    "CONNECTED_COMPONENT",
    "GRAPH_FEATURE_FAMILIES",
    "GRAPH_FEATURE_FAMILY_IDS",
    "GraphFeatureFamilySpec",
    "NODE_DEGREE",
    "PATH_LENGTH",
]
