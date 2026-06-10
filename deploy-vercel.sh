#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

# VERCEL_TOKEN inválido en el entorno anula la sesión del CLI guardada en auth.json
unset VERCEL_TOKEN

if ! npx vercel whoami >/dev/null 2>&1; then
  echo "→ Primero iniciá sesión: npx vercel login"
  exit 1
fi

echo "→ Desplegando a producción..."
npx vercel --prod --yes

echo ""
echo "✓ Listo. Tienda: https://<tu-proyecto>.vercel.app"
echo "  Admin:    https://<tu-proyecto>.vercel.app/admin"
