# Testing

## Strategy
| Level | Tool | What it covers | Mocked |
| --- | --- | --- | --- |
| Unit | pytest | config, logging redaction, rate limiter, score bands, model loading and prediction | Nothing from scikit-learn. A synthetic pipeline with the notebook's structure is trained for real. One test fakes `joblib.load` to emit a version warning |
| HTTP | pytest + FastAPI TestClient | status codes, error format, headers, rate limiting, CORS, logging policy | Nothing. A fault is injected by swapping the model's pipeline for a failing object |
| Frontend unit | Vitest | validation rules, parsing | Nothing |
| Frontend UI | Vitest + Testing Library + axe-core | loading, error + retry, empty, success, server errors, rate limit, pending, XSS text rendering, accessibility | `fetch` (the backend is external to the frontend) |
| End-to-end | Playwright | fill form and get an estimate, empty submit, 375 px width, API down | Nothing; runs against a real backend |

Never mocked: our own validation, our own model-loading and prediction code.
The synthetic model proves the code paths work; it says nothing about the real model's quality.

## Running
```
cd backend  && pytest && ruff check . && ruff format --check . && mypy app scripts
cd frontend && npm run lint && npm run typecheck && npm test && npm run build
cd frontend && npm run e2e        # backend + `npm run dev` running
```

## Status when this was written (honest record)
Environment: the sandbox this project was built in could not reach PyPI or npm.

| Check | Result |
| --- | --- |
| Backend unit tests (config, logging, rate limiter, domain, model service) | 64 passed |
| `ruff check`, `ruff format`, `mypy app scripts` | clean |
| Deliberate break (score-band boundary changed) | caught by `test_bands_follow_the_training_quartiles` |
| Backend HTTP tests (`tests/test_api.py`, 25 test functions) | **not run**: FastAPI and httpx not installable here. Skipped with a stated reason by `importorskip` |
| Frontend validation logic | 14 assertions run via Node type-stripping in a scratch script; Vitest suite itself **not run** |
| Frontend UI tests, lint, typecheck, build | **not run** (no npm packages) |
| Playwright e2e, real-browser look at the UI, 375 px check | **not run** |
| CI workflow, pre-commit config | **not run** |
| Load test, scaling checks | **not done** |

Treat every "not run" row as unverified until you have run it. Expect to fix small things on first run.

## Colour contrast (computed, WCAG 2.1 ratios)
Light: ink on paper 13.1, secondary text on paper 6.4, input border on panel 3.1, button text on accent 6.1,
error text on panel 6.5, notice text 7.4. Dark: ink on paper 14.6, secondary 8.8, input border 3.5,
button text 9.0, error 8.9, notice 10.1. The marker's visibility comes from its 3 px ink outline, not its fill.

## Not done
- Coverage measurement; a 70 to 80 percent target on `services/` and `domain/` is sensible once measured.
- Load testing (playbook layer 15). Needs the real model and a staging host.
- A manual keyboard-only and phone pass (playbook layer 6 "Verify").
- Test quality review (playbook 8d): after the first full run, grep for `skip`, `xit`, `importorskip`
  and confirm none hide real gaps.
