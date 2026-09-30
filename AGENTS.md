# Repository Guidelines

## Project Context

Cloud Economics Intelligence Platform is a productized SaaS around the Causal Cost Attribution Engine. The existing analysis engine identifies anomalies, scores causal candidates across service dependencies, and estimates cost attribution. It provides evidence for candidate explanations; it does not establish scientific proof of causality. Preserve and integrate this engine instead of rebuilding it without a clear need.

The repository is the source of truth. Historical context below guides work but may be stale; inspect current implementation and call out discrepancies. Current reported branch is `product/public-saas`. Local environment reported for this project: Windows, Python 3.12.10, Git 2.50.1.windows.1, Docker 28.3.3, and `.venv`; inspect actual tools and configuration before relying on these versions.

## Structure & Architecture

- `analyzer/`: anomaly detection, dependency graphs, temporal/propagation analysis, scoring, cost attribution, pipeline.
- `dashboard/app.py`: FastAPI API; `auth/` contains authentication, tenant, project, cloud-account, connection, and workspace routers.
- `database/`: SQLAlchemy models and database setup. Entities include users, organizations, memberships, projects, cloud accounts, cloud connections, project/cloud-account associations, and project-scoped cost records. Startup `create_all` initializes the added association and cost tables; it does not alter existing tables.
- `web/`: website app, pages, and assets. `services/checkout`, `services/inventory`, and `services/payment` are instrumented microservices.
- `data/`: sample/generated baselines, anomaly scores, failure scenario, trace, cost attribution, causal candidates, and causal chain.
- `deployment/`: local launchers, deployment wiring, and security documentation. Root Docker/Prometheus/OpenTelemetry files define development infrastructure.

Public application flow: website → FastAPI → tenant/auth/project/cloud APIs → PostgreSQL → cost intelligence and causal analysis → future provider ingestion. Workspace areas include Overview, Projects, Cloud Accounts, Cost Intelligence, Causal Analysis, Recommendations, and Settings.

## Local Ports & Services

Use website `http://127.0.0.1:8090`, API `http://127.0.0.1:8081`, and PostgreSQL host port `5433`. Port **8080 is occupied by Jenkins/Java and must never be used or stopped**. The website launcher defaults to 8090 and production API launcher to 8081. However, the direct-run block in `dashboard/app.py` currently specifies 8080; do not use that entry point as-is. Verify launch configuration before running the API. Docker services include checkout 8001, inventory 8002, payment 8003, Jaeger 16686, Prometheus 9090, and PostgreSQL 5433. Treat observability and database services as internal; do not expose them publicly. Do not start/stop services unless the task calls for it.

## Product & API Context

Existing routes include `/api/auth/signup`, `/api/auth/login`, `/api/account/me`, `/api/projects`, `/api/cloud-accounts`, `/api/cloud-connections`, `/api/workspace/summary`, and project-scoped cost, anomaly, causal, recommendation, and cloud-account association routes; inspect router code for the full current API. JWT uses HS256 and password hashing uses PBKDF2-SHA256. Protected routes rely on authenticated user/organization context. Every tenant-owned read and write must enforce `organization_id` scope.

Project descriptions are supported in the current model, schemas, API, and workspace UI (maximum 500 characters). A historical demo project is named “Cloud Economics Demo” with slug `cloud-economics-demo`; verify database state before assuming it exists locally. Cloud account records support AWS, Azure, and GCP. Connection routes are `GET/POST /api/cloud-connections` and `DELETE /api/cloud-connections/{connection_id}`. Current schema accepts `aws_role`, `azure_service_principal`, or `gcp_service_account`; the API creates a record with status `configured`, but this flow does not establish that provider credentials were validated. Never claim a live provider connection without actual verified authentication. Do not invent provider parameters.

Sample analysis records a `payment → inventory → checkout` candidate chain with payment as candidate root. The cost example estimates increases of checkout 0, inventory 0.63, and payment 0.70 (total 1.33), with attribution shares about 0.4737 and 0.5263. Treat these as sample/model output, not live billing facts.

Synthetic project costs are persisted in `cost_records`, are deterministic local demo estimates, and do not come from provider billing APIs. Connection records in `configured` state do not validate credentials; the local demonstration does not enable credential validation. Causal outputs remain model-derived candidates and are not proof of causality.

## Product Roadmap

Remaining direction: validate connections only through implemented provider APIs; ingest real AWS/Azure/GCP data through verified APIs; add alerts/reports, billing, production deployment, public docs, legal/security documentation, and pricing. Do not rebuild completed foundations (deployment, auth, workspace, project CRUD/descriptions, project/cloud-account association, local demo costs, cloud account/connection records, telemetry, or analysis) before inspecting current code.

## Development & Safety Rules

1. Inspect relevant source, models/schema, configuration, dependencies, and both frontend/backend contracts before changing behavior. Repository evidence outranks this handoff.
2. Make minimal changes; preserve working architecture and OpenTelemetry, Jaeger, Prometheus, and microservices.
3. Never fabricate routes, flags, parameters, packages, environment variables, schema, provider behavior, or commands. Verify uncertain details in source or authoritative documentation.
4. Never hard-code secrets. Keep tenant data isolated by organization. Inspect current migrations/models/schema before database changes; major architecture changes require explicit approval.
5. Keep PostgreSQL, Prometheus, Jaeger, and internal services private. Respect the port rules above.
6. Before code changes, check syntax, imports, dependency availability, variable scope, edge cases, security, and API/database compatibility. After changes, run appropriate verification and report exact commands/results; distinguish verified facts from assumptions.

## Development Commands

Use the existing `.venv` after inspecting it. `python -m analyzer.pipeline.run_pipeline` runs the analysis pipeline. `./scripts/run_analysis.ps1` is a Windows end-to-end flow that starts Docker services, generates telemetry, runs analysis, and checks the dashboard; inspect its side effects and port use before running. PostgreSQL has a separate compose file at `database/docker-compose.postgres.yml`; inspect compose configurations before starting any stack. No checked-in test modules or test framework configuration were found during handoff preparation; inspect `tests/` and dependencies before choosing a test command. No formatter/linter configuration is currently evident.

## Git & Pull Requests

Recent commit subjects are concise imperative summaries (for example, “Add production application foundation”). Use action-oriented subjects. Pull requests should explain behavior, link related issues where available, list verification and results, include UI screenshots for visible changes, and call out configuration, data, or deployment effects.

## Configuration & Security

`.env.example` documents configuration; `.env` is ignored. Review `deployment/security/SECURITY.md` for security changes. Current source includes local database fallback configuration; inspect deployment/runtime configuration and avoid carrying development credentials into production. CORS currently allows `localhost:8090` and `127.0.0.1:8090`; security-header middleware exists. Do not broaden origins or weaken protected-route behavior without need.

The API requires `JWT_SECRET_KEY` and `DATABASE_URL` when `APP_ENV=production`; development-only JWT and local PostgreSQL fallbacks are used outside production only. Configure these values through the runtime environment and never place secrets in frontend code.

## Handoff Provenance

This project was developed incrementally in ChatGPT before Codex. The original conversation is not implementation authority. Historical roadmap and product context are preserved here to reduce context loss. If this file conflicts with code, investigate and report the mismatch instead of blindly changing working code.
