-- Private-banking value features for pb_high_value_movement.
-- Demonstrates amount-to-AUM and amount-to-relationship-baseline ratios for
-- Alpine Crest Private Bank transactions.
WITH account_aum AS (
  SELECT
    banking_relationship_id,
    SUM(CAST(balance_chf AS REAL)) AS relationship_balance_chf
  FROM accounts
  GROUP BY banking_relationship_id
),
transaction_context AS (
  SELECT
    t.transaction_id,
    t.account_id,
    a.banking_relationship_id,
    br.relationship_name,
    t.booked_at,
    t.transaction_type,
    t.direction,
    CAST(t.amount_chf AS REAL) AS amount_chf,
    account_aum.relationship_balance_chf,
    CAST(br.aum_chf AS REAL) AS aum_chf
  FROM transactions AS t
  JOIN accounts AS a
    ON a.account_id = t.account_id
  JOIN banking_relationships AS br
    ON br.banking_relationship_id = a.banking_relationship_id
  JOIN account_aum
    ON account_aum.banking_relationship_id = br.banking_relationship_id
  WHERE br.institution_name = 'Alpine Crest Private Bank'
),
relationship_baselines AS (
  SELECT
    transaction_context.*,
    COALESCE(
      AVG(amount_chf) OVER (
        PARTITION BY banking_relationship_id
        ORDER BY booked_at, transaction_id
        ROWS BETWEEN UNBOUNDED PRECEDING AND 1 PRECEDING
      ),
      amount_chf
    ) AS relationship_amount_baseline_chf
  FROM transaction_context
)
SELECT
  transaction_id,
  banking_relationship_id,
  relationship_name,
  booked_at,
  transaction_type,
  direction,
  ROUND(amount_chf, 2) AS amount_chf,
  ROUND(relationship_balance_chf, 2) AS relationship_balance_chf,
  ROUND(aum_chf, 2) AS aum_chf,
  ROUND(
    CASE
      WHEN aum_chf > 0 THEN amount_chf / aum_chf
      ELSE 0
    END,
    6
  ) AS amount_to_aum_ratio,
  ROUND(relationship_amount_baseline_chf, 2) AS relationship_amount_baseline_chf,
  ROUND(
    CASE
      WHEN relationship_amount_baseline_chf > 0
        THEN amount_chf / relationship_amount_baseline_chf
      ELSE 0
    END,
    4
  ) AS amount_to_relationship_baseline_ratio
FROM relationship_baselines
ORDER BY booked_at, transaction_id;
