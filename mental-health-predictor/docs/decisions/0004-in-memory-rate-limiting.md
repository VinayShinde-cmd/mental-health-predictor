# 0004. In-memory rate limiting for a single instance

Status: accepted, with a known limitation

## Context
The playbook says in-memory counters reset on deploy and do not work across instances, and recommends a
shared store such as Redis. This service runs one instance and has no other need for Redis.

## Decision
A small sliding-window limiter in process memory, keyed by client IP, with separate limits for
`/api/predict` (default 30 per minute) and other `/api/*` routes (default 120 per minute). Health
endpoints are exempt so platform probes are never throttled. Returns 429 with `Retry-After` in the
standard error format.

The client IP is the socket peer address. If `TRUST_PROXY_HEADERS=true`, it is the last entry of
`X-Forwarded-For`, which assumes exactly one trusted proxy in front of the app.

## Alternatives considered
- Redis now: another service to run and pay for, for a limit that matters little at this scale.
- A third-party limiter library: new dependency for ~60 lines of logic.
- No limiting: the endpoint is anonymous and CPU-bound.

## Consequences
- Counters reset on every deploy or restart.
- With N instances the effective limit is N times higher.
- Behind a proxy with the setting off, every visitor shares the proxy's IP and could be limited
  together. Behind a proxy with the setting on but more than one proxy hop, the key can be spoofed.
- Before running more than one instance, replace this with a shared store.
