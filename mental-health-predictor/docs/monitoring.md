# Monitoring plan

Status: **plan only; nothing here is wired up.** The app produces the signals (structured logs, health
endpoints); no external monitor, error tracker or alerting is configured.

## What exists today
- JSON logs on stdout with a request ID on every line and one `request` line per request
  (method, path, status, duration).
- `GET /api/health/live` and `GET /api/health` (model canary prediction; 503 when failing).
- `X-Request-ID` response header, so a user-reported problem can be traced to log lines.

## Uptime checks to create (any free uptime service)
| Check | URL | Expect | Alert if |
| --- | --- | --- | --- |
| Site up | the frontend URL | 200 | 2 failures in a row (about 2 minutes) |
| API ready | `/api/health` | 200 | 2 failures in a row |
| Core flow | scheduled `POST /api/predict` with a fixed valid body | 200 and numeric score | 3 failures in a row |

## Metrics worth watching (from logs; no metrics system yet)
Error rate (`status >= 500`), p95 `duration_ms` for `/api/predict`, count of 429s, container memory.

## Alert rules (only things a human must act on)
| Alert | Threshold | Severity | Who | Runbook |
| --- | --- | --- | --- | --- |
| API down | health failing 2+ minutes | page | owner | `docs/runbooks/incident.md`, "API down" |
| Error spike | more than 5% of requests are 5xx for 10 minutes | notify | owner | incident.md, "Errors" |
| Slow predictions | p95 over 1 s for 15 minutes | notify | owner | incident.md, "Slow" |
| Memory near limit | over 85% for 10 minutes | notify | owner | incident.md, "Memory" |

## Not planned
Business metrics (signups, payments): there are none. Error tracking (for example Sentry): a good next
step; it needs an account and a DSN stored as an environment variable, and a decision that error events
must not include request bodies (ADR 0005).
