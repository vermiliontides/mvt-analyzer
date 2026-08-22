# Observability Stack: necessity, fit, privacy, and integration plan

This document explains why an observability stack (metrics + logs + storage) is necessary for the product, how it fits into a local/offline desktop product, what value it brings, time & cost estimates for integration, options for local-only operation and opt-in sharing, and a recommended prioritized task list.

Contents
- Why observability services are necessary
- How the stack fits into a local desktop product (Electron + epoch tools + extractors)
- Value delivered for customers and support
- Time & cost to integrate (rough estimates)
- Local-only operation and privacy-preserving defaults
- Opt-in sharing and support bundle flows
- Suggested observability stack and rationale (Loki, Vector, VictoriaMetrics, Grafana)
- Docker Compose for a local stack (infra/observability-docker-compose.yml)
- Prioritized tasks for rollout

---

## Why observability services are necessary

A local/offline product that runs complex pipeline stages (decryption, extraction, normalization, DB writes, UI rendering) needs observability for:

- Troubleshooting: fast identification of slow stages, failing extractors, or DB bottlenecks.
- Performance tuning: measure how long extraction/normalization takes, tune batch sizes and concurrency.
- Quality monitoring: detect silent failures (e.g., skipped records, malformed files) and surface them to users.
- Auditability: maintain a local timeline of pipeline runs and their resource usage for compliance and reproducibility.
- Proactive remediation: local alerting can help users take corrective action immediately (e.g., retry pipeline, free disk space).

Even when fully offline and privacy-focused, these capabilities are valuable because they improve the product's reliability and the user’s ability to operate it safely.

## How the stack fits into a local desktop product

Architecture (local-only mode)

- Electron app + epoch UI: the user interface that starts/monitors runs and shows dashboards.
- Orchestrator (Node): runs pipeline stages and exposes metrics (/metrics) and structured logs.
- Extractors (Python): produce logs and metrics for extraction, normalization, DB writes.
- Local Observability Stack (Docker or embedded processes):
  - Vector agent collects logs from extractors and system components, optionally redacts PII, forwards to Loki and VictoriaMetrics.
  - Loki stores logs locally and serves Grafana queries.
  - VictoriaMetrics stores metrics (Prometheus-compatible remote-write ingestion) for efficient TSDB storage.
  - Grafana points at Loki and VictoriaMetrics to render dashboards.

All services are run locally (either as background processes or via Docker Compose) and bound to localhost by default. The UI can embed or link to Grafana dashboards or present summary metrics directly inside the Electron app.

## Value delivered to customers and support

- Faster troubleshooting for end-users: integrated dashboards show which stage failed and why.
- Privacy-preserving diagnostics: all telemetry can remain local unless the user explicitly opts to share.
- Better performance: metrics-driven tuning of batch sizes and concurrency reduces runtime and resource usage.
- Transparent audits: customers can review run history and show support exactly what happened without exposing sensitive artifact content.

## Time & cost to integrate (rough estimates, developer-days)

These are approximate single-engineer estimates to deliver a production-grade local stack and basic instrumentation.

- Basic local stack (Prometheus/VM, Grafana, Loki, Vector) compose + docs: 1–2 days
- Instrument orchestrator & one extractor (metrics + logs + counters + histograms): 1–2 days
- Vector config to redact sensitive fields, forward to Loki/VM: 1 day
- Grafana dashboards & provisioning (basic dashboards for runs, per-extractor stats): 1–2 days
- Diagnostics bundle & export UI in Electron (user-controlled): 2–4 days
- CI tests for instrumentation + CI job to validate dashboards/provisioning: 2–3 days

Total initial MVP: 6–12 developer-days. More polish (centralized optional opt-in sharing, long-term retention, multi-host networking) is additional.

## Local-only operation and privacy guarantees

Design principles for privacy-first local operation:

- Default: local-only. No remote endpoints are configured by default. Metrics and logs are stored on disk in app data directories and are accessible only to the local user.
- Redaction: use Vector to redact PII at collection time (file paths, phone numbers, message content) — the agent runs before storage or upload.
- Least privilege: the product stores only aggregated counters and necessary labels (stage, extractor, environment). Avoid high-cardinality labels and sensitive fields.
- User control: expose a single, discoverable UI action that generates a diagnostics bundle (redacted) and prompts the user to send it to support. The user explicitly consents to each upload.
- Audit & transparency: every opt-in is logged locally with timestamp and scope. Provide an interface to view and remove telemetry history.

## Opt-in sharing

Two supported flows:

1. Manual support bundle (recommended for privacy-first users)
   - The user clicks "Create diagnostics bundle" in the app.
   - Vector and local scripts gather last N days of metrics/logs, run redaction, and create a tarball.
   - The user may review the bundle and then choose to send it to support (secure HTTPS upload) or save it locally and transport it manually.

2. Opt-in automatic sharing (enterprise/managed deployments)
   - The user or administrator explicitly enables remote sharing and trusts the destination.
   - The product uploads telemetry to a vendor-managed endpoint (or a self-hosted endpoint for enterprise) with short retention and access controls.
   - The sharing UI must display precisely what is being shared and for how long.

Both flows should be auditable and reversible.

## Recommended stack & why (summary)

- Vector: local collector and safe redaction pipeline. Cross-platform, low footprint, supports sinks for Loki and VictoriaMetrics.
- Loki: label-based log store, efficient for correlating logs with Prometheus/Grafana dashboards. Good for local deployment and integrates with Grafana.
- VictoriaMetrics: efficient TSDB for metrics; accepts Prometheus remote_write and uses less disk/CPU at scale.
- Grafana: visualization and dashboarding; first-class support for Loki and VictoriaMetrics; can be run locally and embedded into the UI.

Why this combination?
- Privacy-first: all components can run locally, bound to localhost.
- Interoperability: Grafana + Loki + VM + Vector are complementary and standard in modern observability stacks.
- Upgrade path: scale by moving VM/Loki to centralized servers and using remote_write only for opt-in deployments.

---

## Docker Compose (local observability stack)

See `infra/observability-docker-compose.yml` in this repository for a ready-to-run local stack (Loki, VictoriaMetrics, Grafana, Vector). Files under `infra/` include example configs and a Vector pipeline that shows redaction and forwarding to Loki and VictoriaMetrics.

> NOTE: Compose is example-only; adjust mounts and file paths to your platform. All services are bound to localhost by default in the compose file.

---

## Prioritized task list (next steps)

1. (P0) Deploy local observability compose and verify Grafana panels: sanity check dashboards and log queries. (1 day)
2. (P0) Instrument orchestrator for basic metrics (processing time, stage status, counts). (1 day)
3. (P0) Add Vector pipeline to tail extractor logs and redact PII before storing. (1 day)
4. (P1) Add instrumentation to 2–3 representative extractors (ileapp, crash, mvt_iocs). (2–3 days)
5. (P1) Create Grafana provisioning (datasources/dashboards) and import basic dashboards. (1 day)
6. (P1) Implement diagnostics bundle CLI and Electron UI (redaction + user consent). (3 days)
7. (P2) Add CI validation for instrumentation and dashboards (GitHub Actions). (2 days)
8. (P2) Add optional remote_write to VictoriaMetrics for opt-in centralized diagnostics (security review). (3–5 days)
9. (P2) Add long-term retention plan and partitioning/archival policies for forensic_records (DB side). (3–7 days)

---

## Final notes

This design balances privacy, local usability, and future scalability. The recommended stack (Vector + Loki + VictoriaMetrics + Grafana) gives the most flexible path: run locally and private-by-default, then scale out with remote backends if/when the customer explicitly opts in to centralized telemetry.

If you want, I will:
- Add the compose + configs to the repo (already included: `infra/observability-docker-compose.yml`).
- Add basic instrumentation to the orchestrator and to one extractor as a pattern for others.
- Implement the diagnostics bundle and a minimal UI flow.

Which of those would you like first? 
