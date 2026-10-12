#!/usr/bin/env python3
"""Run against the real four-container application. Uses Python stdlib only."""
import json
import sys
import urllib.request

BASE = (sys.argv[1] if len(sys.argv) > 1 else 'http://localhost:8080').rstrip('/')


def api(path, method='GET', data=None):
    encoded = json.dumps(data).encode() if data is not None else None
    request = urllib.request.Request(BASE + '/api/' + path, data=encoded, method=method,
                                    headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(request, timeout=20) as response:
        payload = response.read()
        return response.status, json.loads(payload) if payload else None


status, initial = api('products')
assert status == 200 and isinstance(initial['items'], list)
product = None
try:
    status, product = api('products', 'POST', dict(name='Smoke test cable', quantity=12,
                           daily_usage=5, lead_days=3, safety_stock=5))
    assert status == 201
    product_id = product['id']
    status, result = api('analysis', 'POST')
    assert status == 201
    item = next(p for p in result['items'] if p['id'] == product_id)
    assert (item['threshold'], item['status'], item['recommended_order']) == (20, 'critical', 43)
    status, history = api('analyses')
    saved = next(h for h in history['items'] if h['id'] == result['id'])
    assert saved['result']['items'] == result['items']
    status, edited = api('products/' + str(product_id), 'PUT', {**product, 'quantity': 80})
    assert status == 200 and edited['quantity'] == 80
    _, result = api('analysis', 'POST')
    item = next(p for p in result['items'] if p['id'] == product_id)
    assert item['status'] == 'ok' and item['recommended_order'] == 0
    assert api('products/' + str(product_id), 'DELETE')[0] == 204
    _, items = api('products')
    assert all(p['id'] != product_id for p in items['items'])
    product = None
    print('PASS: PostgreSQL CRUD, HTTP calculation, persisted analysis history')
finally:
    if product is not None:
        api('products/' + str(product['id']), 'DELETE')
