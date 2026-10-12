"""REST API owns persistence; all stock calculations are delegated over HTTP."""
import os
import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb
import requests
from flask import Flask, jsonify, request
from werkzeug.exceptions import BadRequest, UnsupportedMediaType

app = Flask(__name__)
SERVICE_URL = os.getenv("SERVICE_URL", "http://web-service:8001")


def connect():
    return psycopg.connect(host=os.getenv("DB_HOST", "db"),
        port=int(os.getenv("DB_PORT", "5432")), dbname=os.getenv("DB_NAME", "stockwatch"),
        user=os.getenv("DB_USER", "lab"), password=os.getenv("DB_PASSWORD", "local_lab_password"),
        connect_timeout=3, row_factory=dict_row)


def products(conn):
    return conn.execute("SELECT * FROM products ORDER BY id").fetchall()


def validated(data):
    if not isinstance(data, dict):
        raise ValueError("Требуется JSON-объект")
    name = data.get("name")
    if not isinstance(name, str) or not 1 <= len(name.strip()) <= 100:
        raise ValueError("Название должно содержать от 1 до 100 символов")
    fields = {"quantity": (0, 1000000), "daily_usage": (1, 10000),
              "lead_days": (1, 365), "safety_stock": (0, 1000000)}
    values = [name.strip()]
    for key, (low, high) in fields.items():
        value = data.get(key)
        if type(value) is not int or not low <= value <= high:
            raise ValueError(f"{key}: требуется целое число от {low} до {high}")
        values.append(value)
    return values


@app.get("/health")
def health():
    with connect() as conn:
        conn.execute("SELECT id FROM products LIMIT 1")
        conn.execute("SELECT id FROM analyses LIMIT 1")
    return jsonify(status="ok", service="backend")


@app.get("/api/products")
def list_products():
    with connect() as conn:
        return jsonify(items=products(conn))


@app.post("/api/products")
def create_product():
    values = validated(request.get_json())
    with connect() as conn:
        # Serializes creates for the educational 1000-item service limit.
        conn.execute("LOCK TABLE products IN SHARE ROW EXCLUSIVE MODE")
        if conn.execute("SELECT count(*) AS count FROM products").fetchone()["count"] >= 1000:
            return jsonify(error="Достигнут лимит 1000 товаров"), 409
        row = conn.execute("""INSERT INTO products
            (name, quantity, daily_usage, lead_days, safety_stock)
            VALUES (%s,%s,%s,%s,%s) RETURNING *""", values).fetchone()
    return jsonify(row), 201


@app.put("/api/products/<int:product_id>")
def update_product(product_id):
    values = validated(request.get_json())
    with connect() as conn:
        row = conn.execute("""UPDATE products SET name=%s, quantity=%s,
            daily_usage=%s, lead_days=%s, safety_stock=%s WHERE id=%s RETURNING *""",
            [*values, product_id]).fetchone()
    return (jsonify(row), 200) if row else (jsonify(error="Товар не найден"), 404)


@app.delete("/api/products/<int:product_id>")
def delete_product(product_id):
    with connect() as conn:
        row = conn.execute("DELETE FROM products WHERE id=%s RETURNING id", (product_id,)).fetchone()
    return ("", 204) if row else (jsonify(error="Товар не найден"), 404)


@app.post("/api/analysis")
def analyze_stock():
    with connect() as conn:
        snapshot = products(conn)
    # Do not hold a database transaction while waiting for an HTTP service.
    response = requests.post(f"{SERVICE_URL}/analyze", json={"products": snapshot}, timeout=(3, 5))
    response.raise_for_status()
    try:
        result = response.json()
    except ValueError:
        return jsonify(error="Сервис расчёта вернул некорректный JSON"), 502
    if not isinstance(result, dict) or not isinstance(result.get("items"), list) or not isinstance(result.get("summary"), dict):
        return jsonify(error="Некорректный ответ сервиса расчёта"), 502
    with connect() as conn:
        row = conn.execute("INSERT INTO analyses (result) VALUES (%s) RETURNING id, created_at",
                           (Jsonb(result),)).fetchone()
    app.logger.warning("Stock calculation delegated to web-service; analysis_id=%s", row["id"])
    return jsonify(**row, **result), 201


@app.get("/api/analyses")
def history():
    with connect() as conn:
        rows = conn.execute("SELECT id, created_at, result FROM analyses ORDER BY id DESC LIMIT 20").fetchall()
    return jsonify(items=rows)


@app.errorhandler(ValueError)
@app.errorhandler(BadRequest)
@app.errorhandler(UnsupportedMediaType)
def invalid(error):
    return jsonify(error=str(error)), 400


@app.errorhandler(psycopg.Error)
def database_error(error):
    app.logger.exception("Database error")
    return jsonify(error="База данных недоступна или операция не выполнена"), 503


@app.errorhandler(requests.exceptions.RequestException)
def upstream_error(error):
    app.logger.exception("Calculation service error")
    if isinstance(error, requests.exceptions.Timeout):
        return jsonify(error="Сервис расчёта не ответил вовремя"), 504
    return jsonify(error="Сервис расчёта недоступен. Склад доступен через кнопку загрузки."), 502
