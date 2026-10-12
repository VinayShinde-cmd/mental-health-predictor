# Playbook coverage

How each layer of "Vibe Coding a Real SaaS: The 15-Layer Playbook" was applied to this project, sized to
what it is (a stateless prediction app, ADR 0002). "Not applicable" means the layer's risk does not exist
here, with the reason. Statuses are about what is in the repo, not what has been run.

| # | Layer | Status | What was done / why not |
| --- | --- | --- | --- |
| 0 | Agent setup | Done | `CLAUDE.md` + identical `AGENTS.md`, decision records, the "don't fool me" check in the final report |
| 1 | System design | Done | `docs/system-design.md` with out-of-scope list. Assumptions are flagged as open questions, not interviewed |
| 2 | Architecture | Done | `docs/architecture.md` (Mermaid), ADRs 0001 to 0006, layered folders |
| 3 | Databases and storage | Not applicable | Nothing is stored (ADR 0002). No backups or migrations to test. The model file is the one asset (`runbooks/model-update.md`) |
| 4 | Auth and permissions | Not applicable | Anonymous app, no tenants, no roles. No custom password code exists. Revisit with any account feature |
| 5 | APIs and backend logic | Done | Validation at the boundary, standard errors, thin routes, `docs/api-conventions.md`. No background jobs, payments or webhooks needed |
| 6 | Frontend | Done, unverified | Design tokens with dark mode, shared components, `#/design` page, loading/empty/error/success states, inline validation mirroring the server, labelled fields, axe tests written. Never rendered in a browser here |
| 7 | CI/CD and version control | Written, unrun | `.gitignore`, pre-commit config (ruff, gitleaks), GitHub Actions CI, Dependabot. No CD: deploys depend on the host chosen. No git history yet, so no history scan was possible |
| 8 | Testing | Partly run | See `docs/testing.md` for exactly what ran |
| 9 | Hosting and cloud | Plan only | `docs/hosting.md`, `runbooks/deploy.md`. Env vars validated at startup, none hard-coded. No host chosen, no prices verified |
| 10 | Security | Documented | `brain/security/` (four files). Controls in code: validation, headers, hash-pinned model, no input logging, docs off in production, dependency audit in CI. No automated review by a separate agent was run |
| 11 | Rate limiting | Partial | Per-IP in-memory limits with 429 + `Retry-After` (ADR 0004). No shared store, no per-plan limits (no plans), no cost caps (no paid API) |
| 12 | Caching and CDN | Minimal | `Cache-Control` set per endpoint (`no-store` for predictions). No Redis or app cache: not needed. CDN/long-lived asset caching is the static host's default; not verified |
| 13 | Error tracking and logs | Partial | Structured JSON logs, request IDs, redaction, no empty `catch` blocks (lint rule). Sentry-style tracking not integrated (needs an account) |
| 14 | Monitoring and alerts | Plan only | `docs/monitoring.md`, `runbooks/incident.md`; real `/api/health` and `/api/health/live`. No monitor or alert exists yet |
| 15 | Scaling | Not done | No load test. Known first limit: in-memory rate limiter on more than one instance |
| 16 | And more | Partly | Legal: a disclaimer is in the API and UI; terms and privacy policy not written. Analytics, flags, emails, admin, i18n: out of scope |

## Appendix B: pre-launch checklist
| Item | Status |
| --- | --- |
| Cross-tenant data access tested and blocked | N/A (no tenants) |
| Auth via a proven provider; no custom password handling | N/A (no auth); no custom password code exists |
| Every endpoint validates input; permissions on the server | Validation done; permissions N/A |
| Payments via verified, idempotent webhooks | N/A |
| CI blocks merges on failing tests; production deploy has rollback | CI written but unrun and branch protection not set; rollback documented |
| Critical flows covered by end-to-end tests | Written, unrun |
| Separate staging and production | Documented, not created |
| Backups enabled and a restore tested | N/A (nothing stored); model file backup is the owner's job |
| Security review done; dependencies audited | Docs written; `pip-audit`/`npm audit` run only in CI (unrun) |
| Rate limits on login, signup and expensive endpoints | Predict and options limited; no login/signup |
| No tenant data cached at shared layers | N/A; predictions are `no-store` |
| Errors reach a tracker; logs structured and redacted | Logs yes; tracker no |
| Uptime checks and alerts, each with a runbook | Planned only |
| Load tested at expected launch traffic | No |
| Billing alerts on every provider | Owner to do |
| Terms and privacy policy published | No |
