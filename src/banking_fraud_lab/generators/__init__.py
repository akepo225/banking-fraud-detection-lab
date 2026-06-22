"""Synthetic data generator entry points."""

from banking_fraud_lab.generators.digital_banking import (
    generate_digital_fraud_scenarios_world,
    generate_digital_scam_to_mule_world,
    generate_learner_facing_digital_fraud_scenarios_world,
    generate_learner_facing_digital_scam_to_mule_world,
    inject_digital_fraud_scenarios,
    inject_digital_scam_to_mule_flow,
)
from banking_fraud_lab.generators.minimal_world import (
    DEFAULT_SCALE_PROFILE,
    SCALE_PROFILES,
    DatasetScaleProfile,
    build_learner_facing_views,
    generate_learner_facing_minimal_banking_world,
    generate_minimal_banking_world,
)
from banking_fraud_lab.generators.private_banking import (
    generate_learner_facing_private_banking_transaction_fraud_world,
    generate_private_banking_transaction_fraud_world,
    inject_private_banking_transaction_fraud,
)

__all__ = [
    "DEFAULT_SCALE_PROFILE",
    "SCALE_PROFILES",
    "DatasetScaleProfile",
    "build_learner_facing_views",
    "generate_digital_fraud_scenarios_world",
    "generate_digital_scam_to_mule_world",
    "generate_learner_facing_digital_fraud_scenarios_world",
    "generate_learner_facing_digital_scam_to_mule_world",
    "generate_learner_facing_private_banking_transaction_fraud_world",
    "generate_learner_facing_minimal_banking_world",
    "generate_minimal_banking_world",
    "generate_private_banking_transaction_fraud_world",
    "inject_digital_fraud_scenarios",
    "inject_digital_scam_to_mule_flow",
    "inject_private_banking_transaction_fraud",
]
