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
- Orders: list, detail, change status (pending / paid / cancelled)
- Visits: log and 7-day chart
- Products: list, add new, delete

New product images: place files in `catalogo/` and use relative path (e.g. `catalogo/mi_foto.webp`) in the form.

### Deploy en Vercel (CLI — opción B)

```bash
npx vercel login          # una sola vez, abre el navegador
./deploy-vercel.sh          # o: npx vercel --prod --yes
```

Si usás token en CI/Cloud Agent: `export VERCEL_TOKEN=...` y luego `npx vercel --prod --yes --token "$VERCEL_TOKEN"`.

Configurá estas variables de entorno en el dashboard de Vercel (o al primer deploy):

| Variable | Descripción |
|----------|-------------|
| `ADMIN_PASSWORD` | Contraseña del panel admin (obligatoria en producción) |
| `SECRET_KEY` | Clave para firmar sesiones admin (recomendada) |

En Vercel la base SQLite usa `/tmp` (los datos pueden reiniciarse entre despliegues). Para persistencia en producción, conectá Turso/Postgres más adelante.

### Data

SQLite DB at `data/store.db` locally, `/tmp/campeon_figus.db` on Vercel. Products seed from `data/seed_products.json` on first run.

### E2E smoke test

1. Store: browse → add to cart → checkout → finalize order
2. Admin: login → verify order appears → check visit count incremented
