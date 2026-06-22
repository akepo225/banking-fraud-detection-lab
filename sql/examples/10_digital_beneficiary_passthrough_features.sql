-- Digital-banking beneficiary novelty and pass-through features for
-- digital_scam_to_mule and new_beneficiary_payment.
-- Demonstrates beneficiary age, new-beneficiary flags, and rapid pass-through
-- behavior for NovaBank Digital transactions.
WITH digital_transactions AS (
  SELECT
    t.transaction_id,
    t.account_id,
    t.booked_at,
    t.direction,
    CAST(t.amount_chf AS REAL) AS amount_chf,
    t.payment_beneficiary_id
  FROM transactions AS t
  JOIN accounts AS a
    ON a.account_id = t.account_id
  WHERE a.institution_name = 'NovaBank Digital'
),
beneficiary_context AS (
  SELECT
    dt.transaction_id,
    dt.account_id,
    dt.booked_at,
    dt.direction,
    dt.amount_chf,
    dt.payment_beneficiary_id,
    pb.created_at AS beneficiary_created_at,
    pb.beneficiary_change_event
  FROM digital_transactions AS dt
  LEFT JOIN payment_beneficiaries AS pb
    ON pb.payment_beneficiary_id = dt.payment_beneficiary_id
),
-- For each debit, find the nearest prior credit booked on the same account so
-- the pass-through window is per-debit rather than a single account-wide aggregate.
nearest_prior_credit AS (
  SELECT
    d.transaction_id,
    MAX(c.booked_at) AS nearest_prior_credit_at,
    (
      SELECT c2.amount_chf
      FROM beneficiary_context AS c2
      WHERE c2.account_id = d.account_id
        AND c2.direction = 'credit'
        AND c2.booked_at <= d.booked_at
      ORDER BY c2.booked_at DESC
      LIMIT 1
    ) AS nearest_prior_credit_amount_chf
  FROM beneficiary_context AS d
  LEFT JOIN beneficiary_context AS c
    ON c.account_id = d.account_id
   AND c.direction = 'credit'
   AND c.booked_at <= d.booked_at
  WHERE d.direction = 'debit'
  GROUP BY d.transaction_id
),
debit_context AS (
  SELECT
    bc.*,
    npc.nearest_prior_credit_at,
    npc.nearest_prior_credit_amount_chf
  FROM beneficiary_context AS bc
  LEFT JOIN nearest_prior_credit AS npc
    ON npc.transaction_id = bc.transaction_id
  WHERE bc.direction = 'debit'
)
SELECT
  bc.transaction_id,
  bc.account_id,
  bc.booked_at,
  bc.direction,
  ROUND(bc.amount_chf, 2) AS amount_chf,
  ROUND(
    CASE
      WHEN bc.beneficiary_created_at IS NOT NULL
        THEN (julianday(bc.booked_at) - julianday(bc.beneficiary_created_at))
      ELSE -1
    END,
    2
  ) AS db_beneficiary_age_days,
  CASE
    -- Match the Python db_beneficiary_novelty logic: a beneficiary is "new" when
    -- it exists AND it has a new/updated lifecycle event, was created within the
    -- 30-day lookback, or has no recorded creation timestamp.
    WHEN bc.payment_beneficiary_id IS NOT NULL
      AND (
        bc.beneficiary_change_event IN ('new_beneficiary_added', 'beneficiary_updated')
        OR (
          bc.beneficiary_created_at IS NOT NULL
          AND julianday(bc.booked_at) - julianday(bc.beneficiary_created_at) BETWEEN 0 AND 30
        )
        OR bc.beneficiary_created_at IS NULL
      )
      THEN 1
    ELSE 0
  END AS db_is_new_beneficiary,
  ROUND(COALESCE(dc.nearest_prior_credit_amount_chf, 0), 2) AS db_prior_credit_amount_chf,
  ROUND(
    CASE
      WHEN dc.nearest_prior_credit_at IS NOT NULL
        THEN (julianday(bc.booked_at) - julianday(dc.nearest_prior_credit_at)) * 24
      ELSE 25
    END,
    2
  ) AS db_hours_since_prior_credit,
  CASE
    WHEN COALESCE(dc.nearest_prior_credit_amount_chf, 0) > 0
      AND dc.nearest_prior_credit_at IS NOT NULL
      AND (julianday(bc.booked_at) - julianday(dc.nearest_prior_credit_at)) * 24 BETWEEN 0 AND 24
      AND bc.payment_beneficiary_id IS NOT NULL
      THEN 1
    ELSE 0
  END AS db_is_rapid_pass_through
FROM beneficiary_context AS bc
LEFT JOIN debit_context AS dc
  ON dc.transaction_id = bc.transaction_id
ORDER BY bc.booked_at, bc.transaction_id;
