# Security checklist

Project-specific. Status key: **Done** = implemented in code; **Partial**; **Missing**; **N/A** (with reason);
**Verify** = needs a run or a setting check that was not possible where this was written.
"Done" means the code is there. HTTP-level tests exist (`backend/tests/test_api.py`) but **have not been run**.
Finding IDs refer to `threat-model.md` and `attack-surface.md`. Nothing was changed while writing this.

| Area | Status | What applies here | Evidence / next step |
| --- | --- | --- | --- |
| Authentication | N/A | No accounts or logins (ADR 0002). No custom password code exists | If accounts are added, use a proven provider |
| Authorization / RBAC | N/A | No roles, tenants or protected resources | Revisit with any stored data |
| Session / token security | N/A | No sessions, cookies or tokens | `X-Request-ID` is a trace label, not a credential |
| Input validation | Done, Verify | Types, bounds, no extras, no NaN, string length caps, category whitelist, unknown values rejected | `schemas.py`, `model_service.py:prepare_row`, tests in `test_api.py`, `test_model_service.py` (model tests run) |
| Injection | Done | No SQL, shell, template, path or URL built from input | Code search: none of those APIs used with request data |
| XSS | Done, Verify | Errors never echo input; React renders text; lint bans `dangerouslySetInnerHTML`; API sends CSP `default-src 'none'`. Test for a rendered `<img onerror>` exists | `errors.py:66-72`, `eslint.config.js`, `App.test.tsx`. Frontend host CSP is **Missing** (F9) |
| CSRF | N/A | No cookies or sessions, and the only state-changing action is none (a prediction changes nothing) | Re-check if cookies are ever added |
| API security | Partial | Standard errors, methods limited, no stack traces, docs off in production, size cap by header | F4, A1, A4 |
| Rate limiting / abuse | Partial | Per-IP limits on predict and options, `Retry-After` | F1, F2, F6 (verify), A1; no cost caps needed (no paid API) |
| File uploads | N/A | None exist | `attack-surface.md` |
| Database security | N/A | No database | ADR 0002 |
| Secrets | Done | No secrets; env-only config; `.env` ignored; examples contain no values | `secrets.md`; S2 gitleaks not yet run |
| Encryption | Partial | TLS and HSTS: the app adds HSTS outside local (`middleware.py:33-34`); TLS is the host's. Nothing is stored, so nothing needs encryption at rest | Verify HTTPS-only on the chosen host |
| CORS | Partial | Exact-origin allow-list required in production; no credentials; limited methods and headers | F5 (staging allows `*`) |
| Dependency security | Partial | `pip-audit` and `npm audit` in CI; Dependabot; ranges pinned only for scikit-learn and pandas | F8 lockfiles; audits unrun |
| Logging / monitoring | Partial | Structured logs, request IDs, redaction, no inputs or IPs logged. No error tracker, no alerts | F7 (verify), `docs/monitoring.md` is a plan |
| Admin security | N/A | No admin surface in the app. Host, GitHub and registry accounts: enable 2FA | F10 |
| Deployment / infrastructure | Partial | Startup refuses unsafe production config; docs off; separate staging/production documented | No host chosen; frontend headers missing (F9); no branch protection verified (F10) |
| Data privacy | Done | Nothing stored; no inputs or IPs in app logs; disclaimer shown. Provider logs outside scope | ADR 0005; check provider log settings |
| Error handling | Done, Verify | Generic 500 with request ID; detail only in logs; frontend shows plain-language errors with retry | `middleware.py:55-60`, `client.ts:describeError`, tests unrun |
| Backup / recovery | N/A for data | Nothing stored. The model file must be kept somewhere safe by the owner, with the previous version for rollback | `docs/runbooks/model-update.md`, `rollback.md` |
| Model integrity | Partial | Hash check (required in production), strict scikit-learn version check, column and category validation at load | F3, F12 |

## Before each release
1. Run backend and frontend tests, lint, typecheck, `pip-audit`, `npm audit`.
2. Re-read the threat-model findings and close or re-rate each.
3. Review the diff with a fresh pair of eyes, not the author, or a separate reviewer session.
4. Confirm production env: `APP_ENV=production`, `MODEL_SHA256` set, exact `CORS_ORIGINS`, `/docs` returns 404.
5. Send a forged `X-Forwarded-For` and a flood of requests at staging; confirm limits behave (F6, F11).
6. Try `<script>alert(1)</script>` in every text field and confirm nothing runs.
7. Confirm no addresses, inputs or tokens appear in the logs.

This is not a substitute for a professional audit if the app starts handling accounts, payments or stored health data.
