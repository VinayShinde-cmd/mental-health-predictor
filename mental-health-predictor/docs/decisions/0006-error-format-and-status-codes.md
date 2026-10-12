# 0006. One error format, and 400 for every invalid request

Status: accepted

## Context
The playbook asks for a consistent error shape and a clean 400 (not a stack trace) on garbage input.
FastAPI's defaults return 422 with its own shape and expose input values.

## Decision
Every error response has this body:

```json
{
  "error": {
    "code": "invalid_request",
    "message": "Some fields are invalid.",
    "request_id": "7c1f0e0b5d3a4c0f9a1d2b3c4d5e6f70",
    "details": [{ "field": "age", "message": "Input should be greater than or equal to 13" }]
  }
}
```

`details` appears only for field-level problems. Status codes: 400 invalid input (including malformed
JSON and unknown categories), 404 unknown route, 405 wrong method, 413 body too large, 429 rate limited
(with `Retry-After`), 500 unexpected error (generic message, details only in the logs), 503 health
check failing.

## Alternatives considered
- Keep FastAPI's 422: more precise, but the playbook's checklist and most clients expect 400.
- RFC 9457 problem+json: a fine standard, heavier than this API needs.

## Consequences
- The frontend maps `details[].field` to form fields, so field names in the API are the form keys.
- Pydantic's messages are shown to the user as-is. They never contain the submitted value.
