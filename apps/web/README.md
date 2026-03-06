# StateLock Unified Web UI

Thin Next.js UI for the existing Core and Observability backends.

## Run

```bash
cd apps/web
npm install
PORT=3001 \
STATELOCK_CORE_BASE_URL=http://127.0.0.1:8000 \
STATELOCK_CORE_API_KEY= \
STATELOCK_OBS_BASE_URL=http://127.0.0.1:8001 \
STATELOCK_OBS_API_KEY=dev-key \
npm run dev
```

Browser traffic stays on the Next.js origin and uses the proxy routes:

- `/api/core/*`
- `/api/obs/*`
