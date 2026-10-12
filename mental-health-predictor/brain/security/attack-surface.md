# Attack surface

Everything an outsider (or a dependency) can reach in this project, taken from the code. Assessment limits as
in `threat-model.md`: read from source, not tested against a running instance. Nothing was changed.

## Public endpoints
All are unauthenticated. Rate limiting applies where noted. Defined in `backend/app/routes/`.

| Endpoint | Input | Output | Rate limit | Notes |
| --- | --- | --- | --- | --- |
| `GET /api/health/live` | none | `{"status":"ok"}` | none (exempt on purpose) | `health.py:15` |
| `GET /api/health` | none | model health, 200 or 503 | none (exempt) | Runs a canary prediction on every call (`model_service.py:is_healthy`), so it costs CPU and is unthrottled (finding **A1**) |
| `GET /api/options` | none | dropdown values, numeric limits | "general", 120 per minute per IP | `predict.py:17`, cached 5 minutes |
| `POST /api/predict` | JSON, 12 fields | score, band, warnings, disclaimer, model ID | "predict", 30 per minute per IP | `predict.py:34`, `no-store` |
| `OPTIONS /api/*` | CORS preflight | CORS headers | handled by CORS middleware, before limiter | Only when `CORS_ORIGINS` is set (`main.py:56`) |
| `GET /docs`, `/redoc`, `/openapi.json` | none | interactive API docs | none | Disabled when `APP_ENV=production` (`main.py:45`) |
| Static frontend | none | HTML, JS, CSS | host's | Hosted separately; `#/design` page is public |

Any other path returns the standard 404 JSON (`errors.py`).

## Internal endpoints
None. There is no admin, debug, metrics or internal route. (`/api/health` is public.)

## Authentication and authorisation surfaces
None exist. No login, sessions, cookies, tokens, roles or tenant scoping (ADR 0002). Consequently no
privilege-escalation or IDOR surface, and also no way to attribute or individually limit callers beyond IP.

## User inputs
| Input | Where it enters | Handling |
| --- | --- | --- |
| 12 JSON body fields | `POST /api/predict` | Pydantic: types, bounds, no extras, no NaN/inf (`schemas.py`); strings capped at 40 or 80 chars; categories matched to the model's list (`model_service.py:prepare_row`); country grouped, never used as a key or path |
| `X-Request-ID` header | every request | Accepted only if it matches `^[A-Za-z0-9._-]{8,64}$`, else replaced (`middleware.py:21,44`); used in logs and echoed back |
| `Content-Length` header | every request | Compared to a 10 KB cap (`middleware.py:49-50`) |
| `Origin`, `Access-Control-Request-*` | preflight | Matched against the allow-list by Starlette's CORS middleware |
| `X-Forwarded-For` | rate limiting, only if `TRUST_PROXY_HEADERS=true` | Last entry, must parse as an IP (`rate_limit.py:57-65`) |
| Frontend form fields | browser | Validated client-side with the server's limits (`validation.ts`), but the server does not trust that |
| URL hash (`#/design`) | browser | Compared with one fixed string (`App.tsx`); not used otherwise |
| Server responses | browser | Rendered as text by React; no HTML injection API is used |

Values from the body are never used to build SQL, shell commands, file paths, URLs, templates or redirects.

## File uploads
None. No endpoint accepts files or multipart data.

## Database access
None. No database, ORM or query code.

## Storage
- **Model file:** read once at startup from `MODEL_PATH` (`model_service.py:94-104`). Read-only use. Contents are executed during unpickling, so the file's integrity is security-critical (T1).
- **Logs:** JSON to standard output (`logging_config.py`). Retention is the host's.
- **Browser storage:** none used by the frontend.
- No user data is written anywhere.

## Webhooks
None, inbound or outbound.

## Third-party integrations
None at runtime. The backend makes no outbound requests. The frontend loads no third-party scripts, fonts
or analytics (fonts are bundled from npm packages). Build-time and operational third parties: GitHub and
GitHub Actions (CI), package registries (PyPI, npm), the chosen host(s). Not yet chosen or configured.

## Admin surfaces
None in the application. The hosting dashboard, GitHub repository settings and package-registry accounts
are admin surfaces outside this repo (finding F10).

## Network and deployment exposure
- One HTTP service (Uvicorn) expected behind the host's HTTPS proxy. HSTS is added by the app outside `local` (`middleware.py:33-34`); TLS itself is the host's job.
- No other ports, databases, queues or SSH access are part of the design.
- CORS: allow-list from `CORS_ORIGINS`; methods limited to GET, POST, OPTIONS; no credentials allowed (`main.py:56-62`).
- The API's own responses carry CSP, `X-Frame-Options`, `nosniff`, `Referrer-Policy` (`middleware.py:23-34`); the static site's headers are not configured in this repo (finding **F9**).
- Docs and OpenAPI are exposed in `local` and `staging`, off only in `production`.

## Dependencies and other externally reachable surfaces
Direct dependencies (versions in `backend/requirements.txt`, `frontend/package.json`):
- Python: fastapi, uvicorn, python-dotenv, pydantic, scikit-learn, pandas, numpy, joblib. Dev: pytest, httpx, ruff, mypy, pip-audit.
- JavaScript runtime: react, react-dom, two fontsource font packages. Dev: vite, vitest, typescript, eslint and friends, Testing Library, axe-core, Playwright.
- No lockfile is committed for either ecosystem (finding **F8**), and audits have not been run.
- Pickle loading via joblib is itself an attack surface (T1).
- CI: GitHub Actions with `contents: read` only (`ci.yml:10-11`); actions are referenced by version tag (`@v4`, `@v5`), not commit SHA.

## Surface-specific findings
| ID | Class | Severity | Finding | Evidence | Fix |
| --- | --- | --- | --- | --- | --- |
| A1 | Security weakness | Low to Medium | `/api/health` is unthrottled and runs a model prediction per call, so it can be used to burn CPU | `routes/health.py:22-26`; limiter is attached only to options and predict (`routes/predict.py:17,34`) | Rate limit by IP with a generous limit, or cache the canary result for a few seconds |
| A2 | Missing control | Low | No limit on request rate before body parsing, and no host-level protection configured | see F6 in `threat-model.md` | Apply limits at the proxy/CDN |
| A3 | Recommendation | Low | Pin GitHub Actions to commit SHAs | `ci.yml` uses tags | Pin and let Dependabot update them (config exists) |
| A4 | Potential risk requiring verification | Low | Interactive docs stay on in `staging` | `main.py:45` only checks `is_production` | Decide whether staging should be public; if not, protect or disable it |
