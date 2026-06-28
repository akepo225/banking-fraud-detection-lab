-- Capstone digital-banking feature extraction (NovaBank Digital).
-- Investigates the digital_scam_to_mule, new_beneficiary_payment, and mule_ring
-- Detection patterns across the capstone dataset: session / device / beneficiary
-- / pass-through / account-age context for debit payments, tied back to
-- Banking relationship, Client or User, and Alert lifecycle lineage.
WITH digital_accounts AS (
  SELECT
    a.account_id,
    a.banking_relationship_id,
    br.primary_client_id,
    a.opened_at,
    CAST(a.balance_chf AS REAL) AS account_balance_chf
  FROM accounts AS a
  JOIN banking_relationships AS br
    ON br.banking_relationship_id = a.banking_relationship_id
  WHERE a.institution_name = 'NovaBank Digital'
),
all_digital_transactions AS (
  SELECT
    t.transaction_id,
    da.account_id,
    da.banking_relationship_id,
    da.primary_client_id AS client_id,
    t.booked_at,
    t.direction,
    CAST(t.amount_chf AS REAL) AS amount_chf,
    t.payment_beneficiary_id,
    da.opened_at
  FROM transactions AS t
  JOIN digital_accounts AS da
    ON da.account_id = t.account_id
),
digital_transactions AS (
  SELECT *
  FROM all_digital_transactions
  WHERE direction = 'debit'
),
transaction_session AS (
  SELECT
    dt.transaction_id,
    sa.session_id,
    s.user_id,
    s.device_fingerprint_hash,
    s.is_vpn_or_proxy,
    s.auth_method,
    s.session_event
  FROM digital_transactions AS dt
  LEFT JOIN (
    SELECT transaction_id, MIN(session_id) AS session_id
    FROM suspicious_activities
    WHERE transaction_id IS NOT NULL AND session_id IS NOT NULL
    GROUP BY transaction_id
  ) AS sa
    ON sa.transaction_id = dt.transaction_id
  LEFT JOIN sessions AS s
    ON s.session_id = sa.session_id
),
session_payment_counts AS (
  SELECT
    ts.session_id,
    COUNT(*) AS db_session_payment_count,
    SUM(dt.amount_chf) AS db_session_payment_amount_chf
  FROM digital_transactions AS dt
  JOIN transaction_session AS ts
    ON ts.transaction_id = dt.transaction_id
  WHERE ts.session_id IS NOT NULL
  GROUP BY ts.session_id
),
device_user_counts AS (
  SELECT
    s.device_fingerprint_hash,
    COUNT(DISTINCT s.user_id) AS db_device_user_count
  FROM sessions AS s
  GROUP BY s.device_fingerprint_hash
),
beneficiary_context AS (
  SELECT
    pb.payment_beneficiary_id,
    pb.beneficiary_change_event,
    pb.created_at AS beneficiary_created_at
  FROM payment_beneficiaries AS pb
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
  WHERE al.institution_name = 'NovaBank Digital'
),
-- Pass-through context: for each debit, the nearest prior credit on the same
-- account and its amount. A debit booked shortly after a credit is the rapid
-- pass-through signal behind the digital_scam_to_mule Detection pattern
-- (mirrors sql/examples/10_digital_beneficiary_passthrough_features.sql).
prior_credit AS (
  SELECT
    d.transaction_id,
    MAX(c.booked_at) AS nearest_prior_credit_at,
    (
      SELECT c2.amount_chf
      FROM all_digital_transactions AS c2
      WHERE c2.account_id = d.account_id
        AND c2.direction = 'credit'
        AND c2.booked_at <= d.booked_at
      ORDER BY c2.booked_at DESC
      LIMIT 1
    ) AS nearest_prior_credit_amount_chf
  FROM digital_transactions AS d
  LEFT JOIN all_digital_transactions AS c
    ON c.account_id = d.account_id
   AND c.direction = 'credit'
   AND c.booked_at <= d.booked_at
  GROUP BY d.transaction_id
)
SELECT
  dt.transaction_id,
  dt.banking_relationship_id,
  dt.client_id,
  ts.user_id,
  dt.booked_at,
  dt.amount_chf,
  ROUND(
    julianday(dt.booked_at) - julianday(dt.opened_at),
    2
  ) AS db_account_age_days,
  CASE
    WHEN (julianday(dt.booked_at) - julianday(dt.opened_at)) BETWEEN 0 AND 30
      THEN 1
    ELSE 0
  END AS db_is_early_life_account,
  COALESCE(spc.db_session_payment_count, 0) AS db_session_payment_count,
  ROUND(COALESCE(spc.db_session_payment_amount_chf, 0), 2) AS db_session_payment_amount_chf,
  COALESCE(duc.db_device_user_count, 0) AS db_device_user_count,
  CASE WHEN COALESCE(duc.db_device_user_count, 0) > 1 THEN 1 ELSE 0 END AS db_is_shared_device,
  CASE WHEN COALESCE(ts.is_vpn_or_proxy, 0) = 1 THEN 1 ELSE 0 END AS db_is_vpn_or_proxy,
  ts.auth_method AS session_auth_method,
  ts.session_event,
  bc.beneficiary_change_event,
  CASE
    WHEN bc.beneficiary_change_event = 'new_beneficiary_added' THEN 1
    ELSE 0
  END AS db_is_new_beneficiary_payment,
  ROUND(COALESCE(pc.nearest_prior_credit_amount_chf, 0), 2) AS db_prior_credit_amount_chf,
  ROUND(
    CASE
      WHEN pc.nearest_prior_credit_at IS NOT NULL
        THEN (julianday(dt.booked_at) - julianday(pc.nearest_prior_credit_at)) * 24
      ELSE 25
    END,
    2
  ) AS db_hours_since_prior_credit,
  CASE
    WHEN COALESCE(pc.nearest_prior_credit_amount_chf, 0) > 0
      AND pc.nearest_prior_credit_at IS NOT NULL
      AND (julianday(dt.booked_at) - julianday(pc.nearest_prior_credit_at)) * 24 BETWEEN 0 AND 24
      AND dt.payment_beneficiary_id IS NOT NULL
      THEN 1
    ELSE 0
  END AS db_is_rapid_pass_through,
  sa.alert_id,
  sa.alert_type,
  sa.alert_status,
  sa.severity AS alert_severity
FROM digital_transactions AS dt
LEFT JOIN transaction_session AS ts
  ON ts.transaction_id = dt.transaction_id
LEFT JOIN session_payment_counts AS spc
  ON spc.session_id = ts.session_id
LEFT JOIN device_user_counts AS duc
  ON duc.device_fingerprint_hash = ts.device_fingerprint_hash
LEFT JOIN beneficiary_context AS bc
  ON bc.payment_beneficiary_id = dt.payment_beneficiary_id
LEFT JOIN prior_credit AS pc
  ON pc.transaction_id = dt.transaction_id
LEFT JOIN scenario_alerts AS sa
  ON sa.transaction_id = dt.transaction_id
ORDER BY dt.booked_at, dt.transaction_id;
