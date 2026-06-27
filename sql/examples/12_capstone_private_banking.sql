-- Capstone private-banking feature extraction (Alpine Crest Private Bank).
-- Investigates the pb_high_value_movement and pb_transaction_fraud Detection
-- patterns across the capstone dataset: relationship / account / counterparty /
-- relationship-manager / velocity context for high-value debits, tied back to
-- Banking relationship, Client, and Alert lifecycle lineage.
WITH private_accounts AS (
  SELECT
    a.account_id,
    a.banking_relationship_id,
    br.primary_client_id,
    br.relationship_manager_code,
    CAST(br.aum_chf AS REAL) AS aum_chf,
    CAST(a.balance_chf AS REAL) AS account_balance_chf
  FROM accounts AS a
  JOIN banking_relationships AS br
    ON br.banking_relationship_id = a.banking_relationship_id
  WHERE a.institution_name = 'Alpine Crest Private Bank'
),
transaction_context AS (
  SELECT
    t.transaction_id,
    pa.banking_relationship_id,
    pa.primary_client_id,
    pa.relationship_manager_code,
    t.booked_at,
    t.transaction_type,
    t.direction,
    CAST(t.amount_chf AS REAL) AS amount_chf,
    pa.aum_chf,
    pa.account_balance_chf,
    t.payment_beneficiary_id
  FROM transactions AS t
  JOIN private_accounts AS pa
    ON pa.account_id = t.account_id
  WHERE t.direction = 'debit'
),
relationship_velocity AS (
  SELECT
    transaction_context.*,
    COUNT(*) OVER (
      PARTITION BY banking_relationship_id
    ) AS relationship_debit_count,
    COALESCE(
      AVG(amount_chf) OVER (
        PARTITION BY banking_relationship_id
        ORDER BY booked_at, transaction_id
        ROWS BETWEEN UNBOUNDED PRECEDING AND 1 PRECEDING
      ),
      amount_chf
    ) AS relationship_amount_baseline_chf
  FROM transaction_context
),
scenario_alerts AS (
  SELECT
    al.banking_relationship_id,
    al.triggered_transaction_id AS transaction_id,
    al.alert_id,
    al.alert_type,
    al.alert_status,
    al.severity
  FROM alerts AS al
  WHERE al.institution_name = 'Alpine Crest Private Bank'
)
SELECT
  rv.transaction_id,
  rv.banking_relationship_id,
  rv.primary_client_id AS client_id,
  rv.relationship_manager_code,
  rv.booked_at,
  rv.transaction_type,
  rv.amount_chf,
  ROUND(rv.aum_chf, 2) AS aum_chf,
  ROUND(rv.account_balance_chf, 2) AS account_balance_chf,
  rv.relationship_debit_count,
  ROUND(rv.relationship_amount_baseline_chf, 2) AS relationship_amount_baseline_chf,
  ROUND(
    CASE
      WHEN rv.aum_chf > 0 THEN rv.amount_chf / rv.aum_chf
      ELSE 0
    END,
    6
  ) AS amount_to_aum_ratio,
  ROUND(
    CASE
      WHEN rv.relationship_amount_baseline_chf > 0
      THEN rv.amount_chf / rv.relationship_amount_baseline_chf
      ELSE 0
    END,
    4
  ) AS amount_to_relationship_baseline_ratio,
  sa.alert_id,
  sa.alert_type,
  sa.alert_status,
  sa.severity AS alert_severity
FROM relationship_velocity AS rv
LEFT JOIN scenario_alerts AS sa
  ON sa.transaction_id = rv.transaction_id
ORDER BY rv.amount_chf DESC, rv.transaction_id;
