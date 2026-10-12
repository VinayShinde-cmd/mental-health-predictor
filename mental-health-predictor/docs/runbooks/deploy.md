# Runbook: first deploy

Written without a chosen host, so steps are provider-neutral. Fill in provider specifics when chosen.

## Before you start
- [ ] Real model exported, hashed, and tested locally (`model-update.md`).
- [ ] CI is green on `main`.
- [ ] Billing alert set on every provider.

## Backend
1. Create a web service from the `backend/` directory. Python 3.13, `pip install -r requirements.txt`.
2. Set environment variables: `APP_ENV=production`, `MODEL_PATH`, `MODEL_SHA256`, `CORS_ORIGINS=https://<frontend origin>`,
   `LOG_LEVEL=INFO`, and `TRUST_PROXY_HEADERS` as described in `hosting.md`.
3. Start command: see `hosting.md`. Health check path: `/api/health/live`.
4. Open `https://<api>/api/health`: expect `{"status":"ok", ...}`. Open `/docs`: expect 404.

## Frontend
1. Set `VITE_API_BASE_URL=https://<api>` at build time. Build: `npm install && npm run build`; publish `dist/`.
2. Add the security headers listed in `hosting.md`.
3. Open the site, run an estimate, confirm no console errors.

## After
- Check that uptime monitors (`monitoring.md`) are created and a failing one actually alerts you.
- Confirm no inputs or IP addresses appear in the provider's logs (`ADR 0005`; the provider's own proxy logs are outside this repo).
