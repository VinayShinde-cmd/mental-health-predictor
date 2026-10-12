# Secrets

No secret values appear in this file. It records where secrets would live, how configuration is handled, and
what was found. Nothing was changed.

## Where secrets are expected
**Today: none.** The application has no API keys, tokens, passwords, database URLs or private keys.
Every variable it reads is non-secret configuration (`backend/app/config.py`):

| Variable | Secret? | Notes |
| --- | --- | --- |
| `APP_ENV`, `LOG_LEVEL`, `RATE_LIMIT_*`, `TRUST_PROXY_HEADERS` | No | Behaviour switches |
| `MODEL_PATH` | No | A file path |
| `MODEL_SHA256` | No | A public-safe checksum; its value is integrity-sensitive, not confidential |
| `CORS_ORIGINS` | No | Public origins |
| `VITE_API_BASE_URL` (frontend, build time) | No | Compiled into public JavaScript on purpose |

Likely future secrets: an error-tracking DSN, hosting-provider deploy tokens, any storage credentials if
the model is fetched from a private bucket (`docs/runbooks/model-update.md`, step 6). When added they belong
in the host's secret store or GitHub Actions secrets, never in files.

The model file is an integrity-sensitive asset (see `threat-model.md`, T1) rather than a secret.

## Environment and configuration handling
- All configuration comes from environment variables, parsed once at startup, with a clear failure listing every problem (`config.py:load_settings`).
- `.env.example` files document every variable and contain no real values (checked: assignments hold defaults or are empty). `backend/.env.example`, `frontend/.env.example`.
- `.gitignore` excludes `.env` and `.env.*` (except `.example`) and everything in `backend/models/` except `.gitkeep`.
- Only variables prefixed `VITE_` are exposed to the browser by Vite; the only one used is `VITE_API_BASE_URL` (`frontend/src/api/client.ts:4`).
- Production start-up rules: `MODEL_SHA256` required, DEBUG logging refused, CORS wildcard refused (`config.py:95-109`).

## Hardcoded-secret risks
- None found. A pattern search of the repository (keywords such as key, secret, token, password, bearer,
  private-key headers, and common cloud/GitHub token shapes) matched only: the redaction list in
  `logging_config.py:17`, a `request_id_var` token handle in `middleware.py`, CSS "design tokens", and comments
  or docs. No value looked like a credential. This was a text search, not a dedicated scanner.
- Tests use dummy strings (`test_logging.py`) that are not credentials.
- No URLs or IDs are hard-coded in application code; the only external host names are in docs and CI config.

## Client-side exposure risks
- The bundle will contain the API base URL and nothing else configurable. No external scripts, fonts or
  analytics are loaded: fonts come from npm packages (`frontend/src/main.tsx:1-2`) and `index.html` has no external
  URLs (verified by search).
- Source maps are off (`frontend/vite.config.ts`: `sourcemap: false`), so the readable source is not shipped.
- Risk to watch: someone adding a `VITE_*` variable holding something sensitive. `frontend/.env.example` warns against it.

## Git and history exposure risks
- The directory is not a git repository yet, so there is no history to leak and no history scan could be done.
- Before the first push: run the gitleaks scan on the working tree (the pre-commit hook in
  `.pre-commit-config.yaml` does this per commit but has not been run), and confirm `git status` shows no `.env` or `.pkl`.
- The trained model is excluded from git on purpose. If Git LFS is chosen, keep the repository private.

## Logging and error exposure risks
- Request bodies, inputs, predictions and IP addresses are never logged (ADR 0005; `middleware.py:63-72`).
- A redaction filter masks fields named like secrets (`logging_config.py:17-31`). It only works for fields
  passed as structured `extra=` data, not text interpolated into a message string; the app does not log secrets today.
- Unexpected errors log a stack trace server-side only and return a generic message (`middleware.py:55-60`). Stack
  traces can include local variable values only if a library prints them; none do by default.
- Verify (finding F7): that the platform and Uvicorn's own logs do not record client IPs.

## Secret rotation requirements
Nothing to rotate today. When secrets are introduced:
- Rotate any key immediately if it appears in logs, a commit, a screenshot or a chat.
- Rotate deploy tokens when a team member leaves; prefer short-lived or scoped tokens.
- Changing the model means issuing a new `MODEL_SHA256` (not a secret, but it must be updated in lockstep).

## Actual findings with evidence
| # | Class | Severity | Finding | Evidence |
| --- | --- | --- | --- | --- |
| S1 | Observation | None | No secrets in the repository | Pattern search described above |
| S2 | Missing control | Low | No automated secret scan has run yet | `.pre-commit-config.yaml` and CI contain no executed gitleaks step; CI runs `pip-audit`/`npm audit` only (`ci.yml`) |
| S3 | Missing control | Low | No git history exists, so history was not scanned | Directory is not a git repository |
| S4 | Recommendation | Low | Add a gitleaks step to CI so scans are not only local | `ci.yml` |
