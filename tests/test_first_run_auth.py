"""Initial setup regressions never change the live root database or credentials."""
import sqlite3
from tests.test_workspace_control_plane import control, login, confirmed, PASSWORD

def test_legacy_bootstrap_cannot_issue_root_session(control):
    client, _ = control
    for route in ['create-admins', 'change-root-password']:
        assert client.post('/api/v1/auth/first-run/'+route, json={}).status_code == 410
    assert not client.cookies.get('portops_session')

def test_initial_setup_requires_password_and_persisted_confirmation(control):
    client, path = control
    with sqlite3.connect(path) as db:
        db.execute("UPDATE users SET must_change_password=1 WHERE username='root_test'")
        db.execute('UPDATE workspace_setup SET completed=0 WHERE id=1')
    login(client)
    assert client.get('/api/workspace/session').json()['workflow']['current_step'] == 'password'
    response = client.post('/api/v1/auth/password/change', json={'old_password':PASSWORD,'new_password':'First-Run-Isolated-2026!'})
    assert response.status_code == 200
    client.headers['X-CSRF-Token'] = client.get('/api/v1/auth/me').json()['csrf_token']
    assert client.get('/api/workspace/session').json()['workflow']['current_step'] == 'confirmation'
    assert client.post('/api/workspace/setup/complete', json={'revision':1}).status_code == 422
    assert confirmed(client,'setup.complete','/setup/complete',{'revision':1}).status_code == 200
    assert client.get('/api/workspace/session').json()['workflow']['current_step'] == 'ready'
