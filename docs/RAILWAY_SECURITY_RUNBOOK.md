# Railway security remediation — October 2026

## Application changes

- Operational routes use an active, verified server session. The existing owner emails in `OwnerGuard` remain operators; `ADMIN_EMAILS` optionally overrides that comma-separated allowlist. An explicitly empty value permits only the `admin` membership tier. No membership or subscription is changed.
- Evolution reads, commands and CSV export require Bearer authorization. The frontend sends its current session in a header, including for downloads. Credentials must never appear in URL parameters.
- Main maintenance/debug routes and admin report/metrics reads use the same authorization boundary. Public market reads, login and user feedback submission remain available.
- Redis readers belong to one client generation. Cancellation is joined before reconnecting; the private pool has four connections. Diagnostics use a one-connection pool closed in `finally`, reveal no URL fragment, and distinguish a running listener from a healthy tick feed.
- USOIL's existing recorder feed accepts both the production REST client's dictionary response and SDK responses. Its symbol scope stays unchanged. No Redis publisher or new signal strategy is enabled.
- `/api/ready` requires working DB credentials and all routers. It returns 503 on authentication failure, router failure or a two-second probe timeout. Railway checks readiness before routing to the new deployment.
- `CORS_ALLOWED_ORIGINS` optionally overrides the default production and local development origins. A wildcard is rejected. This is additional browser protection, not a substitute for authorization.
- `/api/version` reports `RAILWAY_GIT_COMMIT_SHA` rather than a hardcoded historical revision.

## Credential rotation — operator handoff required

A code deployment does not invalidate credentials copied during the Railway incident. Browser credential changes and MFA enrollment must be completed by the account owner. Do not paste credentials into chat, logs, screenshots, commits or this document.

1. Review provider usage and billing since October 21. Record unfamiliar usage before revoking the affected key; contact the provider and Railway through their official support channels when applicable.
2. For each secret stored in Railway, identify every consumer first. The inspected service contains AI provider keys, a GitHub token, Supabase privileged keys, Redis credentials, mail/CAPTCHA secrets and X credentials.
3. Where the provider supports overlapping keys: create a restricted replacement, update all consumers, verify the replacement, then revoke the previous key promptly. Revoke a known abused key immediately even if this interrupts its consumer. Preserve the minimum scopes each service needs.
4. Supabase service credentials are also used by the Windows agent, trade synchronization and recorder. Coordinate those consumers before revocation. Do not broadly rotate signing keys or all user sessions without identifying the affected key type and impact.
5. Redis credentials are shared by Railway services and any Windows publisher/cache consumers. Update actual consumers together; leave trading processes running unless their own configuration reload requires a restart. Verify PING, feed counters, recorder freshness and error logs afterward.
6. Confirm the GitHub token's scopes and recent usage, replace/revoke it, and verify Railway's source integration. Do not disconnect/reconnect the integration unless deployment reports an integration error; reconnect only the existing repository scope.
7. Enable Railway account MFA and store recovery codes privately. The inspected workspace has one administrator, so avoid locking out that account.

## Deployment verification

- Confirm backend `main` + `/backend` and frontend `main` + `/frontend`.
- Compare `/api/version` to the new deployment's revision.
- Public `/`, `/api/health`, `/api/ready` return 200; readiness reports `routers=true` and `db=true`.
- Anonymous maintenance, diagnostics, Evolution and admin-data requests return 401; authenticated non-operators return 403.
- Existing operator session can load Evolution and download CSV. An expired session must not enqueue commands.
- Market Events routes exist; empty data is distinct from a missing route.
- Inspect Redis connection counts and `forexsai-mt5-feed` clients. There must be one reader per backend process, no recurring connection flood.
- Verify USOIL's recorder source, closed M1 freshness, and error counters. The legacy Redis publisher has been inactive since June; zero Redis ticks must not be reported as a healthy live feed.
- If readiness fails, keep the previous deployment serving while investigating. Never bypass authorization to make a check pass, and never test a destructive maintenance or restart endpoint against production.

## Limits of this review

The inspected Railway Audit Logs page returned no results. This does not establish that credentials were not accessed. Provider-side usage review, key revocation and MFA require separate completion evidence.
