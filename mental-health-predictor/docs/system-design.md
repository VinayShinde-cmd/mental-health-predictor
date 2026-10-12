# System design

Status: draft v1. Written before the code, as the playbook asks (layer 1). Assumptions that the owner
has not confirmed are listed under "Open questions". Nothing here was invented to sound complete: where
a number is an assumption, it says so.

## Problem statement

A random-forest regressor was trained in `code.ipynb` on 5,000 survey rows (`Student Social Media And
Mental Health Impact.csv`) to predict `Mental_Health_Score` (observed range 3.6 to 9.4) from 12 inputs
about a student's phone use, sleep, study, activity, stress and background.

This project puts that model behind a small web app: a person fills in a form and sees the model's
estimate, placed against the range seen in the training data.

The estimate is a statistical output from a survey dataset. It is not a diagnosis, and the UI and API
say so every time.

## Users and roles

| Role | What they do | Authentication |
| --- | --- | --- |
| Visitor | Opens the page, enters the 12 inputs, reads the estimate | None (anonymous) |
| Operator (the owner) | Deploys the service, replaces the model file, watches logs | Hosting-provider login, outside the app |

There are no user accounts, organisations or roles inside the app. See ADR 0002.

## Core user flows

1. **Estimate.** Visitor opens the page, the form options load from the API, the visitor fills in the
   form, submits, and sees the estimate with a scale and any warnings.
2. **Recover from a problem.** Options fail to load (retry), the server rejects a field (message shown
   next to that field), the visitor is rate limited (told when to retry), or the service is down
   (clear error, nothing lost from the form).
3. **Update the model (operator).** Train in the notebook, export, compute the SHA-256, deploy with the
   new `MODEL_SHA256`. See `docs/runbooks/model-update.md`.

## Functional requirements

- F1. `POST /api/predict` accepts the 12 inputs and returns a score, a band, a scale, warnings and a
  disclaimer.
- F2. `GET /api/options` returns the dropdown values and numeric limits, read from the loaded model
  so that the form can never offer a category the model does not know.
- F3. `GET /api/health/live` and `GET /api/health` report process and model health.
- F4. Inputs outside the range seen in training are accepted (if plausible) but flagged in `warnings`.
- F5. Unknown categories are rejected, not silently ignored. (The notebook's one-hot encoder uses
  `handle_unknown="ignore"`, which would otherwise return a prediction with that input dropped.)
- F6. Countries outside the model's top 10 are grouped as `Other`, as in the notebook.

## Non-functional requirements

- **Performance.** A prediction is one row through a 200-tree forest. Target p95 under 300 ms on the
  smallest hosting tier. Not yet measured (see `docs/testing.md`, "Not done").
- **Availability.** Best-effort for a student project. Single instance is acceptable.
- **Security and privacy.** No inputs, predictions or IP addresses are stored or logged
  (ADR 0005). Rate limiting, strict validation, security headers, hash-pinned model file. Details in
  `brain/security/`.
- **Accessibility.** WCAG 2.1 AA as the target for the frontend; automated axe check in tests;
  works at 375 px width.
- **Operability.** Structured JSON logs with request IDs, a real health check, all configuration
  from environment variables validated at startup.

## Out of scope (so the agent does not keep adding features)

- User accounts, login, teams, roles, billing, payments, webhooks.
- A database, saved history of predictions, data export or account deletion (nothing is stored).
- File uploads.
- Retraining from the app. Training stays in the notebook.
- Medical advice, triage, or any claim of clinical validity.
- Multi-language UI.

## Scale assumptions (not confirmed by the owner)

- Year one: tens to low hundreds of predictions per day; peak a few per minute.
- Data size: zero rows stored. The only persistent asset is the model file (size not known here; a
  200-tree forest on 5,000 rows is typically tens of MB).
- First bottleneck: RAM for the loaded model plus the scikit-learn/pandas imports, not CPU or network.
  A small instance with 512 MB may be tight; test with the real file before choosing a tier.

## Compliance notes

Inputs describe sleep, stress and screen habits, which is health-adjacent personal data in some
regimes. Because nothing is stored, the exposure is small today. If storage, analytics or accounts are
ever added, revisit consent and retention first (for example India's DPDP Act, GDPR). This is a
prompt to check, not legal advice.

## Known issues with the model that the product must not hide

- Test R² 0.865 for the saved (tuned) model, train R² 0.955: some overfitting. Cross-validated R² in
  the notebook is about 0.84.
- `Stress_Level` is an input. If it is derived from the same survey as the target, the model may be
  leaning on a near-duplicate of what it predicts. A real deployment should ask whether stress level
  would be known at prediction time.
- The dataset's relationships look unusually clean, which can indicate synthetic or heavily curated
  data. Treat outputs as illustrative.
- The training population is students aged 18 to 24. Other ages get a warning.
- The direction of the score (higher = better wellbeing) is inferred from sample rows in the notebook
  (longer sleep and low stress rows have higher scores). Confirm against the dataset's documentation.

## Open questions for the owner

1. Is higher `Mental_Health_Score` better? (Assumed yes. The band labels depend on it.)
2. Who is the audience: classmates, a portfolio demo, or the public? This decides how much hardening
   and which hosting tier.
3. Where will it be hosted, and is there a budget? (`docs/hosting.md` recommends but does not price.)
4. Which scikit-learn version trained `Mental_Health_Model2.pkl`? The backend refuses to load a model
   saved by a different version.
5. Should predictions ever be stored (for research or improving the model)? If yes, that needs consent
   and a database, and a new design pass.
