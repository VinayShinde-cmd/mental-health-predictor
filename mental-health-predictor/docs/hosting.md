# Hosting plan

Status: recommendation only. No prices are quoted: they change, and none were verified. Check each
provider's pricing page and set a billing alert before launch.

## Shape
| Component | What it needs | Typical fit |
| --- | --- | --- |
| Frontend | Static files, HTTPS, custom security headers | A static host (Vercel, Netlify, Cloudflare Pages) |
| Backend | One small always-on web service running Uvicorn, enough RAM for the model | A managed container/web service (Render, Railway, Fly.io) |
| Database, cache, queue | None | none |
| Model file | Private storage reachable at startup | See `docs/runbooks/model-update.md` |

Avoid serverless functions for the backend: cold starts would reload the model and import
scikit-learn/pandas on many requests.

## Sizing
Memory is the first constraint: Python + pandas + scikit-learn + the loaded forest. Measure with your real
model before picking a tier; the project's authors have not seen its file size.

## Environments
Keep staging and production separate: different `MODEL_PATH` copies, different hostnames, and
`APP_ENV=staging` vs `production`. There is no database to separate and no third-party API keys to
duplicate.

## Backend start command
```
uvicorn app.main:create_app --factory --host 0.0.0.0 --port $PORT --no-access-log --timeout-graceful-shutdown 20
```
- `--no-access-log`: the default access log prints client IPs (ADR 0005).
- `--timeout-graceful-shutdown`: lets in-flight requests finish when the platform stops the old instance.
- Health check path for the platform: `/api/health/live` (process) or `/api/health` (model).
- Behind the provider's proxy set `TRUST_PROXY_HEADERS=true` only if exactly one proxy hop sets
  `X-Forwarded-For`; otherwise every visitor shares one rate-limit bucket. Verify with the provider's docs.

## Environment variables
All listed with explanations in `backend/.env.example` and `frontend/.env.example`. Production requires
`APP_ENV=production`, `MODEL_PATH`, `MODEL_SHA256`, and exact `CORS_ORIGINS` (the frontend's origin).
The frontend needs `VITE_API_BASE_URL` at build time when it is on a different domain from the API.

## Headers the static host must add (the SPA's own page is not covered by the API's headers)
`Content-Security-Policy` (for example `default-src 'self'; connect-src 'self' <api origin>; img-src 'self' data:; frame-ancestors 'none'`,
adjusted after checking the built bundle), `X-Content-Type-Options: nosniff`, `Referrer-Policy: no-referrer`,
`Strict-Transport-Security`. Not configured in this repo yet (see `brain/security/`).

## Costs and budget
Unknown. Decide a ceiling, set billing alerts on every provider, and revisit `docs/system-design.md`
open question 3.

## At 10x traffic
Most likely change: more than one backend instance. That requires replacing the in-memory rate limiter
(ADR 0004) first. Nothing else is stateful.
