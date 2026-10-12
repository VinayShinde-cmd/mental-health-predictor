# Threat model

Scope: the project as it exists in this repository (backend, frontend, CI config, docs). Based only on what
the code and config do. **Limits of this assessment:** nothing was exploited or dynamically tested. The HTTP
layer (FastAPI), the frontend build and the CI pipeline could not be run where this was written, so claims
about runtime behaviour are from reading the code and are marked "verify" where it matters. Nothing was
fixed as part of this review.

## Assets
| Asset | Why it matters | Where |
| --- | --- | --- |
| A1. Visitors' inputs (age, country, sleep, stress, screen time) | Health-adjacent personal data. Never stored or logged by design | In memory during one request: `backend/app/routes/predict.py`, `services/model_service.py` |
| A2. The trained model file | Integrity matters: unpickling executes code. Also the product's core value | `MODEL_PATH`, loaded in `services/model_service.py:95-104` |
| A3. Service availability | The estimate endpoint is CPU-bound and anonymous | `routes/predict.py:34` |
| A4. Trust in the estimate | A wrong or manipulated score shown as meaningful could mislead users about their wellbeing | `domain/interpretation.py`, frontend `ResultPanel.tsx` |
| A5. Operator access (host, GitHub, package registries) | Compromise would let an attacker replace code or the model | Outside the repo |
| A6. Logs | Must not accumulate personal data | `logging_config.py`, `middleware.py:63-72` |

## Actors
| Actor | Description |
| --- | --- |
| Anonymous visitor | Intended user. Can reach every public endpoint |
| Malicious visitor / bot | Scrapes, floods, sends malformed or hostile input, tries to read other people's data (there is none to read) |
| Malicious website | Makes a visitor's browser call the API cross-origin |
| Supply-chain attacker | Publishes or hijacks a dependency |
| Insider / compromised operator account | Can change the model file, env vars, code, or CI |
| Curious user | Reads the page's JavaScript, the API's responses, `/docs` (outside production) |

## Trust boundaries
1. Internet <-> API (everything inbound is untrusted): validated by Pydantic at `schemas.py`, categories checked in `model_service.py:prepare_row`.
2. Browser <-> static host: the SPA is public code; nothing secret is in it (`frontend/src/api/client.ts:4` reads only the API base URL).
3. API process <-> model file: file contents are trusted *after* the hash check (required only in production, `config.py:95-96`).
4. API <-> reverse proxy: client IP and `X-Forwarded-For` are trusted only if `TRUST_PROXY_HEADERS=true` (`rate_limit.py:57-65`).
5. Repository <-> CI / registries / hosting: outside the code, controlled by the owner.

## Entry points
`GET /api/health/live`, `GET /api/health`, `GET /api/options`, `POST /api/predict`, CORS preflight `OPTIONS`,
`GET /docs` `/redoc` `/openapi.json` (not in production, `main.py:45`), the static frontend, request headers
(`Origin`, `X-Request-ID`, `Content-Length`, and `X-Forwarded-For` when trusted), environment variables at
startup, the model file path, dependency installation. Full list: `attack-surface.md`.

## Threats, scenarios, impact, likelihood, severity
Impact and likelihood are judgements for a small anonymous app: Low / Medium / High.

| ID | Threat | Attack scenario | Impact | Likelihood | Severity | Existing mitigations | Missing mitigations |
| --- | --- | --- | --- | --- | --- | --- | --- |
| T1 | Code execution via a malicious model file (insecure deserialization) | Attacker who can write the model file or the deploy pipeline swaps in a crafted pickle | High (full process takeover) | Low | **Medium** | SHA-256 verified before load; required in production (`config.py:95-96`, `model_service.py:95-101`); model path comes from env, never from a request | Hash optional outside production; hash lives in the same trust domain as the file; no signed artefacts (F3) |
| T2 | Denial of service on `/api/predict` | Bot sends thousands of requests; each runs a forest prediction | Medium (slow or down) | Medium | **Medium** | Per-IP limit 30/min, 429 + `Retry-After` (`dependencies.py`, `rate_limit.py`); 10 KB body cap by header (`middleware.py:49-50`) | Per-instance, in memory (F1); soft memory bound (F2); chunked bodies uncapped (F4); no WAF/CDN limits; malformed JSON may skip the limiter (F6, verify) |
| T3 | Limiter evasion or collateral blocking via IP handling | Behind a proxy with `TRUST_PROXY_HEADERS` wrong: attacker rotates a spoofed header, or all users share one bucket | Medium | Medium | **Medium** | Header trusted only when explicitly enabled; last entry only; value must parse as an IP (`rate_limit.py:57-65`) | Assumes exactly one proxy hop; no check that the peer is the proxy |
| T4 | Malicious input (injection, XSS, oversized or odd values) | Sends `<script>` in a text field, NaN, huge numbers, extra fields | Low | High (attempted) | **Low** | `extra="forbid"`, numeric bounds, `allow_inf_nan=False` (`schemas.py`); categories matched against the model's own list; values never echoed in errors (`errors.py:66-72`); no SQL, shell, file or template use of input; React renders text only; ESLint bans `dangerouslySetInnerHTML` (`frontend/eslint.config.js`) | HTTP-level tests exist but were not run |
| T5 | Cross-site abuse of the API from another website | Hostile page makes visitors' browsers call `/api/predict` | Low (no cookies, no state change, no stored data) | Medium | **Low** | CORS allow-list in production (`main.py:56-62`, `config.py:100`); nothing is authenticated, so CSRF has nothing to ride on | `*` allowed in non-production envs, including `staging` (F5) |
| T6 | Personal data leaking through logs or provider logs | Inputs or IPs end up in logs a third party can read | Medium | Low | **Low** | Only method, path, status, duration and request ID logged (`middleware.py:63-72`); Uvicorn access log disabled (`logging_config.py:65`); redaction filter | Provider/proxy logs are outside this repo; the Uvicorn-disable relies on runtime behaviour (F7, verify) |
| T7 | Supply-chain compromise | A malicious or vulnerable release of a dependency is installed | High | Low to Medium | **Medium** | `pip-audit` and `npm audit` steps in CI (unrun); Dependabot config; CI token is read-only (`ci.yml:10-11`) | No lockfiles committed, so versions float (F8); `fastapi`, `uvicorn` etc. are lower-bounded not pinned |
| T8 | Misleading output treated as clinical truth | User or a third party uses a score as a diagnosis | Medium | Medium | **Medium** | Disclaimer in every API response and in the UI; bands described relative to survey respondents (`interpretation.py`); out-of-range warnings | Model quality caveats (overfitting, near-duplicate input, possibly synthetic data) are documented but not surfaced in the UI |
| T9 | Information disclosure about internals | Reads `/docs`, stack traces, version strings | Low | Medium | **Low** | `/docs` off in production (`main.py:45`); generic 500 (`middleware.py:55-60`); standard error format | Model ID (hash prefix) is returned on every prediction (low value); `/api/health` reveals model state to anyone |
| T10 | Weak or missing browser protections on the static site | Clickjacking or script injection into the SPA page itself | Medium | Low | **Medium** | API sets CSP/X-Frame-Options for its own responses | No CSP, framing or HSTS config for the frontend host in this repo (F9) |
| T11 | Compromise of operator accounts or CI | Attacker with repo or host access changes code, model or env | High | Low | **Medium** | Least-privilege CI permissions; `.gitignore` for env files; docs urge branch + PR | Branch protection, 2FA and secret scanning are repo/host settings not verified here (F10) |

## Findings
Format: Severity -> Evidence -> Risk -> Affected location -> Why it matters -> Recommended fix.
Classes: **Confirmed vulnerability**, **Security weakness**, **Missing control**, **Potential risk requiring verification**, **Recommendation**.

### Confirmed vulnerability
None. Nothing was run against a live instance, so no vulnerability could be confirmed dynamically.

### Security weakness (present in the code today)
**F1. Rate limiting is per instance and in memory.** Severity: Medium.
Evidence: counters are a process-local dict (`backend/app/rate_limit.py:29`); documented in ADR 0004.
Risk: resets on every restart and multiplies with each extra instance. Affected: `rate_limit.py`, `dependencies.py`.
Why it matters: the limiter is the only abuse control on an anonymous, CPU-bound endpoint.
Fix: acceptable for one instance; move to a shared store (for example Redis) before scaling out, and add limits at the host or CDN.

**F2. The limiter's memory bound is soft.** Severity: Low.
Evidence: when `len(_hits) >= max_keys`, only *expired* keys are purged (`rate_limit.py:36-37, 47-50`); with 10,000 or more *active* keys nothing is evicted.
Risk: a flood from many distinct IPs (or spoofed addresses if proxy headers are mis-trusted) grows memory within a minute window.
Why it matters: memory is the app's first resource limit (`docs/system-design.md`).
Fix: when still over the cap after purging, reject new keys or evict the oldest; keep host-level limits as a backstop.

**F4. Body size cap trusts the `Content-Length` header only.** Severity: Low.
Evidence: `middleware.py:49-50` checks the declared length; there is no check on streamed or chunked bodies.
Risk: an oversized chunked body bypasses the cap. Affected: `middleware.py`.
Why it matters: bounds memory use per request. Fix: enforce the limit while reading the body, or configure it at the reverse proxy.

**F5. CORS wildcard is allowed outside production.** Severity: Low.
Evidence: only `production` rejects `*` (`config.py:100-101`); `staging` accepts it.
Risk: a staging deployment could be callable from any website. Why it matters: staging often holds near-production config. Fix: reject `*` for `staging` too, or document it as local-only.

**F3. The model hash is optional outside production, and sits beside the file it protects.** Severity: Low to Medium.
Evidence: `config.py:95-96`, `model_service.py:96`.
Risk: in staging or local, an unverified pickle is loaded; in production, anyone able to change the environment variable can also change the file. Why it matters: see T1.
Fix: require the hash in staging; consider moving to a non-executable model format (for example ONNX) in the longer term.

### Missing control
**F8. No lockfiles.** Severity: Medium. Evidence: no `package-lock.json` or `requirements.lock.txt` in the repo; `backend/requirements.txt:12-15` uses lower bounds for `fastapi`, `uvicorn`, `python-dotenv`, `pydantic`; frontend uses caret ranges. Risk: builds can silently pick up a new, possibly compromised release. Fix: generate and commit lockfiles after first install; deploy with `npm ci` and the pinned Python file.

**F9. No browser security headers for the frontend host.** Severity: Medium. Evidence: no `_headers`, `vercel.json`, `netlify.toml` or CSP meta tag in `frontend/`; `docs/hosting.md` lists what to add. Risk: no CSP or framing protection on the SPA page. Fix: add the headers at the static host and test the CSP against the built bundle.

**F10. Repository and account protections are not verified.** Severity: Medium. Evidence: none of branch protection, required checks, 2FA or secret scanning can be seen from the code. The pre-commit gitleaks hook and CI have not been run. Fix: enable branch protection with CI required, 2FA on GitHub and the host, and run the gitleaks scan once on the full history.

**M-auth. No authentication or authorisation.** Severity: accepted design (Medium if the endpoint ever becomes costly). Evidence: ADR 0002; no auth code exists. Fix: none now; revisit if per-user quotas or stored data are added.

**M-track. No error tracking or alerting.** Severity: Low. Evidence: `docs/monitoring.md` is a plan only. Fix: add monitoring before launch.

### Potential risk requiring verification
**F6. Malformed or invalid JSON may not count against the rate limit.** Severity: Low to Medium. Evidence: the limiter is a route dependency (`routes/predict.py:34`); FastAPI parses the JSON body before dependencies run, which would mean unparseable bodies get a 400 without being counted. Not verified because FastAPI could not be run. Fix: if confirmed, apply the limiter as middleware or before body parsing.

**F7. Uvicorn's access log (which includes client IPs) might not be fully disabled.** Severity: Low. Evidence: the app sets `uvicorn.access` to disabled (`logging_config.py:65`) and the run commands pass `--no-access-log`, but behaviour when Uvicorn configures logging was not observed. Fix: start the server once and confirm no IP addresses appear in output; keep the flag in every start command.

**F11. Behaviour of `TRUST_PROXY_HEADERS` on the chosen host.** Severity: Medium if wrong. Evidence: the rule assumes one proxy hop (`ADR 0004`). Fix: check the provider's proxy behaviour before setting it, then test with a forged `X-Forwarded-For`.

**F12. Real-model behaviour.** Evidence: the real model file was never available, only a synthetic stand-in. Whether its pickle structure matches `model_service.py`'s expectations (`preprocessor` step, `Normal` transformer, `feature_names_in_`) is unverified. Failure mode is a startup error, not a security flaw, but it should be confirmed.

### Recommendation
- Run the HTTP test file and a dependency audit once packages are installable, and treat any failure as a finding.
- Have someone other than the author review the diff (playbook rule 7). AI review is not a substitute for a professional audit if the app ever handles real health data or accounts.
- Decide and document the model's storage location and who may write to it (`docs/runbooks/model-update.md`).

## Existing mitigations (summary, each backed by code)
Startup config validation (`config.py`), request validation (`schemas.py`), category whitelist from the model
(`model_service.py`), standard errors without echoing input (`errors.py`), request IDs validated by regex
(`middleware.py:21`), security headers (`middleware.py:23-34`), docs disabled in production (`main.py:45`),
CORS allow-list (`main.py:56-62`), rate limiting (`rate_limit.py`), no input/IP logging (`middleware.py`,
`logging_config.py`), hash-pinned model and strict scikit-learn version check (`model_service.py`),
`no-store` on predictions (`routes/predict.py:41`), no raw-HTML rendering and a lint rule forbidding it
(`frontend/eslint.config.js`), least-privilege CI token (`ci.yml:10-11`).
