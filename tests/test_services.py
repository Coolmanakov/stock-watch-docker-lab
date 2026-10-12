import importlib.util
from pathlib import Path
import pytest
import requests
import psycopg

ROOT = Path(__file__).resolve().parents[1]


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, ROOT / path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


web = module('stock_web', 'web-service/app.py')
backend = module('stock_backend', 'backend/app.py')
PRODUCT = dict(id=1, name='Cable', quantity=12, daily_usage=5, lead_days=3, safety_stock=5)


@pytest.mark.parametrize('quantity,status,order', [(12, 'critical', 43), (20, 'warning', 35), (21, 'ok', 0), (0, 'critical', 55)])
def test_threshold_boundary(quantity, status, order):
    result = web.calculate({**PRODUCT, 'quantity': quantity})
    assert result['threshold'] == 20
    assert result['status'] == status
    assert result['recommended_order'] == order


def test_snapshot_summary_and_empty_stock():
    client = web.app.test_client()
    response = client.post('/analyze', json={'products': [PRODUCT, {**PRODUCT, 'id': 2, 'quantity': 20}, {**PRODUCT, 'id': 3, 'quantity': 80}]})
    assert response.status_code == 200
    assert response.json['summary'] == dict(total=3, critical=1, warning=1, ok=1)
    assert client.post('/analyze', json={'products': []}).json['summary']['total'] == 0


@pytest.mark.parametrize('key,value', [('quantity', -1), ('daily_usage', 0), ('lead_days', True), ('safety_stock', 1.5), ('name', ' '), ('quantity', 1000001)])
def test_invalid_product_not_calculated(key, value):
    response = web.app.test_client().post('/analyze', json={'products': [{**PRODUCT, key: value}]})
    assert response.status_code == 400
    assert 'error' in response.json


@pytest.mark.parametrize('body', [None, {}, {'products': 'bad'}, {'products': [None]}, {'products': [PRODUCT] * 1001}])
def test_invalid_analysis_payload(body):
    response = web.app.test_client().post('/analyze', json=body)
    assert response.status_code == 400


def test_malformed_json_and_content_type():
    for mod, endpoint in [(web, '/analyze'), (backend, '/api/products')]:
        client = mod.app.test_client()
        assert client.post(endpoint, data='{bad', content_type='application/json').status_code == 400
        assert client.post(endpoint, data='plain').status_code == 400


def test_backend_validates_before_connecting(monkeypatch):
    def unexpected():
        pytest.fail('Invalid input must not open a DB connection')
    monkeypatch.setattr(backend, 'connect', unexpected)
    response = backend.app.test_client().post('/api/products', json={**PRODUCT, 'daily_usage': 0})
    assert response.status_code == 400


def test_database_outage_has_json_error(monkeypatch):
    def unavailable():
        raise psycopg.OperationalError('private connection details')
    monkeypatch.setattr(backend, 'connect', unavailable)
    response = backend.app.test_client().get('/api/products')
    assert response.status_code == 503
    assert 'private' not in response.json['error']


@pytest.mark.parametrize('error,status', [(requests.Timeout('private'), 504), (requests.ConnectionError('private'), 502)])
def test_service_outage_does_not_save_snapshot(monkeypatch, error, status):
    calls = []
    class Connection:
        def __enter__(self): return self
        def __exit__(self, *args): pass
    def connect():
        calls.append('read')
        return Connection()
    def unavailable(*args, **kwargs): raise error
    monkeypatch.setattr(backend, 'connect', connect)
    monkeypatch.setattr(backend, 'products', lambda conn: [PRODUCT])
    monkeypatch.setattr(backend.requests, 'post', unavailable)
    response = backend.app.test_client().post('/api/analysis')
    assert response.status_code == status
    assert calls == ['read']
    assert 'private' not in response.json['error']
