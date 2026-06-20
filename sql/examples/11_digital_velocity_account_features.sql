-- Digital-banking velocity, account age, and shared-device features for
-- digital_scam_to_mule and session_payment_velocity.
-- Demonstrates session payment counts, account age / early-life flags, and
-- shared-device usage for NovaBank Digital transactions.
WITH digital_transactions AS (
  SELECT
    t.transaction_id,
    t.account_id,
    t.booked_at,
    t.direction,
    CAST(t.amount_chf AS REAL) AS amount_chf,
    sa.session_id,
    CAST(a.opened_at AS REAL) AS account_opened_epoch
  FROM transactions AS t
  JOIN accounts AS a
    ON a.account_id = t.account_id
  LEFT JOIN suspicious_activities AS sa
    ON sa.transaction_id = t.transaction_id
  WHERE a.institution_name = 'NovaBank Digital'
),
session_payment_counts AS (
  SELECT
    session_id,
    COUNT(*) AS db_session_payment_count,
    SUM(amount_chf) AS db_session_payment_amount_chf,
    MAX(amount_chf) AS db_session_max_payment_chf
  FROM digital_transactions
  WHERE direction = 'debit'
    AND session_id IS NOT NULL
  GROUP BY session_id
),
device_user_counts AS (
  SELECT
    s.device_fingerprint_hash,
    COUNT(DISTINCT s.user_id) AS db_device_user_count
  FROM sessions AS s
  GROUP BY s.device_fingerprint_hash
),
transaction_device AS (
  SELECT
    dt.transaction_id,
    dt.session_id,
    s.device_fingerprint_hash
  FROM digital_transactions AS dt
  LEFT JOIN sessions AS s
    ON s.session_id = dt.session_id
)
SELECT
  dt.transaction_id,
  dt.account_id,
  dt.booked_at,
  dt.direction,
  ROUND(dt.amount_chf, 2) AS amount_chf,
  ROUND(
    (julianday(dt.booked_at) - julianday(date(dt.account_opened_epoch, 'unixepoch'))) ,
    2
  ) AS db_account_age_days,
  CASE
    WHEN (
      julianday(dt.booked_at)
      - julianday(date(dt.account_opened_epoch, 'unixepoch'))
    ) <= 30 THEN 1
    ELSE 0
  END AS db_is_early_life_account,
  COALESCE(spc.db_session_payment_count, 0) AS db_session_payment_count,
  ROUND(COALESCE(spc.db_session_payment_amount_chf, 0), 2) AS db_session_payment_amount_chf,
  ROUND(COALESCE(spc.db_session_max_payment_chf, 0), 2) AS db_session_max_payment_chf,
  COALESCE(duc.db_device_user_count, 0) AS db_device_user_count,
  CASE WHEN COALESCE(duc.db_device_user_count, 0) > 1 THEN 1 ELSE 0 END AS db_is_shared_device
FROM digital_transactions AS dt
LEFT JOIN session_payment_counts AS spc
  ON spc.session_id = dt.session_id
LEFT JOIN transaction_device AS td
  ON td.transaction_id = dt.transaction_id
LEFT JOIN device_user_counts AS duc
  ON duc.device_fingerprint_hash = td.device_fingerprint_hash
ORDER BY dt.booked_at, dt.transaction_id;
