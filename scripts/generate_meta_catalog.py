#!/usr/bin/env python3
"""Genera data/meta_catalog.csv para importar en Meta Commerce Manager."""

from __future__ import annotations

import argparse
import csv
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SEED_PATH = ROOT / "data" / "seed_products.json"
OUT_PATH = ROOT / "data" / "meta_catalog.csv"

CAT_LABELS = {
    "combos": "Combos Álbum + Sobres",
    "albums": "Álbumes",
    "figuritas": "Sobres y Packs de Figuritas",
    "cromos": "Cromos Adrenalyn XL",
}

# Google product category (coleccionables / juguetes deportivos)
GOOGLE_CATEGORY = "Toys & Games > Collectible Toys"


def fmt_price(amount: float | int) -> str:
    return f"{float(amount):.2f} ARS"


def product_link(base: str, product_id: int) -> str:
    base = base.rstrip("/")
    return f"{base}/#/product/{product_id}"


def image_link(base: str, img_path: str) -> str:
    base = base.rstrip("/")
    path = img_path.lstrip("/")
    return f"{base}/{path}"


def load_products() -> list[dict]:
    return json.loads(SEED_PATH.read_text(encoding="utf-8"))


def build_rows(products: list[dict], base_url: str) -> list[dict]:
    rows = []
    for p in products:
        desc = (p.get("desc") or "").strip()
        badge = p.get("badge")
        if badge:
            desc = f"{badge} — {desc}" if desc else str(badge)

        rows.append(
            {
                "id": str(p["id"]),
                "title": p["name"],
                "description": desc[:9999],
                "availability": "in stock" if p.get("stock", True) else "out of stock",
                "condition": "new",
                "price": fmt_price(p["price"]),
                "link": product_link(base_url, p["id"]),
                "image_link": image_link(base_url, p["img"]),
                "brand": "Campeón Figus",
                "google_product_category": GOOGLE_CATEGORY,
                "product_type": CAT_LABELS.get(p.get("cat", ""), p.get("cat", "")),
                "custom_label_0": p.get("cat", ""),
                "custom_label_1": "destacado" if p.get("highlight") else "catalogo",
            }
        )
    return rows


def write_csv(rows: list[dict], out_path: Path) -> None:
    fieldnames = [
        "id",
        "title",
        "description",
        "availability",
        "condition",
        "price",
        "link",
        "image_link",
        "brand",
        "google_product_category",
        "product_type",
        "custom_label_0",
        "custom_label_1",
    ]
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description="Generar CSV de catálogo para Meta")
    parser.add_argument(
        "--base-url",
        default=os.environ.get("STORE_URL", "https://TU-TIENDA.vercel.app"),
        help="URL pública de la tienda (sin barra final). Env: STORE_URL",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=OUT_PATH,
        help="Ruta del CSV de salida",
    )
    args = parser.parse_args()

    products = load_products()
    rows = build_rows(products, args.base_url)
    write_csv(rows, args.output)
    print(f"OK: {len(rows)} productos → {args.output}")
    print(f"Base URL: {args.base_url}")


if __name__ == "__main__":
    main()
