"""Exercise authorization before real router handlers, without starting workers."""
import ast
import asyncio
import time
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from services import admin_auth
from routers import evolution_router, admin


def profile(**kwargs):
    return SimpleNamespace(**dict(dict(email='operator@example.com', membership_tier='pro',
                                      status='active', email_verified=True), **kwargs))


@pytest.fixture
def application(monkeypatch):
    monkeypatch.setenv('ADMIN_EMAILS', 'operator@example.com')
    app = FastAPI()
    app.include_router(evolution_router.router)
    app.include_router(admin.router)
    # Compile the actual main endpoint definitions without importing main's
    # unrelated ML models or running background workers against production.
    names = {'health_readiness', 'health_liveness', 'root', 'datahub_reseed',
             'datahub_purge_stale_cache', 'datahub_clear_symbol', 'mt5_redis_diagnostics',
             'debug_info', 'connection_stats', 'debug_ml_model'}
    source = ast.parse((Path(__file__).parents[1] / 'main.py').read_text())
    nodes = [n for n in source.body if isinstance(n, ast.AsyncFunctionDef) and n.name in names]
    namespace = dict(app=app, Depends=Depends, require_admin=admin_auth.require_admin,
                     asyncio=asyncio, time=time, _APP_START_TIME=time.time(), ROUTERS_LOADED=True)
    exec(compile(ast.Module(body=nodes, type_ignores=[]), 'main.py', 'exec'), namespace)
    return app, namespace


@pytest.mark.parametrize('method,path,body', [
    ('POST', '/api/evolution/remote/command', {'kind': 'restart_bot'}),
    ('POST', '/api/evolution/analyst/run', {}),
    ('GET', '/api/evolution/remote/bot-performance', None),
    ('GET', '/api/evolution/remote/bot-trades-export.csv', None),
    ('GET', '/api/admin/reports', None),
    ('GET', '/api/admin/metrics', None),
    ('POST', '/api/datahub/reseed', {}),
    ('POST', '/api/datahub/purge-stale-cache', {}),
    ('POST', '/api/datahub/clear-symbol/NDX.INDX', {}),
    ('GET', '/api/debug', None),
    ('GET', '/api/debug/ml-model/NDX.INDX', None),
    ('GET', '/api/mt5-redis/diagnostics', None),
    ('GET', '/api/stats/connections', None),
])
def test_anonymous_cannot_reach_operational_handlers(application, monkeypatch, method, path, body):
    validate = AsyncMock(side_effect=AssertionError('anonymous request must not touch DB'))
    monkeypatch.setattr(admin_auth, 'validate_session', validate)
    response = TestClient(application[0]).request(method, path, json=body)
    assert response.status_code == 401
    validate.assert_not_awaited()


@pytest.mark.parametrize('user,status', [
    (None, 401),
    (profile(email='other@example.com'), 403),
    (profile(status='suspended'), 403),
    (profile(email_verified=False), 403),
    (profile(membership_tier='admin', status='banned'), 403),
])
def test_invalid_or_non_operator_cannot_queue_command(application, monkeypatch, user, status):
    monkeypatch.setattr(admin_auth, 'validate_session', AsyncMock(return_value=user))
    enqueue = Mock(side_effect=AssertionError('must not enqueue'))
    monkeypatch.setattr(evolution_router.remote, 'enqueue_command', enqueue)
    response = TestClient(application[0]).post('/api/evolution/remote/command',
        headers={'Authorization': 'Bearer test-session'}, json={'kind': 'restart_bot'})
    assert response.status_code == status
    enqueue.assert_not_called()


def test_operator_keeps_existing_command_workflow(application, monkeypatch):
    monkeypatch.setattr(admin_auth, 'validate_session', AsyncMock(return_value=profile()))
    enqueue = Mock(return_value={'id': 'fake-command'})
    monkeypatch.setattr(evolution_router.remote, 'enqueue_command', enqueue)
    monkeypatch.setattr(evolution_router.remote, 'command_to_run_meta', lambda cmd: cmd)
    response = TestClient(application[0]).post('/api/evolution/remote/command',
        headers={'Authorization': 'Bearer test-session'}, json={'kind': 'git_pull'})
    assert response.status_code == 200
    enqueue.assert_called_once()


def test_default_owner_policy_matches_existing_panel(application, monkeypatch):
    monkeypatch.delenv('ADMIN_EMAILS', raising=False)
    monkeypatch.setattr(admin_auth, 'validate_session', AsyncMock(return_value=profile(email='m.canodacioglu@gmail.com')))
    monkeypatch.setattr(evolution_router.evo, 'get_registry', lambda: [])
    response = TestClient(application[0]).get('/api/evolution/registry', headers={'Authorization': 'Bearer test'})
    assert response.status_code == 200


def test_liveness_is_public_and_database_auth_failure_is_not_ready(application, monkeypatch):
    import database.supabase_client as db
    monkeypatch.setattr(db, 'get_supabase_client', lambda: None)
    monkeypatch.setattr(db, 'is_auth_failed', lambda: True)
    client = TestClient(application[0])
    assert client.get('/api/health').status_code == 200
    response = client.get('/api/ready')
    assert response.status_code == 503
    assert response.json()['ok'] is False
    assert response.json()['checks']['degraded'] is True


def test_router_failure_prevents_ready_even_when_db_is_up(application, monkeypatch):
    import database.supabase_client as db
    query = Mock()
    query.table.return_value.select.return_value.limit.return_value.execute.return_value = {'error': None}
    monkeypatch.setattr(db, 'get_supabase_client', lambda: query)
    monkeypatch.setattr(db, 'is_auth_failed', lambda: False)
    application[1]['ROUTERS_LOADED'] = False
    response = TestClient(application[0]).get('/api/ready')
    assert response.status_code == 503
    assert response.json()['checks']['db'] is True


def test_readiness_does_not_return_database_exception_text(application, monkeypatch):
    import database.supabase_client as db
    def fail(): raise RuntimeError('redis://operator:secret-value@private-host')
    monkeypatch.setattr(db, 'get_supabase_client', fail)
    response = TestClient(application[0]).get('/api/ready')
    assert response.status_code == 503
    assert 'secret-value' not in response.text
    assert response.json()['checks']['db_error'] == 'unavailable'
