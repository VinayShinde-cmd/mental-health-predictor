# Project: Habit gauge (mental-health score estimator)

## What this product does
A web form where a person enters 12 facts about their phone use, sleep, study, activity, stress and
background, and sees a wellbeing score estimated by a random-forest model trained in `code.ipynb` on a
student survey (5,000 rows). The result is an estimate placed on a ruler, never a diagnosis.
Anonymous users, nothing is stored.

## Stack (do not change without asking)
- Frontend: React 19 + TypeScript (strict) + Vite, hand-written CSS tokens. Hosted as static files.
- Backend: Python 3.12+ / FastAPI + Uvicorn. Pydantic v2 validation.
- ML: scikit-learn pipeline loaded with joblib at startup. scikit-learn version must match training.
- Database: none (ADR 0002). Auth: none. Hosting: static host + one small web service.
- Tests: pytest (backend), Vitest + Testing Library + axe-core (frontend), Playwright (one e2e flow).

## Architecture
Modular monolith. Layers in `backend/app/`: `routes/` (thin) -> `services/` (logic) -> `domain/` (plain
Python, no framework imports). Config in `config.py`, errors in `errors.py`, logging in
`logging_config.py`, cross-cutting request handling in `middleware.py`. Details: `docs/architecture.md`.

## Rules
- Never commit secrets. All config is environment variables, documented in `.env.example` files, and
  validated at startup (`backend/app/config.py`). No URLs, keys or IDs hard-coded.
- Never log request bodies, user inputs, predictions or client IPs (ADR 0005).
- Every endpoint: validate input at the boundary, return errors in the standard format
  (`docs/api-conventions.md`), have tests including bad input.
- Server is the source of truth for validation. Frontend mirrors the limits from `/api/options`.
- Unknown categories are rejected, never silently ignored.
- Never edit a test to make it pass. If a test reveals a bug, stop and report it.
- Never load a model file that has not been verified (`MODEL_SHA256`); never loosen the scikit-learn
  version check.
- Ask before adding a dependency. Every dependency needs a one-line reason in `requirements.txt` or the PR.
- No `dangerouslySetInnerHTML`; render server text as text.
- Small, reviewable changes. One feature per branch. Conventional Commits (`feat:`, `fix:`, `docs:`...).
  Never push directly to main.
- Run lint, typecheck and tests before saying a task is done, and show the output.
- Update this file and `docs/decisions/` whenever a decision is made.

## Commands
- Backend dev (from `backend/`): `uvicorn app.main:create_app --factory --no-access-log --reload --env-file .env`
- Backend tests: `pytest`
- Backend lint/types: `ruff check . && ruff format --check . && mypy app scripts`
- Synthetic stand-in model (tests/smoke only, never deploy): `python -m scripts.make_dev_model`
- Frontend dev (from `frontend/`): `npm run dev`
- Frontend checks: `npm run lint && npm run typecheck && npm test && npm run build`
- End-to-end (backend and dev server running): `npm run e2e`

## Known limitations (read before "fixing")
- Rate limiting is in memory and per instance (ADR 0004).
- The real model file is not in git; see `docs/runbooks/model-update.md`.
- Higher score = better wellbeing is an assumption (docs/system-design.md, open question 1).

## Architecture decisions
See `docs/decisions/`.
