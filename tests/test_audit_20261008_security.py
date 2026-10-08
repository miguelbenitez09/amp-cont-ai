"""Security regression tests for the operational API and browser contract.

Administrative dispatch checks stub account creation; real auth flows use only a temporary database.
"""
from fastapi.testclient import TestClient
from src.serving.api import app
from src.infrastructure.security.governance_panel import PanamaSecurityGovernancePanel
import pytest
import sqlite3
from pathlib import Path
from src.serving import api, v1_router as iam
from src.auth.authentication import AuthenticationEngine
from src.auth.audit import SecurityAuditLogger


@pytest.fixture(autouse=True)
def isolated_audit(monkeypatch):
    monkeypatch.setattr(api.audit_manager, 'record_request_audit', lambda **kwargs: None)


@pytest.mark.parametrize('method,path', [
    ('post','/api/admin/users'), ('post','/api/admin/delete-user'),
    ('post','/api/admin/revoke-sessions'), ('post','/api/admin/verify-permission'),
    ('get','/api/admin/governance'), ('get','/api/v1/infra/config'),
    ('post','/api/v1/infra/config/db'), ('post','/api/v1/infra/config/minio'),
    ('post','/api/v1/infra/config/wazuh'), ('post','/api/config'),
    ('post','/api/v1/framework/profile'), ('post','/api/v1/guardrails/policies'),
    ('post','/api/mcp/souls'), ('post','/api/mcp/execute-tool'),
    ('post','/api/models/presets'), ('post','/api/models/reproducible-train'),
])
def test_legacy_sensitive_routes_deny_guests(method, path):
    response = getattr(TestClient(app),method)(path, **({'json':{}} if method=='post' else {}))
    assert response.status_code == 401


@pytest.fixture
def auth_database(tmp_path, monkeypatch):
    path = tmp_path / 'auth.sqlite3'
    with sqlite3.connect(path) as db:
        db.executescript('''
        CREATE TABLE users(user_id TEXT PRIMARY KEY,username TEXT,email TEXT,password_hash TEXT,salt TEXT,
          is_active INTEGER,is_root INTEGER,must_change_password INTEGER,mfa_enabled INTEGER,mfa_secret TEXT,
          failed_attempts INTEGER,created_at TEXT,updated_at TEXT);
        CREATE TABLE roles(role_id TEXT PRIMARY KEY,role_name TEXT);
        CREATE TABLE user_roles(user_id TEXT,role_id TEXT,assigned_by TEXT,assigned_at TEXT);
        CREATE TABLE role_permissions(role_id TEXT,permission_id TEXT);
        CREATE TABLE sessions(session_id TEXT PRIMARY KEY,user_id TEXT,token_hash TEXT,ip_address TEXT,
          user_agent TEXT,expires_at TEXT,is_revoked INTEGER,last_activity_at TEXT);
        CREATE TABLE workspace_setup(id INTEGER PRIMARY KEY,completed INTEGER,completed_at TEXT);
        INSERT INTO workspace_setup VALUES(1,1,'2026-10-08');
        ''')
        for username, role in [('audit_admin','platform_admin'),('audit_viewer','readonly_viewer')]:
            pwd,salt=AuthenticationEngine.hash_password('Audit-isolated-password-2026!')
            db.execute('INSERT INTO users VALUES(?,?,?,?,?,1,0,0,0,NULL,0,?,?)',(username,username,'test@example.test',pwd,salt,'2026-10-08','2026-10-08'))
            db.execute('INSERT INTO roles VALUES(?,?)',(role,role))
            db.execute('INSERT INTO user_roles VALUES(?,?,?,?)',(username,role,'test','2026-10-08'))
    monkeypatch.setattr(iam,'DB_PATH',path)
    import src.infrastructure.security.governance_panel as panel
    monkeypatch.setattr(panel,'DB_PATH',path)
    monkeypatch.setattr(SecurityAuditLogger,'log_event',lambda *args,**kwargs: None)
    monkeypatch.setattr(api,'runtime_config',dict(api.runtime_config))
    from src.serving import workspace_router as workspace
    workspace.initialize()
    with sqlite3.connect(path) as db:
        db.execute('UPDATE workspace_config SET revision=1 WHERE id=1')
        for role in ['security_admin','mlops_engineer']:
            db.execute('INSERT INTO roles VALUES(?,?)',(role,role))
            db.execute('INSERT INTO users SELECT ?,?,email,password_hash,salt,is_active,is_root,must_change_password,mfa_enabled,mfa_secret,failed_attempts,created_at,updated_at FROM users WHERE username=?',(role,role,'audit_viewer'))
            db.execute('INSERT INTO user_roles VALUES(?,?,?,?)',(role,role,'test','2026-10-08'))
    return path


def login_cookie(client, username):
    response=client.post('/api/v1/auth/login',json={'username':username,'password':'Audit-isolated-password-2026!'})
    assert response.status_code == 200
    assert 'httponly' in response.headers['set-cookie'].lower()
    me=client.get('/api/v1/auth/me')
    assert me.status_code == 200 and me.json()['is_authenticated']
    assert 'token' not in me.json()
    return me.json()['csrf_token']


def test_cookie_admin_flow_csrf_and_revocation(auth_database,monkeypatch):
    calls=[]
    monkeypatch.setattr(PanamaSecurityGovernancePanel,'register_user',lambda **kwargs: calls.append(kwargs) or {'status':'success'})
    client=TestClient(app)
    csrf=login_cookie(client,'audit_admin')
    payload={'username':'stub','full_name':'Stub','entity':'Test','role_id':'platform_admin'}
    assert client.post('/api/admin/users',json=payload).status_code == 403
    assert not calls
    assert client.post('/api/admin/users',json=payload,headers={'X-CSRF-Token':csrf,'Origin':'https://example.com'}).status_code == 403
    response=client.post('/api/admin/users',json=payload,headers={'X-CSRF-Token':csrf,'Origin':'http://testserver'})
    assert response.status_code == 410 and not calls
    assert client.post('/api/config',json={'default_monte_carlo_paths':100},headers={'X-CSRF-Token':csrf}).status_code==200
    cookie=client.cookies.get('portops_session')
    assert client.post('/api/v1/auth/logout',headers={'X-CSRF-Token':csrf}).status_code==200
    assert not client.get('/api/v1/auth/me').json()['is_authenticated']
    assert client.get('/api/admin/governance',headers={'Authorization':f'Bearer {cookie}'}).status_code==401


def test_cookie_viewer_cannot_mutate_admin_or_config(auth_database):
    client=TestClient(app)
    csrf=login_cookie(client,'audit_viewer')
    for path,payload in [('/api/admin/users',{'username':'stub','full_name':'Stub','entity':'Test'}),('/api/config',{})]:
        assert client.post(path,json=payload,headers={'X-CSRF-Token':csrf}).status_code==403
    assert client.get('/api/admin/governance').status_code==403


def test_inactive_user_session_and_password_rotation_gate(auth_database):
    client=TestClient(app)
    csrf=login_cookie(client,'audit_admin')
    with sqlite3.connect(auth_database) as db:
        db.execute("UPDATE users SET must_change_password=1 WHERE username='audit_admin'")
    assert client.get('/api/admin/governance').status_code==403
    with sqlite3.connect(auth_database) as db:
        db.execute("UPDATE users SET is_active=0 WHERE username='audit_admin'")
    assert client.get('/api/admin/governance').status_code==401


def test_security_overview_does_not_invent_runtime_evidence(auth_database):
    overview=PanamaSecurityGovernancePanel.get_security_overview()
    assert overview['tls_certificate']['status']=='not_verified'
    assert overview['tls_certificate']['protocol'] is None
    assert overview['cookie_hardening']['cookie_name']=='portops_session'
    assert overview['cookie_hardening']['same_site']=='Lax'
    assert overview['anti_ransomware_and_dr']['status']=='not_verified'


def test_failed_security_inventory_is_reported_degraded(monkeypatch):
    def unavailable():
        raise sqlite3.OperationalError('unavailable')
    monkeypatch.setattr(PanamaSecurityGovernancePanel,'_get_db',unavailable)
    overview=PanamaSecurityGovernancePanel.get_security_overview()
    assert overview['status']=='degraded' and not overview['inventory_verified']
    assert overview['first_run_initialized'] is None


def test_new_admin_created_account_requires_password_rotation(auth_database):
    result=PanamaSecurityGovernancePanel.register_user(username='temporary_user', full_name='Temporary User',
        entity='Test', role_id='readonly_viewer', password='Temporary-isolated-password-2026!')
    assert result['status']=='success'
    with sqlite3.connect(auth_database) as db:
        assert db.execute("SELECT must_change_password FROM users WHERE username='temporary_user'").fetchone()[0]==1


def test_rejected_csrf_request_is_audited(monkeypatch):
    events=[]
    monkeypatch.setattr(api.audit_manager,'record_request_audit',lambda **kwargs: events.append(kwargs))
    response=TestClient(app).post('/api/config',json={},headers={'Origin':'https://example.com'})
    assert response.status_code==403
    assert len(events)==1 and events[0]['status_code']==403


def test_ui_does_not_persist_bearer_and_selectors_are_named():
    from bs4 import BeautifulSoup
    root=Path('src/serving/static')
    for name in ['app.js','auth_flow.js','browser_security.js']:
        source=(root/'js'/name).read_text(encoding='utf-8')
        assert 'localStorage.setItem("portops_token"' not in source
        assert 'localStorage.getItem("portops_token"' not in source
    soup=BeautifulSoup((root/'index.html').read_text(encoding='utf-8'),'html.parser')
    assert soup.select_one('#nav-lang-select')['aria-label']
    assert soup.select_one('#theme-selector')['aria-label']
    modal=soup.select_one('#auth-iam-modal')
    assert modal['role']=='dialog' and modal['aria-modal']=='true'
    assert soup.find(id=modal['aria-labelledby'])
    for tag in soup.select('[src^="https://cdn.jsdelivr.net"], [href^="https://cdn.jsdelivr.net"]'):
        assert tag.get('integrity','').startswith('sha384-') and tag['crossorigin']=='anonymous'


def test_browser_cookie_login_reload_admin_write_and_logout(auth_database, tmp_path):
    import socket
    import threading
    import time
    import uvicorn
    from playwright.sync_api import sync_playwright, expect

    listener=socket.socket()
    listener.bind(('127.0.0.1',0))
    port=listener.getsockname()[1]
    server=uvicorn.Server(uvicorn.Config(app,host='127.0.0.1',port=port,lifespan='off',log_level='error'))
    thread=threading.Thread(target=lambda:server.run(sockets=[listener]),daemon=True)
    thread.start()
    try:
        deadline=time.monotonic()+10
        while not server.started and time.monotonic()<deadline:
            time.sleep(.05)
        assert server.started
        with sync_playwright() as p:
            browser=p.chromium.launch(headless=True)
            page=browser.new_page()
            page.goto(f'http://127.0.0.1:{port}/app',wait_until='domcontentloaded')
            page.locator('#btn-auth-iam').click()
            page.locator('#auth-input-username').fill('audit_admin')
            page.locator('#auth-input-password').fill('Audit-isolated-password-2026!')
            page.locator('#btn-submit-login').click()
            expect(page.locator('#hud-active-role')).to_contain_text('platform_admin')
            assert page.evaluate("window.activeSession?.user?.username === 'audit_admin'")
            assert page.evaluate("localStorage.getItem('portops_token')") is None
            assert 'portops_session' not in page.evaluate('document.cookie')
            page.reload(wait_until='domcontentloaded')
            expect(page.locator('#hud-active-role')).to_contain_text('platform_admin')
            assert page.evaluate("window.activeSession?.user?.username === 'audit_admin' && !!window.portopsCsrfToken")
            assert page.evaluate('window.activeSession.token') is None
            # A stale token from another tab must refresh safely before one retry.
            page.evaluate("window.portopsCsrfToken = 'outdated-tab-token'")
            code=page.evaluate("""async () => (await fetch('/api/config', {
                method:'POST', headers:{'Content-Type':'application/json'},
                body:JSON.stringify({default_monte_carlo_paths:100})
            })).status""")
            assert code==200
            page.locator('#btn-auth-iam').click()
            page.locator('#auth-session-profile-view button[onclick="window.executeLogout()"] ').click()
            expect(page.locator('#hud-active-role')).to_contain_text('Invitado')
            assert page.evaluate("async () => (await fetch('/api/admin/governance')).status")==401
            assert page.evaluate("async () => !(await (await fetch('/api/v1/auth/me')).json()).is_authenticated")
            browser.close()
    finally:
        server.should_exit=True
        thread.join(timeout=10)
        listener.close()


def test_guest_cannot_invoke_legacy_admin_user_creation(monkeypatch):
    calls = []
    def fake_register(**kwargs):
        calls.append(kwargs)
        return {'status': 'success', 'audit_stub': True}
    monkeypatch.setattr(PanamaSecurityGovernancePanel, 'register_user', fake_register)
    with TestClient(app) as client:
        response = client.post('/api/admin/users', json={
            'username': 'audit_stub_only', 'full_name': 'Audit Stub',
            'entity': 'Audit', 'role_id': 'root_owner',
        })
    assert response.status_code in (401, 403), f'Guest reached admin service: HTTP {response.status_code}, calls={len(calls)}'
    assert not calls


def test_guest_cannot_read_legacy_admin_inventory(monkeypatch):
    monkeypatch.setattr(PanamaSecurityGovernancePanel, 'get_security_overview', lambda: {'active_users': [{'username': 'stub'}]})
    with TestClient(app) as client:
        response = client.get('/api/admin/governance')
    assert response.status_code in (401,403), f'Guest inventory returned HTTP {response.status_code}'


def test_expired_browser_cookie_is_removed_on_session_refresh():
    client = TestClient(app)
    client.cookies.set('portops_session', 'expired-or-invalid-cookie', domain='testserver.local', path='/')
    response = client.get('/api/v1/auth/me')
    assert response.status_code == 401
    assert 'Max-Age=0' in response.headers['set-cookie']
    assert 'portops_session' not in client.cookies


def test_unavailable_simulator_preserves_recoverable_status(monkeypatch):
    monkeypatch.setitem(api.ml_artifacts, 'stress_tester', None)
    response = TestClient(app).post('/api/simulation/run', json={
        'port':'Puerto Balboa', 'scenario_type':'baseline', 'num_paths':100, 'horizon_months':3
    })
    assert response.status_code == 503
    assert 'no inicializado' in response.json()['detail']
