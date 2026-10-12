# 0005. Never store or log the user's inputs, predictions or IP addresses

Status: accepted

## Context
The inputs (sleep, stress, screen time, age, country) are health-adjacent personal data. Request logs are
the easiest place for such data to leak and to outlive its purpose.

## Decision
- Request logs contain only: event name, method, path, status, duration, request ID.
- No request bodies, response bodies, query strings, headers or client IPs are logged.
- Uvicorn's own access log (which prints client IPs) is switched off in the run commands; the
  application logs one structured line per request instead.
- Validation error responses name the field and the rule, never the submitted value.
- A redaction filter masks any log field whose name contains `password`, `token`, `secret`,
  `authorization`, `cookie` or `api_key`. These do not exist in this app today; the filter protects
  against future additions.

## Alternatives considered
- Log inputs to debug the model: gives useful data, but creates stored personal data with no consent flow.
- Keep Uvicorn's access log: includes IP addresses.

## Consequences
- Debugging a specific user's bad prediction is harder; use the request ID plus a reproduction.
- The platform in front of the app (load balancer, CDN) may still log IPs. That is outside this repo;
  check the provider's settings.
