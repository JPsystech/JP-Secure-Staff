# Frontend environment variables

## API base URL

| Variable | When to use |
|----------|-------------|
| `NEXT_PUBLIC_API_BASE_URL` | **Recommended.** Backend origin only, e.g. `https://jp-secure-staff.onrender.com`. The client appends `/api/v1` automatically. |
| `NEXT_PUBLIC_API_URL`     | **Legacy.** Full base including path, e.g. `https://jp-secure-staff.onrender.com/api/v1`. Also supported. |

- **Local:** Set in `.env.local` or leave unset to use `http://localhost:8000` (with `/api/v1`).
- **Render / Vercel:** Set in the service **Environment** tab. No `.env` file is needed at runtime; build-time and runtime both read these.

## Example

**Local (.env.local):**
```bash
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

**Production (Render frontend service):**
```bash
NEXT_PUBLIC_API_BASE_URL=https://jp-secure-staff.onrender.com
```

## Centralized API client

All API calls use `@/lib/api`:

- **JSON requests:** `apiRequest<T>(endpoint, options)` — base URL + JWT from storage, returns `{ data?, error? }`.
- **Blob / custom responses:** `apiFetch(endpoint, init)` — same base URL + JWT, returns raw `Response` (e.g. for downloads, file uploads).

No hardcoded backend URLs; the base URL is read from env in `lib/api.ts` only.

---

## Confirmation checklist (production-ready frontend ↔ backend)

- [x] **Single API base:** All requests use `getApiBaseUrl()` from `lib/api.ts`; no hardcoded `localhost`, `127.0.0.1`, or backend URLs in components.
- [x] **Env-based URL:** `NEXT_PUBLIC_API_BASE_URL` (recommended) or `NEXT_PUBLIC_API_URL`; fallback `http://localhost:8000` only when unset (local dev).
- [x] **Centralized client:** `apiRequest()` for JSON + JWT; `apiFetch()` for blobs/uploads; JWT from `localStorage` attached automatically.
- [x] **No direct fetch/axios URLs:** All API calls go through `apiRequest` or `apiFetch`; no `process.env.NEXT_PUBLIC_*` or URL strings in components.
- [x] **Render-compatible:** Set `NEXT_PUBLIC_API_BASE_URL=https://jp-secure-staff.onrender.com` in the frontend service Environment; no `.env` file required at runtime.
- [x] **Works locally and on Render:** Same code path; env differs per environment.
