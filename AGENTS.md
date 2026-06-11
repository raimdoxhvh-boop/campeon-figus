# AGENTS.md

## Cursor Cloud specific instructions

### Product

**Campeón Figus** — e-commerce SPA (vanilla HTML/JS) + Flask API + SQLite. Serves FIFA World Cup 2026 Panini collectibles for Argentina.

### Running the application

Install dependencies and start the server (serves static files + API on one port):

```bash
pip install -r requirements.txt
python3 server.py
```

Open http://localhost:8080 for the store and http://localhost:8080/admin for the admin panel.

Default admin password: `campeon2026` (override with `ADMIN_PASSWORD` env var).

Do **not** use `python3 -m http.server` alone — the store needs the Flask API for products, orders, and visits.

### Lint / test / build

None configured. Verify manually in browser.

### Admin panel (`/admin`)

- Dashboard: visits, orders, revenue stats
- Orders: list, detail (incl. payment receipt when attached), change status (pending / paid / cancelled)
- Visits: log and 7-day chart
- Products: list, add new, delete

New product images: place files in `catalogo/` and use relative path (e.g. `catalogo/mi_foto.webp`) in the form.

### Data

By default a local SQLite DB at `data/store.db` (gitignored). Products seed from `data/seed_products.json` on first run.

**Persistent storage (production / Vercel):** Vercel's filesystem is ephemeral (`/tmp`), so orders/receipts/visits would be lost. Set these env vars to use [Turso](https://turso.tech) (libSQL, SQLite-compatible) instead — the app connects remotely over HTTP, no local file:

- `TURSO_DATABASE_URL` (e.g. `libsql://<db>-<org>.turso.io`)
- `TURSO_AUTH_TOKEN`

When `TURSO_DATABASE_URL` is set, the app uses Turso automatically; otherwise it falls back to local SQLite. Same schema and seeding logic apply to both.

### Admin session / security

Admin sessions use signed stateless tokens (works across Vercel's serverless instances). Set a strong `ADMIN_PASSWORD` (default `campeon2026` is public in the repo) and optionally `SECRET_KEY` to harden token signing.

### E2E smoke test

1. Store: browse → add to cart → checkout → finalize order
2. Admin: login → verify order appears → check visit count incremented
