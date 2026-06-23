---
title: "Swiss AMLA, AMLO, and FINMA AML anchors"
status: draft-hitl
hitl_review_required: true
source_families:
  - swiss_amla
  - swiss_amlo
  - finma
pattern_ids:
  - pb_high_value_movement
  - pb_transaction_fraud
learning_use:
  - analytics_question
  - control
  - documentation
  - explainability
  - alert_handling
track: private-banking fraud detection
primary_official_sources:
  - https://www.finma.ch/en/documentation/legal-basis/laws-and-ordinances/anti-money-laundering-act-%28amla%29/
  - https://www.fedlex.admin.ch/eli/cc/1998/892_892_892/en
  - https://www.fedlex.admin.ch/eli/cc/2015/791/de
  - https://www.fedlex.admin.ch/eli/cc/2015/390/de
linked_modules:
  - notebooks/00_foundations/foundations_data_tour.ipynb
  - notebooks/01_private_banking_transaction_fraud/alpine_crest_baseline.ipynb
  - notebooks/03_alert_governance/alert_governance_memo.ipynb
  - notebooks/04_private_banking_feature_engineering/alpine_crest_feature_engineering.ipynb
  - notebooks/04_private_banking_feature_engineering/alpine_crest_supervised_baseline.ipynb
---

# Swiss AMLA, AMLO, And FINMA AML Anchors

<!-- HITL-REVIEW-REQUIRED -->

Educational use only: this source note supports fraud-detection curriculum design and is not legal or compliance advice.

## Source Scope

This note uses FINMA's legal-basis page as the navigation anchor for Swiss anti-money
laundering sources, then links the official Fedlex entries for AMLA, AMLO, and the FINMA
Anti-Money Laundering Ordinance. No direct quotations are needed for the v0.1 exercises.

The source family is useful for **Private-banking fraud detection** because Swiss private
banking scenarios often require learners to distinguish analytics evidence from control,
documentation, and escalation context.

In v0.3, the same source family anchors deeper Alpine Crest Private Bank feature
engineering and threshold-tuning questions. The regulatory note connects relationship-manager
responsibility, beneficial-ownership and signatory context, counterparty novelty, cross-border
movement, alert capacity, and false-positive explanation boundaries to observable analytics
evidence rather than to legal conclusions.

## Learning Prompt

When building `pb_transaction_fraud` and `pb_high_value_movement` features in the Alpine
Crest notebooks, use this source family to frame what makes a transaction reviewable rather
than to reach a legal conclusion. Consider how relationship-manager responsibility, beneficial
ownership, and counterparty novelty shape the analytics question, the control evidence, the
documentation you would keep, the way you explain a score to a reviewer, and how the alert
moves through its lifecycle.

## Official Sources

- [FINMA legal basis for combating money laundering](https://www.finma.ch/en/documentation/legal-basis/laws-and-ordinances/anti-money-laundering-act-%28amla%29/)
- [Federal Act on Combating Money Laundering and Terrorist Financing, AMLA](https://www.fedlex.admin.ch/eli/cc/1998/892_892_892/en)
- [Anti-Money Laundering Ordinance, AMLO](https://www.fedlex.admin.ch/eli/cc/2015/791/de)
- [FINMA Anti-Money Laundering Ordinance, AMLO-FINMA](https://www.fedlex.admin.ch/eli/cc/2015/390/de)

## Learning Implications

Learners should see the Swiss AML stack as a reason to document why a transaction pattern is
investigable, what data supports the concern, and what remains uncertain. In Alpine Crest
Private Bank exercises, this note should steer learners toward repeatable evidence such as
Banking relationship context, counterparty novelty, amount-to-history change, and alert
lifecycle status instead of broad conclusions about a Client.

This source note should also reinforce that model outputs are decision support. The relevant
learner habit is to connect a score to observable data signals and case notes, not to present
the score as a legal finding.

For v0.3 private-banking analytics, learners should connect `pb_high_value_movement` and
`pb_transaction_fraud` features to documented review questions. Relationship-manager context,
beneficial-ownership signals, authorized-signatory joins, and amount-to-relationship baselines
help explain why an alert is reviewable. Threshold rationale, alert capacity, and false-positive
examples help learners document limits without treating legitimate high-net-worth behaviour as
evidence of wrongdoing.

## Linked Exercises

- `notebooks/00_foundations/foundations_data_tour.ipynb`: introduces the Alert lifecycle and
  protected answer keys so learners separate operational labels from hidden ground truth.
- `notebooks/01_private_banking_transaction_fraud/alpine_crest_baseline.ipynb`: uses Alpine
  Crest Private Bank data to connect private-banking transaction signals to a review queue.
- `notebooks/03_alert_governance/alert_governance_memo.ipynb`: turns threshold and alert
  capacity analysis into a governance memo draft with limitations.
- `notebooks/04_private_banking_feature_engineering/alpine_crest_feature_engineering.ipynb`:
  maps relationship, counterparty, cross-border, velocity, and relationship-manager features to
  Detection pattern IDs and source columns.
- `notebooks/04_private_banking_feature_engineering/alpine_crest_supervised_baseline.ipynb`:
  uses capacity-aware threshold summaries and limitation wording to keep Swiss regulatory context
  separate from model conclusions.

## Human Review

HITL review should confirm that the Swiss-law framing is accurate, that source links are the
right official anchors for English-language learners, and that the exercise language remains
educational rather than advisory.
