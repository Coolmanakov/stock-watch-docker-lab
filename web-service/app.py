"""Stateless service: deterministic, educational stock threshold calculation."""
from flask import Flask, jsonify, request
from werkzeug.exceptions import BadRequest, UnsupportedMediaType

app = Flask(__name__)


def calculate(product):
    if not isinstance(product, dict):
        raise ValueError("Товар должен быть объектом")
    limits = {"id": (1, 2147483647), "quantity": (0, 1000000),
              "daily_usage": (1, 10000), "lead_days": (1, 365),
              "safety_stock": (0, 1000000)}
    for key, (low, high) in limits.items():
        value = product.get(key)
        if type(value) is not int or not low <= value <= high:
            raise ValueError(f"Поле {key}: требуется целое число от {low} до {high}")
    name = product.get("name")
    if not isinstance(name, str) or not 1 <= len(name.strip()) <= 100:
        raise ValueError("Название товара должно содержать от 1 до 100 символов")
    threshold = product["daily_usage"] * product["lead_days"] + product["safety_stock"]
    quantity = product["quantity"]
    status = "critical" if quantity < threshold else "warning" if quantity == threshold else "ok"
    # Target: enough stock for delivery lead time plus seven days and safety stock.
    target = threshold + product["daily_usage"] * 7
    return {**product, "threshold": threshold, "status": status,
            "days_left": round(quantity / product["daily_usage"], 1),
            "recommended_order": max(0, target - quantity) if quantity <= threshold else 0}


@app.get("/health")
def health():
    return jsonify(status="ok", service="web-service")


@app.post("/analyze")
def analyze():
    data = request.get_json()
    products = data.get("products") if isinstance(data, dict) else None
    if not isinstance(products, list) or len(products) > 1000:
        raise ValueError("products: требуется массив из не более 1000 товаров")
    items = [calculate(p) for p in products]
    return jsonify(items=items, summary={
        "total": len(items),
        "critical": sum(x["status"] == "critical" for x in items),
        "warning": sum(x["status"] == "warning" for x in items),
        "ok": sum(x["status"] == "ok" for x in items)})


@app.errorhandler(ValueError)
@app.errorhandler(BadRequest)
@app.errorhandler(UnsupportedMediaType)
def invalid(error):
    return jsonify(error=str(error)), 400
