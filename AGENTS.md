# AGENTS.md

Guidance for cloud agents working in this repository.

## Project overview

**Campeón Figus** is a static e-commerce prototype for FIFA World Cup 2026 Panini collectibles. The main app is a single-page storefront in `index.html` (catalog → cart → shipping → bank transfer → order confirmation). Cart state is stored in browser `localStorage` (`cf-cart2`). There is no backend, database, build step, or package manager.

Supplementary artifacts:

- `stitch_tienda_de_figuritas_mundial/` — Stitch-generated HTML mockups
- `campeon_figus_theme.zip` — TiendaNube Liquid theme (deployed externally, not runnable locally)
- `catalogo/` — product WebP images

## Cursor Cloud specific instructions

### Services

| Service | Required | Start command | URL |
|---------|----------|---------------|-----|
| Static file server | Yes | `python3 -m http.server 8080` (from repo root) | http://localhost:8080/ |

No database, API, Docker Compose, or env files are needed. Outbound internet is required for Tailwind CDN, Google Fonts, and Material Symbols.

### Lint / test / build

There is no `package.json`, linter, test runner, or build pipeline. Validation is manual: serve the site and exercise the storefront flow in a browser.

### Development workflow

1. From `/workspace`, start the static server (see table above).
2. Open `http://localhost:8080/` in a browser.
3. Core flow to verify: add a product to cart → open cart → proceed to shipping → payment → finalize order (confetti + order number on success page).

Alternative static server:

```bash
npx --yes serve /workspace -l 3000
```

### Gotchas

- **CDN dependency**: The UI depends on `cdn.tailwindcss.com` and Google Fonts. Offline or blocked CDN requests will break styling.
- **No hot reload**: Edits to `index.html` require a browser refresh; the Python server does not watch files.
- **Stitch mockups**: Individual pages under `stitch_tienda_de_figuritas_mundial/` are standalone prototypes, not wired into `index.html`.
- **Theme zip**: `campeon_figus_theme.zip` is for TiendaNube hosting only; do not expect it to run as a local app.
