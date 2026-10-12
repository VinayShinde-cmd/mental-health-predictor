# Runbook: incidents

## Declaring and communicating
1. Decide it is an incident if estimates fail or are wrong for real users for more than a few minutes.
2. Post a short notice where users will see it (the site, or wherever you shared the link): what is broken, since when, next update time.
3. Fix first, then write the review (template below). Keep updates short and factual.

## Common cases
**API down.** Check the host's dashboard and logs. Search logs for `startup_complete`. If missing, the
app failed at startup: the message names the problem (bad config, model file missing, hash mismatch,
scikit-learn version mismatch). Fix the setting or roll back (`rollback.md`).

**Errors (5xx).** Find a failing request ID (users can send the `X-Request-ID` from the failed
response). Search logs for that ID; `unhandled_error` lines carry the stack trace.

**Slow.** Check `duration_ms` on `request` lines and memory use. Memory pressure shows up as slowness first. Try
the next size up.

**Memory.** Compare with the model file size; restart if growth continues, then investigate.

**Everyone is rate limited.** If many users get 429s together, the proxy's address is probably being used
as the client IP: check `TRUST_PROXY_HEADERS` against the host's proxy setup (`hosting.md`).

## Post-incident review template
- What happened, in two sentences.
- Timeline (start, detection, fix).
- Cause.
- What would have caught it sooner.
- Follow-ups, each with an owner and a date.
