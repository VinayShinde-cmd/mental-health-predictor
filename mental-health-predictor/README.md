# Habit gauge

A web app around the model trained in `code.ipynb`: fill in 12 questions about phone use, sleep, study,
activity, stress and background, and see an estimated wellbeing score on a ruler. It is an estimate from a
student survey dataset, not a diagnosis.

- **Frontend:** React + TypeScript + Vite (`frontend/`)
- **Backend:** FastAPI (`backend/`), loads your pickled scikit-learn pipeline once at startup
- **No database, no accounts, nothing stored.** Inputs and IP addresses are never logged.

> **Status:** written in an environment that could not install packages. The backend's non-HTTP logic is
> tested (64 passing tests); the HTTP tests, the whole frontend, CI and the browser flow have **not been run**.
> See [docs/testing.md](docs/testing.md) for the exact record, and expect small fixes on your first run.

## Run it locally

You need Python 3.12+ and Node 20+ (22 recommended).

### 1. Backend
```bash
cd backend
python -m venv .venv && source .venv/bin/activate        # Windows: .venv\Scripts\activate
```
Edit `requirements.txt` so `scikit-learn`, `pandas` and `numpy` match the versions in your notebook
(`import sklearn; print(sklearn.__version__)`). The app refuses a model saved by a different scikit-learn version.
```bash
pip install -r requirements-dev.txt
cp .env.example .env                                     # then set MODEL_PATH
```
Put your exported `Mental_Health_Model2.pkl` in `backend/models/` and keep `MODEL_PATH=models/Mental_Health_Model2.pkl`.
No model yet? Create a **synthetic** stand-in (random data, meaningless predictions) to try the app:
```bash
python -m scripts.make_dev_model                         # writes models/DEV_SYNTHETIC_model.pkl
# then set MODEL_PATH=models/DEV_SYNTHETIC_model.pkl in .env
```
Start the API:
```bash
uvicorn app.main:create_app --factory --no-access-log --reload --env-file .env
```
Check http://localhost:8000/api/health and the interactive docs at http://localhost:8000/docs (local only).
If a setting is missing or wrong, the app stops at startup and says which one.

### 2. Frontend
```bash
cd frontend
npm install
npm run dev
```
Open http://localhost:5173. The dev server forwards `/api` to the backend on port 8000. The design system
page is at http://localhost:5173/#/design.

After the first `npm install`, commit `package-lock.json`; after your first `pip install`, run
`pip freeze > requirements.lock.txt` and deploy from it.

## Checks
```bash
cd backend  && pytest && ruff check . && ruff format --check . && mypy app scripts
cd frontend && npm run lint && npm run typecheck && npm test && npm run build
cd frontend && npm run e2e          # with backend and `npm run dev` running
```

## API
| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/api/health/live` | Process is up |
| GET | `/api/health` | Model loaded and answering a test input |
| GET | `/api/options` | Dropdown values (from the model) and numeric limits |
| POST | `/api/predict` | The 12 inputs in, score + band + warnings out |

Conventions and error format: [docs/api-conventions.md](docs/api-conventions.md).

## Project map
```
CLAUDE.md / AGENTS.md   rules for coding agents          docs/            design, decisions, runbooks
backend/app/            routes -> services -> domain      brain/security/  threat model and checklists
frontend/src/           components, hooks, styles         .github/         CI and Dependabot
```
Start with [docs/system-design.md](docs/system-design.md), [docs/architecture.md](docs/architecture.md),
[docs/playbook-coverage.md](docs/playbook-coverage.md) and [brain/security/](brain/security/).

## Things to know about the model
Test R² 0.865 vs train 0.955 (some overfitting), and `Stress_Level` is both an input and closely related to
the target. The dataset looks unusually clean. See "Known issues with the model" in
[docs/system-design.md](docs/system-design.md) before presenting results as meaningful.
