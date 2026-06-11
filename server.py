#!/usr/bin/env python3
"""Campeón Figus — servidor estático + API para pedidos, visitas y productos."""

from __future__ import annotations

import base64
import binascii
import json
import os
import random
import re
import sqlite3
from datetime import datetime, timedelta, timezone
from functools import wraps
from pathlib import Path

from flask import Flask, Response, jsonify, request, send_from_directory
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

ROOT = Path(__file__).resolve().parent
SEED_PATH = ROOT / "data" / "seed_products.json"
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "campeon2026")

# Sesión admin: token firmado (sin estado en memoria) para que funcione en
# entornos serverless con múltiples instancias (Vercel). La clave de firma se
# deriva de SECRET_KEY si existe, o de ADMIN_PASSWORD (idéntica en todas las
# instancias). El token expira a las 12 horas.
SECRET_KEY = os.environ.get("SECRET_KEY") or ("cf-admin::" + ADMIN_PASSWORD)
TOKEN_MAX_AGE = 12 * 60 * 60
_serializer = URLSafeTimedSerializer(SECRET_KEY, salt="campeon-figus-admin")

# Comprobante de pago: tipos permitidos y tamaño máximo (5 MB).
RECEIPT_ALLOWED_MIME = {"image/jpeg", "image/png", "image/webp", "application/pdf"}
RECEIPT_MAX_BYTES = 5 * 1024 * 1024
_DATA_URL_RE = re.compile(r"^data:([\w.+-]+/[\w.+-]+);base64,(.+)$", re.DOTALL)


def parse_receipt(receipt: dict | None) -> tuple[str, str, str] | None:
    """Valida un comprobante recibido como data URL base64.

    Devuelve (data_url, filename, mime) o None si no hay comprobante.
    Lanza ValueError si el comprobante es inválido (tipo o tamaño).
    """
    if not receipt or not isinstance(receipt, dict):
        return None
    data_url = (receipt.get("data") or "").strip()
    if not data_url:
        return None
    m = _DATA_URL_RE.match(data_url)
    if not m:
        raise ValueError("Comprobante con formato inválido")
    mime = m.group(1).lower()
    if mime not in RECEIPT_ALLOWED_MIME:
        raise ValueError("Tipo de comprobante no permitido (usá JPG, PNG, WEBP o PDF)")
    try:
        raw = base64.b64decode(m.group(2), validate=True)
    except (binascii.Error, ValueError):
        raise ValueError("Comprobante con datos inválidos")
    if len(raw) > RECEIPT_MAX_BYTES:
        raise ValueError("El comprobante supera el máximo de 5MB")
    name = (receipt.get("name") or "comprobante").strip()[:120]
    return data_url, name, mime


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

# Persistencia: si TURSO_DATABASE_URL está definida usamos Turso (libSQL) en
# modo remoto por HTTP, ideal para serverless (Vercel) donde el filesystem es
# efímero. Si no, caemos a SQLite local para desarrollo.
TURSO_DATABASE_URL = os.environ.get("TURSO_DATABASE_URL")
TURSO_AUTH_TOKEN = os.environ.get("TURSO_AUTH_TOKEN")
USE_TURSO = bool(TURSO_DATABASE_URL)

app = Flask(__name__, static_folder=str(ROOT), static_url_path="")


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def is_unique_violation(exc: Exception) -> bool:
    """Detecta una violación de UNIQUE en ambos backends.

    sqlite3 lanza IntegrityError; libsql lanza ValueError con el mensaje
    'UNIQUE constraint failed'.
    """
    return isinstance(exc, sqlite3.IntegrityError) or "UNIQUE constraint failed" in str(exc)


class _DictCursor:
    """Envuelve un cursor de libsql para devolver filas como dict.

    libsql devuelve tuplas planas y no soporta row_factory, así que
    reproducimos el acceso por nombre que usa el resto del código (row["col"]).
    """

    def __init__(self, cur):
        self._cur = cur

    def _cols(self) -> list[str]:
        return [d[0] for d in (self._cur.description or [])]

    def fetchone(self):
        row = self._cur.fetchone()
        return dict(zip(self._cols(), row)) if row is not None else None

    def fetchall(self):
        cols = self._cols()
        return [dict(zip(cols, row)) for row in self._cur.fetchall()]

    @property
    def rowcount(self):
        return self._cur.rowcount

    @property
    def lastrowid(self):
        return self._cur.lastrowid

    @property
    def description(self):
        return self._cur.description


class _LibsqlConnection:
    """Adapta una conexión libsql a la interfaz que usa el código (estilo sqlite3)."""

    def __init__(self, conn):
        self._conn = conn

    def execute(self, sql, params=()):
        return _DictCursor(self._conn.execute(sql, params))

    def executescript(self, sql):
        return self._conn.executescript(sql)

    def executemany(self, sql, seq):
        return self._conn.executemany(sql, seq)

    def commit(self):
        self._conn.commit()

    def rollback(self):
        self._conn.rollback()

    def close(self):
        self._conn.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        try:
            if exc_type is None:
                self._conn.commit()
            else:
                self._conn.rollback()
        finally:
            self.close()
        return False


def get_db():
    if USE_TURSO:
        import libsql

        kwargs = {}
        if TURSO_AUTH_TOKEN:
            kwargs["auth_token"] = TURSO_AUTH_TOKEN
        conn = libsql.connect(database=TURSO_DATABASE_URL, **kwargs)
        return _LibsqlConnection(conn)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    if not USE_TURSO:
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
                receipt_data TEXT,
                receipt_name TEXT,
                receipt_mime TEXT,
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
        # Migración: agrega columnas de comprobante a bases existentes.
        existing_cols = {r["name"] for r in conn.execute("PRAGMA table_info(orders)").fetchall()}
        for col in ("receipt_data", "receipt_name", "receipt_mime"):
            if col not in existing_cols:
                conn.execute(f"ALTER TABLE orders ADD COLUMN {col} TEXT")
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
        try:
            _serializer.loads(token, max_age=TOKEN_MAX_AGE)
        except SignatureExpired:
            return jsonify({"error": "Sesión expirada"}), 401
        except BadSignature:
            return jsonify({"error": "No autorizado"}), 401
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

    try:
        receipt = parse_receipt(data.get("receipt"))
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    receipt_data, receipt_name, receipt_mime = receipt if receipt else (None, None, None)

    with get_db() as conn:
        for _ in range(10):
            try:
                conn.execute(
                    """
                    INSERT INTO orders
                    (order_number, customer_email, customer_phone, customer_name,
                     shipping_json, items_json, subtotal, shipping_cost, total, status,
                     receipt_data, receipt_name, receipt_mime, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending', ?, ?, ?, ?)
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
                        receipt_data,
                        receipt_name,
                        receipt_mime,
                        now_iso(),
                    ),
                )
                break
            except Exception as exc:
                if not is_unique_violation(exc):
                    raise
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
                "has_receipt": bool(r["receipt_data"]),
                "receipt_name": r["receipt_name"],
                "receipt_mime": r["receipt_mime"],
                "created_at": r["created_at"],
            }
        )
    return jsonify(orders)


@app.get("/api/orders/<int:order_id>/receipt")
@require_admin
def get_order_receipt(order_id: int):
    with get_db() as conn:
        row = conn.execute(
            "SELECT receipt_data, receipt_name, receipt_mime FROM orders WHERE id = ?",
            (order_id,),
        ).fetchone()
    if row is None:
        return jsonify({"error": "Pedido no encontrado"}), 404
    if not row["receipt_data"]:
        return jsonify({"error": "Este pedido no tiene comprobante"}), 404
    m = _DATA_URL_RE.match(row["receipt_data"])
    if not m:
        return jsonify({"error": "Comprobante inválido"}), 500
    try:
        raw = base64.b64decode(m.group(2), validate=True)
    except (binascii.Error, ValueError):
        return jsonify({"error": "Comprobante inválido"}), 500
    mime = row["receipt_mime"] or m.group(1)
    name = row["receipt_name"] or "comprobante"
    return Response(
        raw,
        mimetype=mime,
        headers={"Content-Disposition": f'inline; filename="{name}"'},
    )


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
    token = _serializer.dumps({"admin": True, "ts": now_iso()})
    return jsonify({"token": token})


@app.post("/api/admin/logout")
def admin_logout():
    # Los tokens son sin estado (firmados); el cliente descarta el suyo.
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
# Un fallo transitorio (p. ej. red hacia Turso en un cold start) no debe tirar
# todo el módulo: se reintentará en el próximo arranque.
try:
    init_db()
except Exception as exc:  # noqa: BLE001
    print(f"[init_db] no se pudo inicializar la base al arrancar: {exc}")


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    print(f"Campeón Figus server → http://0.0.0.0:{port}")
    print(f"Admin panel → http://0.0.0.0:{port}/admin")
    app.run(host="0.0.0.0", port=port, debug=False)
