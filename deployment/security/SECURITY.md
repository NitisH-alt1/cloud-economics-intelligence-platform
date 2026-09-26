# Security

## Principles

- No cloud credentials are stored in source control.
- Secrets are supplied through environment variables or managed secret stores.
- Customer cloud credentials must never be displayed in logs.
- Tenant data must be isolated at the database/API layer.
- Public APIs must use authentication and authorization.
- Production endpoints must use HTTPS.
- Sensitive telemetry must not be exposed publicly.

## Current status

Public SaaS security hardening is being implemented before production customer onboarding.
