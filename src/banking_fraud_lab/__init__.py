"""Banking Fraud Detection Lab package."""

from banking_fraud_lab.evaluation import evaluate_alert_scores
from banking_fraud_lab.generators import (
    build_learner_facing_views,
    generate_digital_scam_to_mule_world,
    generate_learner_facing_digital_scam_to_mule_world,
    generate_learner_facing_private_banking_transaction_fraud_world,
    generate_learner_facing_minimal_banking_world,
    generate_minimal_banking_world,
    generate_private_banking_transaction_fraud_world,
    inject_digital_scam_to_mule_flow,
    inject_private_banking_transaction_fraud,
)
from banking_fraud_lab.sqlite_loader import (
    create_minimal_banking_world_sqlite,
    load_tables_to_sqlite,
)

__all__ = [
    "__version__",
    "build_learner_facing_views",
    "create_minimal_banking_world_sqlite",
    "evaluate_alert_scores",
    "generate_digital_scam_to_mule_world",
    "generate_learner_facing_digital_scam_to_mule_world",
    "generate_learner_facing_private_banking_transaction_fraud_world",
    "generate_learner_facing_minimal_banking_world",
    "generate_minimal_banking_world",
    "generate_private_banking_transaction_fraud_world",
    "inject_digital_scam_to_mule_flow",
    "inject_private_banking_transaction_fraud",
    "load_tables_to_sqlite",
]

__version__ = "0.1.0"
