# Runbook: roll back

There is no database, so rollback never involves data.

- **Bad backend release:** redeploy the previous successful build from your host's deploy history. If the
  model file also changed, restore the previous file and its `MODEL_SHA256` (`model-update.md`).
- **Bad frontend release:** promote the previous deployment in the static host's dashboard.
- **After rolling back:** run `/api/health`, run one estimate in the browser, then open an issue describing
  what failed so the fix goes through a branch and CI.

Practise this once on staging before you need it.
