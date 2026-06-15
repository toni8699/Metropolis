# Production deployment — Metropolis Nexus

Backend on **Render** (Docker from GHCR). Frontend on **Vercel**. Database on **Neon**. Files on **AWS S3**. Payments via **Stripe** (test mode in staging).

## Architecture

```
Vercel (SPA) ──REST/JWT──► Render Web Service (Gunicorn + UvicornWorker)
                │                    │
                │                    ├── Neon Postgres
                │                    ├── AWS S3 (presigned uploads)
                │                    ├── Stripe webhooks → /webhooks/stripe
                └── Socket.IO ───────┴── Redis (Socket.IO + ARQ)
```

## API docs (hosted backend)

FastAPI serves OpenAPI automatically on the same host as the API. No extra Render service or Vercel config.

| URL | What |
|-----|------|
| `https://<your-render-host>/docs` | Swagger UI |
| `https://<your-render-host>/redoc` | ReDoc |
| `https://<your-render-host>/openapi.json` | OpenAPI JSON |

Example: if Render URL is `https://metropolis-api.onrender.com`, docs are at `https://metropolis-api.onrender.com/docs`.

Docs are on by default in production. Health check stays `/api/health` (not `/docs`).

---

## 1. Neon Postgres

1. Create a Neon project and database.
2. Copy the pooled connection string (`?sslmode=require`).
3. Set `DATABASE_URL` on the Render web service.

Migrations run on container start via `docker-entrypoint.prod.sh` (`alembic upgrade head`).

## 2. AWS S3

1. Create a bucket for listing photos and host documents.
2. IAM user or task role with `s3:PutObject`, `s3:GetObject` on the bucket prefix.
3. Set on Render:
   - `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY` (or use IAM role on AWS)
   - `AWS_REGION`, `S3_BUCKET_NAME`
   - `S3_PRESIGN_TTL_SECONDS=300`

## 3. Stripe

1. Create a Stripe account; use **test keys** in staging.
2. Backend (Render):
   - `STRIPE_SECRET_KEY=sk_test_...`
   - `STRIPE_WEBHOOK_SECRET=whsec_...` (endpoint: `https://api.example.com/webhooks/stripe`, event: `payment_intent.succeeded`)
3. Frontend (Vercel build env):
   - `VITE_STRIPE_PUBLISHABLE_KEY=pk_test_...`

Without Stripe keys locally, checkout auto-completes payment in dev (`mock: true`).

## 4. Render web service

1. **New Web Service** → Deploy from container image.
2. Image: `ghcr.io/<github-owner>/metropolis-backend:<git-sha>` (pushed by CI on `main`).
3. Port: `8080` (matches `PORT` in `Dockerfile.prod`).
4. Health check path: `/api/health`

**After Flask → FastAPI cutover:** same image name, port, and health path. CI already builds `Dockerfile.prod` with `metropolis.asgi:app`. You do **not** need a new GHCR repo or Render service type — merge to `main`, CI pushes a new tag, deploy hook pulls it.

### Render env changes (one-time)

If you set these for the old Flask/Eventlet stack, update or remove them:

| Variable | Old (Flask) | New (FastAPI) |
|----------|-------------|---------------|
| `GUNICORN_WORKER_CLASS` | `eventlet` | `uvicorn.workers.UvicornWorker` (or omit — prod entrypoint defaults to this) |
| `WEB_CONCURRENCY` | `1` (eventlet) | `2`+ with `REDIS_URL` for Socket.IO; default in `gunicorn.conf.py` is CPU-based |

Keep unchanged: `DATABASE_URL`, `JWT_SECRET`, `CORS_ORIGINS`, `REDIS_URL`, Stripe/AWS keys, `RENDER_DEPLOY_HOOK` secret in GitHub.

`FLASK_DEBUG=0` is still the env name for the debug flag (`settings.debug`).

### Required environment variables

| Variable | Notes |
|----------|--------|
| `DATABASE_URL` | Neon connection string |
| `JWT_SECRET` | `openssl rand -hex 32` — must not be dev default when `FLASK_DEBUG=0` |
| `FLASK_DEBUG` | `0` |
| `CORS_ORIGINS` | Your Vercel SPA URL (comma-separated) |
| `AWS_REGION`, `S3_BUCKET_NAME` | S3 uploads |
| `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET` | Payments |
| `REDIS_URL` | Render Redis or Upstash — **required** for multi-worker Socket.IO and ARQ booking sweep |
| `ALLOW_USER_LISTINGS` | `1` to allow host listings |

### Optional

| Variable | Notes |
|----------|--------|
| `GOOGLE_OAUTH_CLIENT_ID` | Google Sign-In token verification |
| `WEB_CONCURRENCY` | Gunicorn worker count (default from `gunicorn.conf.py`) |
| `BOOKING_SWEEP_ENABLED` | `1` to run expired-booking cron in ARQ worker |

## 5. GitHub Actions deploy (CI)

On push to `main`, after tests pass, CI:

1. Builds `backend/Dockerfile.prod`
2. Pushes to `ghcr.io/<owner>/metropolis-backend:<sha>` and `:latest`
3. POSTs `RENDER_DEPLOY_HOOK` (repository secret) to trigger Render pull

Add secret: **Settings → Secrets → Actions → `RENDER_DEPLOY_HOOK`** (from Render service → Deploy Hook).

No CI changes needed for docs — they ship inside the same backend container.

## 6. Vercel (frontend)

1. Import the GitHub repo; root directory `frontend/`.
2. Build: `npm run build`; output `dist`.
3. `frontend/vercel.json` rewrites all routes to `index.html` (SPA).
4. Environment variables (Production):
   - `VITE_API_URL` — Render API URL (e.g. `https://metropolis-api.onrender.com`) — **unchanged**; same `/api/*` paths
   - `VITE_GOOGLE_MAPS_API_KEY`
   - `VITE_STRIPE_PUBLISHABLE_KEY`
   - `VITE_GOOGLE_OAUTH_CLIENT_ID` (optional)

## 7. Redis (Socket.IO + ARQ)

Single Gunicorn worker can run without Redis for basic HTTP, but production should use Redis for:

1. Socket.IO cross-worker rooms (`python-socketio` Redis manager)
2. ARQ background worker (booking sweep cron)

1. Add Redis (Render Redis, Upstash, or ElastiCache).
2. Set `REDIS_URL` on the web service (and on the ARQ worker if separate).

Local dev: `docker compose up` includes `redis`, `backend`, and `worker` (ARQ).

### Optional: ARQ worker on Render

Booking auto-expiry runs in a separate process:

```bash
arq metropolis.jobs.booking_sweep.WorkerSettings
```

Add a **Background Worker** on Render (same GHCR image, override start command to the line above, same `REDIS_URL` + `DATABASE_URL`). Or run sweep only in dev until you add the worker service.

## 8. Smoke checks after deploy

```bash
curl -sf https://api.example.com/api/health
curl -sf https://api.example.com/docs
curl -sf https://api.example.com/openapi.json | head -c 200
```

Log in on the SPA, search with dates, complete checkout (Stripe test card `4242 4242 4242 4242`), open trip chat.

## 9. Security checklist

- [ ] `JWT_SECRET` ≥ 32 chars, not `change-me-dev-secret`
- [ ] `FLASK_DEBUG=0`
- [ ] `CORS_ORIGINS` lists only your SPA origin(s)
- [ ] S3 bucket not public; objects via presigned URLs
- [ ] Stripe webhook secret configured; live keys only in production
