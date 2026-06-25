"""Tests for package-level imports and version."""

from banking_fraud_lab import (
    DEFAULT_FP_SEGMENT_COLUMNS,
    EDGE_CATEGORY_IDS,
    EDGE_SPECS,
    EDGE_TYPE_IDS,
    EXPLANATION_FAMILY_IDS,
    EXPLANATION_FAMILY_SPECS,
    FEATURE_FAMILY_IDS,
    FOUNDATION_PROGRESSIVE_VIEW_SPECS,
    GRAPH_FEATURE_FAMILIES,
    GRAPH_FEATURE_FAMILY_IDS,
    MODEL_DOCUMENTATION_SECTIONS,
    MODEL_DOCUMENTATION_SECTION_IDS,
    MONITORING_CHECKLIST_DIMENSIONS,
    MONITORING_CHECKLIST_DIMENSION_IDS,
    NODE_SPECS,
    NODE_TYPE_IDS,
    PRIVATE_BANKING_FEATURE_FAMILIES,
    DatasetQualityReport,
    EdgeSpec,
    ExplanationFamilySpec,
    FeatureFamilySpec,
    GraphFeatureFamilySpec,
    ModelDocumentationSectionSpec,
    MonitoringChecklistDimensionSpec,
    NodeSpec,
    ProgressiveViewSpec,
    __version__,
    build_all_graph_features,
    build_banking_graph,
    build_bridge_node_features,
    build_centrality_features,
    build_community_features,
    build_connected_component_features,
    build_model_documentation,
    build_monitoring_checklist,
    build_node_degree_features,
    build_path_length_features,
    build_partial_dependence_grid,
    build_learner_facing_views,
    build_foundation_progressive_views,
    build_private_banking_features,
    calculate_amount_to_aum_features,
    calculate_amount_to_baseline_features,
    calculate_cross_border_features,
    calculate_new_counterparty_features,
    calculate_off_hours_features,
    calculate_rm_concentration_features,
    calculate_velocity_features,
    concentrate_false_positives,
    create_minimal_banking_world_sqlite,
    evaluate_alert_scores,
    recommend_lowest_cost_threshold,
    explain_feature_family,
    extract_feature_importance,
    generate_dataset_quality_report,
    generate_digital_scam_to_mule_world,
    generate_learner_facing_digital_scam_to_mule_world,
    generate_learner_facing_private_banking_transaction_fraud_world,
    generate_learner_facing_minimal_banking_world,
    generate_minimal_banking_world,
    generate_private_banking_transaction_fraud_world,
    inject_digital_scam_to_mule_flow,
    inject_private_banking_transaction_fraud,
    join_graph_features_to_view,
    load_tables_to_sqlite,
)


def test_package_imports() -> None:
    """The package must expose the correct version and a callable generator."""
    assert __version__ == "0.1.0"
    assert FEATURE_FAMILY_IDS
    assert FOUNDATION_PROGRESSIVE_VIEW_SPECS
    assert PRIVATE_BANKING_FEATURE_FAMILIES
    assert DatasetQualityReport
    assert FeatureFamilySpec
    assert GraphFeatureFamilySpec
    assert NodeSpec
    assert EdgeSpec
    assert ExplanationFamilySpec
    assert ModelDocumentationSectionSpec
    assert MonitoringChecklistDimensionSpec
    assert ProgressiveViewSpec
    assert EDGE_CATEGORY_IDS
    assert EDGE_SPECS
    assert EDGE_TYPE_IDS
    assert GRAPH_FEATURE_FAMILIES
    assert GRAPH_FEATURE_FAMILY_IDS
    assert EXPLANATION_FAMILY_IDS
    assert EXPLANATION_FAMILY_SPECS
    assert MODEL_DOCUMENTATION_SECTIONS
    assert MODEL_DOCUMENTATION_SECTION_IDS
    assert MONITORING_CHECKLIST_DIMENSIONS
    assert MONITORING_CHECKLIST_DIMENSION_IDS
    assert NODE_SPECS
    assert NODE_TYPE_IDS
    assert callable(generate_minimal_banking_world)
    assert callable(build_all_graph_features)
    assert callable(build_banking_graph)
    assert callable(build_bridge_node_features)
    assert callable(build_centrality_features)
    assert callable(build_community_features)
    assert callable(build_connected_component_features)
    assert callable(build_node_degree_features)
    assert callable(build_path_length_features)
    assert callable(build_partial_dependence_grid)
    assert callable(extract_feature_importance)
    assert callable(explain_feature_family)
    assert callable(build_model_documentation)
    assert callable(build_monitoring_checklist)
    assert callable(join_graph_features_to_view)
    assert callable(build_learner_facing_views)
    assert callable(build_foundation_progressive_views)
    assert callable(build_private_banking_features)
    assert callable(calculate_amount_to_aum_features)
    assert callable(calculate_amount_to_baseline_features)
    assert callable(calculate_cross_border_features)
    assert callable(calculate_new_counterparty_features)
    assert callable(calculate_off_hours_features)
    assert callable(calculate_rm_concentration_features)
    assert callable(calculate_velocity_features)
    assert callable(generate_digital_scam_to_mule_world)
    assert callable(generate_learner_facing_digital_scam_to_mule_world)
    assert callable(generate_learner_facing_private_banking_transaction_fraud_world)
    assert callable(generate_learner_facing_minimal_banking_world)
    assert callable(create_minimal_banking_world_sqlite)
    assert callable(generate_private_banking_transaction_fraud_world)
    assert callable(inject_digital_scam_to_mule_flow)
    assert callable(inject_private_banking_transaction_fraud)
    assert callable(load_tables_to_sqlite)
    assert callable(evaluate_alert_scores)
    assert callable(concentrate_false_positives)
    assert callable(recommend_lowest_cost_threshold)
    assert DEFAULT_FP_SEGMENT_COLUMNS
    assert callable(generate_dataset_quality_report)
