# AGENTS.md

## Cursor Cloud specific instructions

### Product

**Campeón Figus** is a client-side e-commerce SPA for FIFA World Cup 2026 Panini collectibles (Argentina). The main app is a single `index.html` with vanilla HTML/CSS/JavaScript. There is no backend, database, build step, or package manager.

### Running the application

Start a static HTTP server from the repo root:

```bash
python3 -m http.server 8080
```

Open http://localhost:8080 in a browser.

Do not open `index.html` via `file://` — relative asset paths (e.g. `catalogo/`) require HTTP serving.

### Lint / test / build

None configured. This repo has no `package.json`, test suite, or linter. Verification is manual/browser-based.

### Optional assets (not required for the main app)

- `stitch_tienda_de_figuritas_mundial/` — design reference HTML mockups
- `campeon_figus_theme.zip` — TiendaNube Liquid theme (separate from `index.html`)
- `catalogo/` — product images served by the static server

### E2E smoke test

1. Browse products on the homepage
2. Add an item to cart ("Agregar")
3. Open cart → proceed to shipping → fill required fields
4. Continue to payment (bank transfer) → "FINALIZAR PEDIDO"
5. Confirm success page with order number (e.g. `#CF-XXXX`)

Cart state persists in `localStorage` under key `cf-cart2`.

### External dependencies

The app loads Tailwind CSS, Google Fonts, and Material Symbols from CDNs. Offline use degrades styling but core JS still runs.
