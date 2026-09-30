# Website

The FastAPI application in `web.app:app` serves the user-facing site on port `8090`.

| Route | Page |
| --- | --- |
| `/`, `/login`, `/signup` | Shared sign-in and organization signup page |
| `/workspace` | Authenticated workspace shell and its project, account, cost, causal, anomaly, recommendation, and settings sections |
| `/dashboard` | Redirects to `/workspace` |
| `/health` | Website health response |

Browser assets are served from `/assets`. API requests go to the FastAPI application on port `8081` and use the bearer token stored by the sign-in flow. Workspace analysis currently uses project-scoped local demo estimates and included analyzer samples; it does not represent provider billing or validated cloud credentials.
