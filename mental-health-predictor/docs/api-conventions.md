# API conventions

The API is small, but the rules are written down so new endpoints match.

## URLs and naming
- All routes live under `/api`. Nouns, lowercase, no trailing slash: `/api/predict`, `/api/options`.
- JSON field names are `snake_case` and equal the frontend's form keys.
- Health: `GET /api/health/live` (process up, for the load balancer) and `GET /api/health` (model loaded
  and answering a fixed test input; 503 if not).

## Validation
- Pydantic models in `backend/app/schemas.py`, applied at the boundary. `extra="forbid"`: unknown fields
  are rejected.
- Numeric limits live once, in `backend/app/domain/features.py`, and are published through
  `GET /api/options` so the frontend enforces the same numbers.
- Category values are checked against the loaded model, not a hard-coded list.
- Inputs outside the training range but inside the plausible limits are accepted and return `warnings`.

## Error format
Defined in ADR 0006. Every non-2xx response:

```json
{ "error": { "code": "rate_limited", "message": "Too many requests. Wait a moment and try again.",
             "request_id": "…", "details": [{ "field": "age", "message": "…" }] } }
```
`details` only for field problems. The submitted value is never echoed.

| Status | `code` | When |
| --- | --- | --- |
| 400 | `invalid_request` | Malformed JSON, missing/extra/out-of-range field, unknown category |
| 404 | `not_found` | Unknown route |
| 405 | `method_not_allowed` | Wrong method |
| 413 | `payload_too_large` | `Content-Length` over 10,000 bytes |
| 429 | `rate_limited` | Over the per-IP limit; `Retry-After` header in seconds |
| 500 | `internal_error` | Unexpected failure; generic message, detail only in logs |
| 503 | (health body) | `/api/health` model check failing |

## Auth and organisation context
None: the API is anonymous and has no organisations (ADR 0002). There is no `can()` function or
permissions matrix because there is nothing to authorise. Adding either is a design change, not a patch.

## Pagination
No list endpoints exist. Any future list endpoint must use cursor pagination.

## Headers
- Every response: `X-Request-ID` (echoed if the caller sends a well-formed one, otherwise generated),
  `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`, `Content-Security-Policy`
  (not on `/docs`), and `Strict-Transport-Security` outside `local`.
- `POST /api/predict`, health: `Cache-Control: no-store`. `GET /api/options`: `public, max-age=300`
  (identical for everyone, changes only when the model changes).

## Slow work
A prediction runs inline (milliseconds). Anything over about a second must move to a background job.
