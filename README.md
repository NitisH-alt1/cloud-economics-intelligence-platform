# Cloud Economics Intelligence Platform

## Current application

The local website is served by `web.app:app` on port `8090`. It provides login, signup, and the authenticated workspace. The FastAPI application in `dashboard.app:app` serves the API on port `8081`. PostgreSQL is configured for host port `5433` by `database/docker-compose.postgres.yml`.

The API includes organization-scoped authentication, projects, cloud-account records, connection records, project/account associations, and project-scoped cost and analysis routes. See the FastAPI OpenAPI page at `/docs` when the API is running.

## Data and analysis status

Project cost records currently contain deterministic local demo estimates, not provider billing data. Cloud-account records and connection records do not validate provider credentials or enable ingestion. Causal results are model-derived candidates for investigation, not proof of causality. Anomaly signals use the included analyzer sample data.

## Repository structure

- `analyzer/` — anomaly detection, dependency graphs, causal candidate scoring, and cost attribution.
- `auth/` — authentication, organization-scoped APIs, projects, cloud accounts, connections, and intelligence.
- `dashboard/` — FastAPI API application, configuration, logging, and security middleware.
- `database/` — SQLAlchemy models, initialization, and the local PostgreSQL Compose file.
- `data/` — included sample inputs and analysis outputs.
- `deployment/` — local launchers, wiring scripts, and security notes.
- `services/` — instrumented checkout, inventory, and payment demo services.
- `web/` — website routes, pages, styles, and browser assets.

The root `docker-compose.yml` defines the local observability and instrumented-service stack. PostgreSQL is started separately. The Compose host ports bind to loopback for local use.

## Production configuration

Production startup requires `DATABASE_URL` and `JWT_SECRET_KEY`. Configure them in the deployment environment; never commit secret values. The Render Blueprint leaves the database URL and production website origin for operator configuration and generates the JWT signing key.
