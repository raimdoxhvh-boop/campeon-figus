#!/usr/bin/env python3
"""Campeón Figus — servidor estático + API para pedidos, visitas y productos."""

from __future__ import annotations

import json
import os
import random
import secrets
import sqlite3
from datetime import datetime, timedelta, timezone
from functools import wraps
from pathlib import Path

from flask import Flask, jsonify, request, send_from_directory

ROOT = Path(__file__).resolve().parent
SEED_PATH = ROOT / "data" / "seed_products.json"
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "campeon2026")


def _resolve_db_path() -> Path:
    """Elige una ruta de base escribible.

    En Vercel (y otros entornos serverless) el filesystem del deploy es de
    solo lectura: únicamente /tmp permite escritura. Usamos DB_PATH si está
    definido por entorno; si no, /tmp en serverless o data/ en local.
    """
    env_path = os.environ.get("DB_PATH")
    if env_path:
        return Path(env_path)
    if os.environ.get("VERCEL") or os.environ.get("AWS_LAMBDA_FUNCTION_NAME"):
        return Path("/tmp") / "campeon_figus_store.db"
    return ROOT / "data" / "store.db"


DB_PATH = _resolve_db_path()

app = Flask(__name__, static_folder=str(ROOT), static_url_path="")
_tokens: dict[str, datetime] = {}


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def get_db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with get_db() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                cat TEXT NOT NULL,
                img TEXT NOT NULL,
                price REAL NOT NULL,
                badge TEXT,
                badge_color TEXT,
                stock INTEGER NOT NULL DEFAULT 1,
                desc TEXT,
                highlight INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_number TEXT NOT NULL UNIQUE,
                customer_email TEXT,
                customer_phone TEXT,
                customer_name TEXT,
                shipping_json TEXT NOT NULL,
                items_json TEXT NOT NULL,
                subtotal REAL NOT NULL,
                shipping_cost REAL NOT NULL,
                total REAL NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending',
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS visits (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                path TEXT NOT NULL,
                referrer TEXT,
                user_agent TEXT,
                ip TEXT,
                created_at TEXT NOT NULL
            );
            """
        )
        count = conn.execute("SELECT COUNT(*) AS c FROM products").fetchone()["c"]
        if count == 0 and SEED_PATH.exists():
            products = json.loads(SEED_PATH.read_text(encoding="utf-8"))
            for p in products:
                conn.execute(
                    """
                    INSERT INTO products
                    (id, name, cat, img, price, badge, badge_color, stock, desc, highlight, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        p["id"],
                        p["name"],
                        p["cat"],
                        p["img"],
                        p["price"],
                        p.get("badge"),
                        p.get("badgeColor", ""),
                        1 if p.get("stock", True) else 0,
                        p.get("desc", ""),
                        1 if p.get("highlight") else 0,
                        now_iso(),
                    ),
                )


def row_to_product(row: sqlite3.Row) -> dict:
    return {
        "id": row["id"],
        "name": row["name"],
        "cat": row["cat"],
        "img": row["img"],
        "price": row["price"],
        "badge": row["badge"],
        "badgeColor": row["badge_color"] or "",
        "stock": bool(row["stock"]),
        "desc": row["desc"] or "",
        "highlight": bool(row["highlight"]),
    }


def require_admin(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        auth = request.headers.get("Authorization", "")
        if not auth.startswith("Bearer "):
            return jsonify({"error": "No autorizado"}), 401
        token = auth[7:]
        expires = _tokens.get(token)
        if not expires or expires < datetime.now(timezone.utc):
            _tokens.pop(token, None)
            return jsonify({"error": "Sesión expirada"}), 401
        return f(*args, **kwargs)

    return wrapper


@app.route("/")
def home():
    return send_from_directory(ROOT, "index.html")


@app.route("/admin")
def admin_page():
    return send_from_directory(ROOT, "admin.html")


@app.get("/api/products")
def list_products():
    with get_db() as conn:
        rows = conn.execute("SELECT * FROM products ORDER BY highlight DESC, id ASC").fetchall()
    return jsonify([row_to_product(r) for r in rows])


@app.post("/api/products")
@require_admin
def create_product():
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    cat = (data.get("cat") or "").strip()
    img = (data.get("img") or "").strip()
    price = data.get("price")
    if not name or not cat or not img or price is None:
        return jsonify({"error": "Nombre, categoría, imagen y precio son obligatorios"}), 400
    try:
        price = float(price)
    except (TypeError, ValueError):
        return jsonify({"error": "Precio inválido"}), 400

    with get_db() as conn:
        next_id = conn.execute("SELECT COALESCE(MAX(id), 0) + 1 AS n FROM products").fetchone()["n"]
        conn.execute(
            """
            INSERT INTO products (id, name, cat, img, price, badge, badge_color, stock, desc, highlight, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                next_id,
                name,
                cat,
                img,
                price,
                data.get("badge") or None,
                data.get("badgeColor") or "",
                1 if data.get("stock", True) else 0,
                data.get("desc") or "",
                1 if data.get("highlight") else 0,
                now_iso(),
            ),
        )
        row = conn.execute("SELECT * FROM products WHERE id = ?", (next_id,)).fetchone()
    return jsonify(row_to_product(row)), 201


@app.delete("/api/products/<int:product_id>")
@require_admin
def delete_product(product_id: int):
    with get_db() as conn:
        cur = conn.execute("DELETE FROM products WHERE id = ?", (product_id,))
        if cur.rowcount == 0:
            return jsonify({"error": "Producto no encontrado"}), 404
    return jsonify({"ok": True})


@app.post("/api/visit")
def track_visit():
    data = request.get_json(silent=True) or {}
    path = (data.get("path") or "/").strip() or "/"
    with get_db() as conn:
        conn.execute(
            "INSERT INTO visits (path, referrer, user_agent, ip, created_at) VALUES (?, ?, ?, ?, ?)",
            (
                path,
                data.get("referrer") or request.headers.get("Referer"),
                request.headers.get("User-Agent"),
                request.remote_addr,
                now_iso(),
            ),
        )
    return jsonify({"ok": True})


@app.post("/api/orders")
def create_order():
    data = request.get_json(silent=True) or {}
    items = data.get("items") or []
    shipping = data.get("shipping") or {}
    if not items:
        return jsonify({"error": "El pedido no tiene productos"}), 400

    subtotal = float(data.get("subtotal") or 0)
    shipping_cost = float(data.get("shipping_cost") or 0)
    total = float(data.get("total") or subtotal + shipping_cost)
    order_number = "#CF-" + str(random.randint(1000, 9999))

    with get_db() as conn:
        for _ in range(10):
            try:
                conn.execute(
                    """
                    INSERT INTO orders
                    (order_number, customer_email, customer_phone, customer_name,
                     shipping_json, items_json, subtotal, shipping_cost, total, status, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending', ?)
                    """,
                    (
                        order_number,
                        shipping.get("email"),
                        shipping.get("phone"),
                        shipping.get("name"),
                        json.dumps(shipping, ensure_ascii=False),
                        json.dumps(items, ensure_ascii=False),
                        subtotal,
                        shipping_cost,
                        total,
                        now_iso(),
                    ),
                )
                break
            except sqlite3.IntegrityError:
                order_number = "#CF-" + str(random.randint(1000, 9999))
        else:
            return jsonify({"error": "No se pudo generar número de pedido"}), 500

    return jsonify({"order_number": order_number, "total": total})


@app.get("/api/orders")
@require_admin
def list_orders():
    with get_db() as conn:
        rows = conn.execute("SELECT * FROM orders ORDER BY created_at DESC").fetchall()
    orders = []
    for r in rows:
        orders.append(
            {
                "id": r["id"],
                "order_number": r["order_number"],
                "customer_email": r["customer_email"],
                "customer_phone": r["customer_phone"],
                "customer_name": r["customer_name"],
                "shipping": json.loads(r["shipping_json"]),
                "items": json.loads(r["items_json"]),
                "subtotal": r["subtotal"],
                "shipping_cost": r["shipping_cost"],
                "total": r["total"],
                "status": r["status"],
                "created_at": r["created_at"],
            }
        )
    return jsonify(orders)


@app.patch("/api/orders/<int:order_id>")
@require_admin
def update_order(order_id: int):
    data = request.get_json(silent=True) or {}
    status = data.get("status")
    if status not in {"pending", "paid", "cancelled"}:
        return jsonify({"error": "Estado inválido"}), 400
    with get_db() as conn:
        cur = conn.execute("UPDATE orders SET status = ? WHERE id = ?", (status, order_id))
        if cur.rowcount == 0:
            return jsonify({"error": "Pedido no encontrado"}), 404
    return jsonify({"ok": True})


@app.get("/api/visits")
@require_admin
def list_visits():
    limit = min(int(request.args.get("limit", 100)), 500)
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM visits ORDER BY created_at DESC LIMIT ?",
            (limit,),
        ).fetchall()
    return jsonify([dict(r) for r in rows])


@app.get("/api/stats")
@require_admin
def stats():
    today = datetime.now(timezone.utc).date().isoformat()
    week_ago = (datetime.now(timezone.utc) - timedelta(days=6)).date().isoformat()
    with get_db() as conn:
        total_visits = conn.execute("SELECT COUNT(*) AS c FROM visits").fetchone()["c"]
        visits_today = conn.execute(
            "SELECT COUNT(*) AS c FROM visits WHERE date(created_at) = date(?)",
            (today,),
        ).fetchone()["c"]
        unique_today = conn.execute(
            "SELECT COUNT(DISTINCT ip) AS c FROM visits WHERE date(created_at) = date(?)",
            (today,),
        ).fetchone()["c"]
        total_orders = conn.execute("SELECT COUNT(*) AS c FROM orders").fetchone()["c"]
        pending_orders = conn.execute(
            "SELECT COUNT(*) AS c FROM orders WHERE status = 'pending'"
        ).fetchone()["c"]
        revenue = conn.execute(
            "SELECT COALESCE(SUM(total), 0) AS s FROM orders WHERE status != 'cancelled'"
        ).fetchone()["s"]
        product_count = conn.execute("SELECT COUNT(*) AS c FROM products").fetchone()["c"]
        daily = conn.execute(
            """
            SELECT date(created_at) AS day, COUNT(*) AS visits
            FROM visits
            WHERE date(created_at) >= date(?)
            GROUP BY date(created_at)
            ORDER BY day ASC
            """,
            (week_ago,),
        ).fetchall()
    return jsonify(
        {
            "total_visits": total_visits,
            "visits_today": visits_today,
            "unique_visitors_today": unique_today,
            "total_orders": total_orders,
            "pending_orders": pending_orders,
            "revenue": revenue,
            "product_count": product_count,
            "visits_by_day": [{"day": r["day"], "visits": r["visits"]} for r in daily],
        }
    )


@app.post("/api/admin/login")
def admin_login():
    data = request.get_json(silent=True) or {}
    if data.get("password") != ADMIN_PASSWORD:
        return jsonify({"error": "Contraseña incorrecta"}), 401
    token = secrets.token_urlsafe(32)
    _tokens[token] = datetime.now(timezone.utc) + timedelta(hours=12)
    return jsonify({"token": token})


@app.post("/api/admin/logout")
@require_admin
def admin_logout():
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        _tokens.pop(auth[7:], None)
    return jsonify({"ok": True})


@app.route("/<path:filepath>")
def static_files(filepath: str):
    if filepath.startswith("api/"):
        return jsonify({"error": "No encontrado"}), 404
    target = ROOT / filepath
    if target.is_file():
        return send_from_directory(ROOT, filepath)
    return jsonify({"error": "No encontrado"}), 404


# Inicializa la base al importar el módulo (necesario en entornos serverless
# como Vercel, donde la app se importa y no se ejecuta el bloque __main__).
init_db()


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    print(f"Campeón Figus server → http://0.0.0.0:{port}")
    print(f"Admin panel → http://0.0.0.0:{port}/admin")
    app.run(host="0.0.0.0", port=port, debug=False)
