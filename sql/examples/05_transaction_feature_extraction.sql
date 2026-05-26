-- Feature extraction using canonical tables plus foundation Progressive data views.
WITH alert_flags AS (
  SELECT
    transaction_id,
    COUNT(DISTINCT alert_id) AS alert_count
  FROM foundation_alert_lifecycle
  WHERE alert_id IS NOT NULL
  GROUP BY transaction_id
),
transaction_context AS (
  SELECT
    transactions.transaction_id,
    fcr.client_id,
    fcr.client_segment,
    fcr.risk_rating,
    fcr.banking_relationship_id,
    accounts.account_id,
    transactions.booked_at,
    transactions.channel,
    transactions.direction,
    CAST(transactions.amount_chf AS REAL) AS amount_chf,
    CASE
      WHEN transactions.payment_beneficiary_id IS NULL THEN 0
      ELSE 1
    END AS uses_saved_beneficiary,
    COALESCE(alert_flags.alert_count, 0) AS lifecycle_alert_count
  FROM transactions
  JOIN accounts
    ON accounts.account_id = transactions.account_id
  JOIN foundation_client_relationships AS fcr
    ON fcr.banking_relationship_id = accounts.banking_relationship_id
  LEFT JOIN alert_flags
    ON alert_flags.transaction_id = transactions.transaction_id
)
SELECT
  transaction_id,
  client_id,
  client_segment,
  risk_rating,
  banking_relationship_id,
  account_id,
  booked_at,
  channel,
  direction,
  amount_chf,
  COUNT(*) OVER (
    PARTITION BY banking_relationship_id
  ) AS relationship_transaction_count,
  ROUND(
    SUM(amount_chf) OVER (
      PARTITION BY banking_relationship_id
    ),
    2
  ) AS relationship_total_amount_chf,
  ROUND(
    AVG(amount_chf) OVER (
      PARTITION BY banking_relationship_id
    ),
    2
  ) AS relationship_average_amount_chf,
  uses_saved_beneficiary,
  lifecycle_alert_count,
  CASE
    WHEN amount_chf >= 50000 THEN 1
    ELSE 0
  END AS high_value_feature
FROM transaction_context
ORDER BY booked_at, transaction_id;
