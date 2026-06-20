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
prior_credits AS (
  SELECT
    bc.account_id,
    MAX(bc.booked_at) AS prior_credit_at,
    SUM(CASE WHEN bc.direction = 'credit' THEN bc.amount_chf ELSE 0 END) AS prior_credit_amount_chf
  FROM beneficiary_context AS bc
  WHERE bc.direction = 'credit'
  GROUP BY bc.account_id
),
debit_context AS (
  SELECT
    bc.*,
    pc.prior_credit_at,
    pc.prior_credit_amount_chf
  FROM beneficiary_context AS bc
  LEFT JOIN prior_credits AS pc
    ON pc.account_id = bc.account_id
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
        THEN (julianday(bc.booked_at) - julianday(bc.beneficiary_created_at)) * 24
      ELSE -1
    END,
    2
  ) AS db_beneficiary_age_hours,
  CASE
    WHEN bc.beneficiary_change_event IN ('new_beneficiary_added', 'beneficiary_updated')
      THEN 1
    ELSE 0
  END AS db_is_new_beneficiary,
  ROUND(COALESCE(dc.prior_credit_amount_chf, 0), 2) AS db_prior_credit_amount_chf,
  ROUND(
    CASE
      WHEN dc.prior_credit_at IS NOT NULL
        THEN (julianday(bc.booked_at) - julianday(dc.prior_credit_at)) * 24
      ELSE 25
    END,
    2
  ) AS db_hours_since_prior_credit,
  CASE
    WHEN dc.prior_credit_amount_chf > 0
      AND dc.prior_credit_at IS NOT NULL
      AND (julianday(bc.booked_at) - julianday(dc.prior_credit_at)) * 24 <= 24
      AND bc.payment_beneficiary_id IS NOT NULL
      THEN 1
    ELSE 0
  END AS db_is_rapid_pass_through
FROM beneficiary_context AS bc
LEFT JOIN debit_context AS dc
  ON dc.transaction_id = bc.transaction_id
ORDER BY bc.booked_at, bc.transaction_id;
