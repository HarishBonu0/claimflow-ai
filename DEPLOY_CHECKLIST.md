# Production Deployment Checklist (Render Backend + Vercel Frontend)

Use this checklist for every production rollout.

## 1. Pre-deploy safety checks

- [ ] Confirm no secrets are committed (`.env` must stay untracked).
- [ ] Confirm frontend build works locally:
  - `cd frontend`
  - `npm run build`
- [ ] Confirm backend starts locally with production-like env values.
- [ ] Confirm database connectivity (`DATABASE_URL`) is valid.
- [ ] Confirm Gemini key works (`GEMINI_API_KEY`).

## 2. Render backend deployment

- [ ] Push code to GitHub.
- [ ] In Render: `New +` -> `Blueprint`.
- [ ] Select repository and verify `render.yaml` is detected.
- [ ] Ensure service uses Docker and port `8000`.
- [ ] Set required environment variables:
  - `APP_ENV=production`
  - `DATABASE_URL=<your_postgres_url>`
  - `GEMINI_API_KEY=<your_gemini_key>`
  - `ALLOWED_ORIGINS=<your_vercel_url[,extra_domain]>`
  - Optional: `SENTRY_DSN=<dsn>`
- [ ] Deploy backend and record URL (example: `https://claimflow-api.onrender.com`).

## 3. Vercel frontend deployment

- [ ] In Vercel: import repository.
- [ ] Set root directory to `frontend`.
- [ ] Framework preset: `Vite`.
- [ ] Add frontend env var:
  - `VITE_API_BASE_URL=https://claimflow-api.onrender.com`
- [ ] Deploy frontend and record URL (example: `https://claimflow-ai-bot.vercel.app`).

## 4. CORS and cross-service linking

- [ ] Update Render `ALLOWED_ORIGINS` to include exact Vercel domain(s).
- [ ] Redeploy backend after CORS env update.
- [ ] Verify frontend points to Render URL via `VITE_API_BASE_URL`.

## 5. Smoke tests (must pass)

Run:

```powershell
./scripts/smoke-test-deploy.ps1 -BackendUrl "https://claimflow-api.onrender.com" -FrontendUrl "https://claimflow-ai-bot.vercel.app"
```

Expected:

- Backend `/health` returns `status=ok`.
- Backend `/chat` responds with HTTP 200 and non-empty `response`.
- Frontend root URL returns HTTP 200.
- Frontend can reach backend (manual browser chat test).

## 6. Post-deploy validation

- [ ] Login/signup works.
- [ ] Chat send/receive works.
- [ ] Voice endpoint works (`/voice`).
- [ ] Document upload works (`/upload`).
- [ ] Browser console has no CORS errors.
- [ ] Render logs show no startup/runtime exceptions.

## 7. Rollback readiness

- [ ] Previous stable commit hash recorded.
- [ ] Render supports redeploy of previous image/commit.
- [ ] Vercel supports instant rollback to previous deployment.

## 8. Incident quick fixes

- If frontend cannot reach backend:
  - Check `VITE_API_BASE_URL` in Vercel.
  - Check backend URL health endpoint.
- If CORS errors appear:
  - Check `ALLOWED_ORIGINS` exact domain and protocol.
- If backend boot fails:
  - Check Render logs for missing env vars.
  - Verify database SSL params in `DATABASE_URL`.
