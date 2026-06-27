# Advanced Notes: Real-Time Infrastructure for Fraud Detection

> Educational notes for the **banking-fraud-detection-lab** curriculum. These
> notes describe, conceptually, what a real-time streaming infrastructure would
> add **on top of** the local v0.8 monitoring world built in this repo. The repo
> itself does not implement any of this, and **the repo does not claim production
> readiness** — this material is for learning, not advice, and not a deployment
> blueprint. Everything described here is a **later, optional capability**.

## Where these notes fit

The local v0.8 world you have already built is intentionally **batch-oriented**
and **single-process**:

- You generate a synthetic banking world (clients, users, banking
  relationships, transactions, sessions).
- You score transactions offline with a scikit-learn model.
- You record five **monitoring tables** that capture how the model and a human
  reviewer behave across the scored population.

Those five local monitoring tables are the **conceptual baseline** for the rest
of these notes. Real-time infrastructure does not replace them — it adds a
streaming **delta** on top of the same ideas. Before reading on, make sure you
can name the five baseline tables and what each one is for:

1. `score` — per-transaction model outputs and inputs at scoring time.
2. `threshold` — the cutoff(s) applied to scores to flag transactions.
3. `alert_decision` — the system decision (e.g. approve / review / block)
   derived from a score crossing a threshold.
4. `reviewer_action` — what a human analyst did with an alert in the queue.
5. `audit_event` — an immutable, append-only record of security-relevant
   actions taken across the lifecycle (who/what/when/why).

The institutions used elsewhere in this repo carry through here too:
**Alpine Crest Private Bank** (the private-banking track, lower volume, higher
value per client) and **NovaBank Digital** (the digital-banking track, higher
volume, faster sessions). Real-time infra helps the two tracks differently, and
we note the tradeoffs where they diverge.

## The delta: what "real-time" adds over the local batch world

In the local world, the loop is: *score a batch, write rows, then later read
them back for monitoring.* Real-time infrastructure inserts three things the
batch world does not have:

- **Latency**: decisions happen while a transaction or session is in flight,
  not after the fact. For NovaBank Digital this can mean a card-present
  authorization is held for a fraction of a second while a score is computed;
  for Alpine Crest Private Bank a "real-time" SLA is often minutes, not
  milliseconds, because private-banking workflows prioritize relationship
  handling over speed.
- **Streaming data movement**: events flow continuously between producers
  (the banking channels) and consumers (scorers, rule engines, case
  management) instead of being loaded as files.
- **Stateful online services**: low-latency lookups of features, thresholds,
  and case state that the batch world keeps on disk in tables.

Everything below maps each local monitoring table to its real-time
counterpart, then names the categories of infrastructure that would carry it.
None of these technologies are imported, depended on, or endorsed by this repo.

## Mapping the five local monitoring tables to real-time counterparts

### 1. `score` → online feature store + low-latency scorer

- **Local baseline:** a `score` row is written once per transaction by an
  offline scikit-learn model in a notebook.
- **Real-time delta:** a serving path computes the **same kind of score**, but
  within a request budget (tens to hundreds of milliseconds). Features are read
  from an **online feature store** — a low-latency lookup layer that holds
  per-client / per-user / per-relationship aggregates (rolling spend, velocity,
  session frequency) precomputed from the stream. The model itself runs behind
  a thin **model-serving** endpoint.
- **What does NOT change:** the scoring contract. The schema of a `score` row
  in the local world is the *definition* of a score; the real-time world simply
  produces more of them, faster, from fresher features.

### 2. `threshold` → online config / threshold service

- **Local baseline:** a `threshold` row records the cutoff value(s) applied to
  scores during a given scoring run.
- **Real-time delta:** thresholds move into an **online configuration service**
  so they can change without redeploying the scorer. A reviewer tuning a cutoff
  at NovaBank Digital during a fraud wave should not have to wait for the next
  batch. The threshold service exposes the current value to the decision engine
  over the network and versions every change.
- **What does NOT change:** a `threshold` is still just a number (or small set
  of numbers) that a score is compared against; the real-time world makes it
  *mutable and centrally served*, not more complex in concept.

### 3. `alert_decision` → streaming decision engine

- **Local baseline:** an `alert_decision` row is derived locally by comparing a
  score to a threshold and choosing approve / review / block.
- **Real-time delta:** a **streaming decision engine** consumes scored events
  off a stream, applies the current threshold plus any rules (velocity rules,
  block-lists, relationship-level caps), and emits a decision onto another
  stream. This is where Kafka-style event streams or Spark/Flink-style
  micro-batch engines typically appear — as the *plumbing* between scoring and
  downstream consumers.
- **What does NOT change:** the decision logic mirrors what produced your local
  `alert_decision` rows. The local table is the *specification* of a decision;
  the engine is a *distribution mechanism* for decisions.

### 4. `reviewer_action` → case management / review UI

- **Local baseline:** a `reviewer_action` row records what a human analyst did
  with an alert.
- **Real-time delta:** analysts need a **case-management system** and a
  **review UI** to triage alerts as they stream in. For Alpine Crest Private
  Bank this may be a small queue tied to a relationship manager; for NovaBank
  Digital it may be a high-throughput queue with SLAs and routing rules. The
  case-management system writes the same `reviewer_action`-shaped records back
  to a store, often enriched with latency and SLA metadata.
- **What does NOT change:** a `reviewer_action` is still a human-issued verdict
  on a specific alert. The real-time world adds the *queue and the UI*, not a
  new concept of review.

### 5. `audit_event` → immutable append-only event log / audit sink

- **Local baseline:** an `audit_event` row captures a security-relevant action
  immutably.
- **Real-time delta:** the real-time equivalent is an **append-only event log**
  (sometimes called an **audit sink**) that every service writes to as a side
  effect of doing its job: the scorer logs that it scored, the threshold
  service logs every change, the decision engine logs every block, the case
  manager logs every disposition. This log is the system of record for
  after-the-fact reconstruction and for regulators.
- **What does NOT change:** immutability and append-only semantics. The local
  `audit_event` table already enforces the same discipline; the real-time world
  just makes it the *shared spine* every component writes to.

## Categories of real-time infrastructure (named, not depended on)

These are the families of technology the mapping above leans on. The repo
references them **conceptually only**; none are dependencies.

- **Event streams (Kafka-style).** A durable, partitioned log that decouples
  producers (the banking channels) from consumers (scorers, decision engine,
  audit sink). Useful for both tracks, but NovaBank Digital's session and
  payment volumes are what usually justify the operational cost.
- **Micro-batch / stream processors (Spark- or Flink-style).** Compute
  rolling aggregates and windowed features from the stream and feed the online
  feature store. Alpine Crest Private Bank's smaller volumes may make
  micro-batching the pragmatic choice; NovaBank Digital may need true streaming.
- **In-memory caches (Redis-style).** Hold the hot working set: current
  thresholds, recent per-client velocity, case state. These are the low-latency
  lookups the scorer and decision engine make per event.
- **Dashboards / operational UIs.** Visualize alert volumes, reviewer
  throughput, threshold drift, and model score distributions. Distinct from the
  review UI (which is for acting on individual alerts): dashboards are for
  *observing the system*. These are explicitly **deferred** in this repo's PRD
  and are a later, optional capability.

## Putting it together: the streaming loop

A single event in the real-time world flows roughly like this:

1. A banking channel (NovaBank Digital payment, Alpine Crest Private Bank
   transfer instruction) emits an event onto the **event stream**.
2. The stream processor updates **online features** in the in-memory cache.
3. The **low-latency scorer** reads features, applies the model, emits a score.
4. The **streaming decision engine** reads the score, reads the current
   **threshold** from the config service, and emits an **alert decision**.
5. If reviewable, the alert lands in the **case-management queue**; a human
   issues a **reviewer action**.
6. Every one of steps 1–5 writes a row to the **immutable audit log**.

Compare this to the local loop you already have: *score → threshold →
alert_decision → reviewer_action → audit_event*, written as five tables by a
notebook. The streaming loop produces the **same five kinds of records**, just
distributed across services and emitted continuously.

## What this repo does and does not provide

- **Does provide:** the local v0.8 monitoring tables as a clean, teachable
  definition of each concept, and these advanced notes as a bridge to the
  streaming world.
- **Does not provide:** any event stream, stream processor, cache, serving
  endpoint, case-management UI, or dashboard. Those are out of scope and are
  intentionally **optional and deferred** per the PRD.
- **Important:** these notes are **educational**. The repo **does not claim
  production readiness**, this is not operational advice, and none of the
  named technologies are imported or endorsed. Real deployment choices depend
  on volume, regulatory context, and operational capacity that a curriculum
  cannot capture.
