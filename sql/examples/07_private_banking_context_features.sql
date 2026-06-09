-- Private-banking context features for pb_transaction_fraud and
-- pb_high_value_movement.
-- Demonstrates off-hours, cross-border, and velocity signals for Alpine Crest
-- Private Bank transactions.
WITH transaction_context AS (
  SELECT
    t.transaction_id,
    t.account_id,
    a.banking_relationship_id,
    br.primary_client_id,
    c.partner_id,
    p.country AS partner_country,
    t.payment_beneficiary_id,
    pb.beneficiary_account_country,
    pb.beneficiary_bank_country,
    t.booked_at,
    CAST(strftime('%H', t.booked_at) AS INTEGER) AS booked_hour,
    CAST(t.amount_chf AS REAL) AS amount_chf
  FROM transactions AS t
  JOIN accounts AS a
    ON a.account_id = t.account_id
  JOIN banking_relationships AS br
    ON br.banking_relationship_id = a.banking_relationship_id
  JOIN clients AS c
    ON c.client_id = br.primary_client_id
  JOIN partners AS p
    ON p.partner_id = c.partner_id
  LEFT JOIN payment_beneficiaries AS pb
    ON pb.payment_beneficiary_id = t.payment_beneficiary_id
  WHERE br.institution_name = 'Alpine Crest Private Bank'
),
velocity_windows AS (
  SELECT
    transaction_context.*,
    COUNT(*) OVER (
      PARTITION BY banking_relationship_id
      ORDER BY booked_at, transaction_id
      ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
    ) AS relationship_txn_count_7d,
    SUM(amount_chf) OVER (
      PARTITION BY banking_relationship_id
      ORDER BY booked_at, transaction_id
      ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
    ) AS relationship_amount_sum_7d_chf,
    COUNT(*) OVER (
      PARTITION BY banking_relationship_id
      ORDER BY booked_at, transaction_id
      ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
    ) AS relationship_txn_count_30d,
    SUM(amount_chf) OVER (
      PARTITION BY banking_relationship_id
      ORDER BY booked_at, transaction_id
      ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
    ) AS relationship_amount_sum_30d_chf
  FROM transaction_context
)
SELECT
  transaction_id,
  banking_relationship_id,
  booked_at,
  booked_hour,
  CASE
    WHEN booked_hour < 8 OR booked_hour >= 18 THEN 1
    ELSE 0
  END AS is_off_hours,
  partner_country,
  COALESCE(beneficiary_account_country, '') AS beneficiary_account_country,
  COALESCE(beneficiary_bank_country, '') AS beneficiary_bank_country,
  CASE
    WHEN payment_beneficiary_id IS NOT NULL
      AND (
        beneficiary_account_country <> partner_country
        OR beneficiary_bank_country <> partner_country
      )
      THEN 1
    ELSE 0
  END AS is_cross_border,
  relationship_txn_count_7d,
  ROUND(relationship_amount_sum_7d_chf, 2) AS relationship_amount_sum_7d_chf,
  relationship_txn_count_30d,
  ROUND(relationship_amount_sum_30d_chf, 2) AS relationship_amount_sum_30d_chf,
  ROUND(
    CAST(relationship_txn_count_7d AS REAL) / relationship_txn_count_30d,
    4
  ) AS txn_count_7d_to_30d_ratio,
  ROUND(
    CASE
      WHEN relationship_amount_sum_30d_chf > 0
        THEN relationship_amount_sum_7d_chf / relationship_amount_sum_30d_chf
      ELSE 0
    END,
    4
  ) AS amount_7d_to_30d_ratio
FROM velocity_windows
ORDER BY booked_at, transaction_id;
