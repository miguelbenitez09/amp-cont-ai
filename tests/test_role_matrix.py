"""Every built-in role: server denials, UI controls, real workflows and revocation."""
import json
from pathlib import Path
import sqlite3
import threading
import socket
import time
import pytest
from src.serving import api, workspace_router as workspace
from src.auth.authentication import AuthenticationEngine
from tests.test_workspace_control_plane import control, login, confirmed, PASSWORD

READS={'/configuration':'config.read','/identity':'iam.write','/secrets':'secrets.write',
 '/services':'services.write','/modules':'modules.write','/datasets':'datasets.read',
 '/models':'models.read','/agents':'workspace.read','/security':'audit.read'}
WRITES=[('put','/configuration','config.write'),('post','/identity/users','iam.write'),
 ('put','/identity/users','iam.write'),('put','/identity/roles','iam.write'),('put','/secrets','secrets.write'),
 ('post','/services/test','services.write'),('put','/modules','modules.write'),('post','/datasets','datasets.write'),
 ('post','/datasets/review','datasets.review'),('post','/models/train','models.train'),
 ('post','/models/predict','models.predict'),('post','/models/review','models.review'),
 ('put','/agents','agents.write'),('post','/agents/run','agents.write')]

@pytest.fixture
def matrix(control):
 client,path=control
 with sqlite3.connect(path) as db:
  for role in workspace.DEFAULT_ROLES:
   name='audit_'+role;hashed,salt=AuthenticationEngine.hash_password(PASSWORD)
   db.execute('INSERT INTO users(user_id,username,email,password_hash,salt,is_root,must_change_password,created_at,updated_at) VALUES(?,?,?,?,?,?,0,?,?)',
    (name,name,name+'@test.invalid',hashed,salt,int(role=='root'),'2026-10-08','2026-10-08'))
   db.execute('INSERT INTO user_roles VALUES(?,?,?,?)',(name,role,'test','2026-10-08'))
 return client,path

@pytest.mark.parametrize('role',list(workspace.DEFAULT_ROLES))
def test_each_role_enforces_every_workspace_read_and_write(matrix,role):
 client,_=matrix;login(client,'audit_'+role)
 caps=set(workspace.DEFAULT_ROLES[role])
 assert set(client.get('/api/workspace/session').json()['capabilities'])==caps
 from src.auth.capability_permissions import permission_names
 assert set(client.get('/api/v1/auth/me').json()['permissions'])==set(permission_names(caps))
 metadata=next(item for item in client.get('/api/v1/roles').json()['roles'] if item['role_id']==role)
 assert set(metadata['capabilities'])==caps
 for route,cap in READS.items():
  result=client.get('/api/workspace'+route)
  assert result.status_code==(200 if cap in caps else 403),(role,route,result.text)
 for method,route,cap in WRITES:
  result=getattr(client,method)('/api/workspace'+route,json={})
  assert result.status_code==(422 if cap in caps else 403),(role,route,result.text)
 # Existing endpoints must obey the same capabilities, not a broad admin role.
 for route,cap in [('/api/v1/system/secrets','secrets.write'),('/api/v1/infra/config','config.read'),('/api/v1/audit/worm/blocks','audit.read')]:
  result=client.get(route)
  assert result.status_code==(200 if cap in caps else 403),(role,route,result.text)
 for route,cap in [('/api/config','config.write'),('/api/models/reproducible-train','models.train'),('/api/mcp/execute-tool','agents.write')]:
  result=client.post(route,json={})
  assert result.status_code in ({200,422} if cap in caps else {403}),(role,route,result.text)
 for route in ['/api/admin/users','/api/admin/delete-user','/api/v1/auth/users']:
  result=client.post(route,json={})
  assert result.status_code in ({410, 422} if 'iam.write' in caps else {403}),(role,route,result.text)

def test_security_admin_cannot_downgrade_superior_accounts_or_roles(matrix):
 client,_=matrix;login(client,'audit_security_admin')
 assert confirmed(client,'identity.access','/identity/users',{'username':'audit_platform_admin','roles':['readonly_viewer'],'active':False},'put').status_code==403
 assert confirmed(client,'identity.role','/identity/roles',{'role_id':'platform_admin','capabilities':['workspace.read']},'put').status_code==403
 assert confirmed(client,'identity.role','/identity/roles',{'role_id':'security_admin','capabilities':['workspace.read']},'put').status_code==403
 data=client.get('/api/workspace/identity').json()
 assert 'platform_admin' not in data['assignable_roles'] and 'root' not in data['assignable_roles']
 assert 'audit_platform_admin' not in data['manageable_users']
 assert 'readonly_viewer' in data['assignable_roles']

def test_root_role_label_without_root_flag_never_grants_root(matrix):
 client,path=matrix
 with sqlite3.connect(path) as db:db.execute("UPDATE users SET is_root=0 WHERE username='audit_root'")
 login(client,'audit_root')
 assert client.get('/api/workspace/session').json()['capabilities']==[]
 assert client.get('/api/workspace/identity').status_code==403
 assert client.post('/api/config',json={}).status_code==403

def test_required_mfa_is_persistent_and_cannot_be_enabled_without_code(matrix):
 client,path=matrix
 with sqlite3.connect(path) as db:db.execute("UPDATE roles SET requires_mfa=1 WHERE role_id='security_admin'")
 login(client,'audit_security_admin')
 session=client.get('/api/workspace/session').json()
 assert session['user']['mfa_setup_required'] and not session['capabilities']
 assert session['workflow']['current_step']=='mfa'
 assert client.get('/api/workspace/identity').status_code==403
 secret=client.post('/api/v1/auth/mfa/setup').json()['mfa_secret']
 with sqlite3.connect(path) as db:assert db.execute("SELECT mfa_enabled FROM users WHERE username='audit_security_admin'").fetchone()[0]==0
 assert client.post('/api/v1/auth/mfa/confirm',json={'code':'000000'}).status_code==401
 code=AuthenticationEngine.generate_totp_code(secret)
 assert client.post('/api/v1/auth/mfa/confirm',json={'code':code}).status_code==200
 client.headers['X-CSRF-Token']=client.get('/api/v1/auth/me').json()['csrf_token']
 assert client.get('/api/workspace/identity').status_code==200
 assert client.post('/api/v1/auth/mfa/setup').status_code==409
 client.post('/api/v1/auth/logout')
 challenge=client.post('/api/v1/auth/login',json={'username':'audit_security_admin','password':PASSWORD}).json()
 assert challenge['mfa_required'] and challenge['temp_token']
 assert client.post('/api/v1/auth/mfa/verify',json={'temp_token':challenge['temp_token'],'totp_code':code}).status_code==200
 assert client.get('/api/workspace/session').json()['user']['mfa_verified']

def test_manual_test_identity_is_local_only_even_with_stolen_session(matrix):
 client,path=matrix
 with sqlite3.connect(path) as db:
  db.execute('CREATE TABLE manual_test_accounts(user_id TEXT PRIMARY KEY,created_at TEXT)')
  db.execute('INSERT INTO manual_test_accounts VALUES(?,?)',('audit_root','2026-10-08'))
  db.execute("UPDATE roles SET requires_mfa=1 WHERE role_id='root'")
 login(client,'audit_root')
 assert client.get('/api/workspace/session').json()['user']['local_test_account']
 from fastapi.testclient import TestClient
 remote=TestClient(api.app,client=('203.0.113.10',44000))
 assert remote.post('/api/v1/auth/login',json={'username':'audit_root','password':PASSWORD}).status_code==403
 remote.cookies.update(client.cookies)
 assert remote.get('/api/workspace/session').status_code==403
 assert remote.get('/api/workspace/identity').status_code==403

def test_manual_preparation_preserves_other_accounts_and_enforces_local_test_scope(matrix,tmp_path):
 client,path=matrix
 with sqlite3.connect(path) as db:
  db.execute("UPDATE users SET username='root' WHERE username='audit_root'")
  previous=db.execute("SELECT password_hash FROM users WHERE username='platform_test'").fetchone()[0]
 from scripts.prepare_manual_role_accounts import prepare, ACCOUNTS
 result=prepare('Manual-Prueba-2026!',database=path,private_dir=tmp_path/'private')
 assert result['local_only'] and len(result['accounts'])==12
 with sqlite3.connect(path) as db:
  assert db.execute("SELECT password_hash FROM users WHERE username='platform_test'").fetchone()[0]==previous
  assert db.execute('SELECT count(*) FROM manual_test_accounts').fetchone()[0]==12
  assert db.execute('SELECT completed FROM workspace_setup').fetchone()[0]==1
 for name,role in ACCOUNTS.items():
  client.cookies.clear();client.headers.pop('X-CSRF-Token',None)
  response=client.post('/api/v1/auth/login',json={'username':name,'password':'Manual-Prueba-2026!'})
  assert response.status_code==200,(name,response.text)
  session=client.get('/api/workspace/session').json()
  assert session['workflow']['current_step']=='ready' and session['user']['local_test_account']
  assert set(session['capabilities'])==set(workspace.DEFAULT_ROLES[role])

def test_revocation_after_access_change_and_combined_role_union(matrix):
 _,path=matrix
 from fastapi.testclient import TestClient
 viewer=TestClient(api.app);root=TestClient(api.app)
 login(viewer,'audit_readonly_viewer');login(root,'audit_root')
 assert confirmed(root,'identity.access','/identity/users',{'username':'audit_readonly_viewer','roles':['data_steward','ml_reviewer'],'active':True},'put').status_code==200
 assert viewer.get('/api/workspace/session').status_code==401
 login(viewer,'audit_readonly_viewer')
 expected=set(workspace.DEFAULT_ROLES['data_steward'])|set(workspace.DEFAULT_ROLES['ml_reviewer'])
 assert set(viewer.get('/api/workspace/session').json()['capabilities'])==expected
 assert viewer.post('/api/workspace/models/train',json={}).status_code==403

def test_real_steward_review_engineer_training_and_independent_model_review(matrix):
 client,path=matrix;login(client,'audit_data_engineer')
 csv='date,x,y\n'+'\n'.join(f'2026-01-{i+1:02d},{i},{2*i+3}' for i in range(20))
 result=client.post('/api/workspace/datasets',json={'name':'Role pipeline','csv_text':csv,'date_column':'date','target_column':'y','feature_columns':['x']})
 assert result.status_code==200,result.text
 dataset=result.json()['id']
 assert confirmed(client,'dataset.review','/datasets/review',{'dataset_id':dataset}).status_code==403
 login(client,'audit_data_steward')
 assert confirmed(client,'dataset.review','/datasets/review',{'dataset_id':dataset}).status_code==200
 login(client,'audit_mlops_engineer')
 trained=confirmed(client,'model.train','/models/train',{'dataset_id':dataset,'recipe_id':'linear_baseline'})
 assert trained.status_code==200,trained.text
 model=trained.json()['model_id']
 login(client,'audit_ml_reviewer')
 assert confirmed(client,'model.review','/models/review',{'model_id':model,'decision':'approved','note':'Métricas y firma comprobadas.'}).status_code==200
 assert client.get('/api/workspace/models').json()['items'][0]['review']['decision']=='approved'
 # Same principal combining trainer and reviewer roles cannot self-approve.
 with sqlite3.connect(path) as db:db.execute('INSERT INTO user_roles VALUES(?,?,?,?)',('audit_mlops_engineer','ml_reviewer','test','2026-10-08'))
 login(client,'audit_mlops_engineer')
 assert confirmed(client,'model.review','/models/review',{'model_id':model,'decision':'approved','note':'Intento de autoaprobación.'}).status_code==403

def test_all_roles_browser_navigation_and_action_controls(matrix):
 import uvicorn
 from playwright.sync_api import sync_playwright
 _,path=matrix
 listener=socket.socket();listener.bind(('127.0.0.1',0));listener.listen(128)
 port=listener.getsockname()[1]
 server=uvicorn.Server(uvicorn.Config(api.app,log_level='error',lifespan='off'))
 worker=threading.Thread(target=server.run,kwargs={'sockets':[listener]},daemon=True);worker.start()
 for _ in range(100):
  if server.started:break
  time.sleep(.05)
 evidence=[]
 navcaps={'overview':'workspace.read','configuration':'config.write','services':'services.write','modules':'modules.write','identity':'iam.write',
  'datasets':'datasets.read','models':'models.read','agents':'workspace.read','secrets':'secrets.write','security':'audit.read'}
 try:
  with sync_playwright() as p:
   browser=p.chromium.launch()
   for role,caps in workspace.DEFAULT_ROLES.items():
    context=browser.new_context(viewport={'width':1440,'height':960});page=context.new_page();errors=[]
    page.on('pageerror',lambda error:errors.append(str(error)))
    page.goto(f'http://127.0.0.1:{port}/static/workspace/index.html')
    page.locator('#login-form [name=username]').fill('audit_'+role)
    page.locator('#login-form [name=password]').fill(PASSWORD)
    page.locator('#login-form button').click()
    page.locator('[data-route=overview]').wait_for()
    expected=[route for route,cap in navcaps.items() if cap in caps]
    assert page.locator('#management-nav button').evaluate_all('(buttons)=>buttons.map(b=>b.dataset.route)')==expected,role
    for route in expected:
     page.locator(f'[data-route={route}]').click()
     page.locator('main[aria-busy]').wait_for(state='detached')
     assert not page.locator('#retry-view').count(),(role,route,page.locator('main').inner_text())
     if route=='datasets':assert bool(page.locator('#dataset-form').count())==('datasets.write' in caps)
     if route=='models':
      assert bool(page.locator('#training-form').count())==('models.train' in caps)
      assert bool(page.locator('#model-review-form').count())==('models.review' in caps)
     if route=='agents':assert bool(page.locator('#agent-form').count())==('agents.write' in caps)
    page.goto(f'http://127.0.0.1:{port}/app')
    page.wait_for_function('window.activeSession?.user && document.querySelector("#workspace-access") && !document.querySelector("#workspace-access").hidden')
    page.wait_for_selector('body[data-role-ready="true"]')
    for tab,cap in [('tab-forecast','forecast.read'),('tab-simulation','simulation.run'),('tab-cot-swarm','agents.write'),('tab-data-platform','datasets.read')]:
     assert page.locator(f'.tab-btn[data-tab={tab}]').is_visible()==(cap in caps),(role,tab)
    assert not errors,(role,errors)
    evidence.append({'role':role,'capabilities':caps,'management_screens':expected,'operations_navigation':'passed','javascript_errors':errors})
    context.close()
   with sqlite3.connect(path) as db:db.execute("UPDATE roles SET requires_mfa=1 WHERE role_id='security_admin'")
   context=browser.new_context();page=context.new_page()
   page.goto(f'http://127.0.0.1:{port}/static/workspace/index.html')
   page.locator('#login-form [name=username]').fill('audit_security_admin')
   page.locator('#login-form [name=password]').fill(PASSWORD)
   page.locator('#login-form button').click()
   page.locator('#begin-mfa').wait_for();page.reload();page.locator('#begin-mfa').wait_for()
   assert page.locator('#management-nav button').count()==0
   page.locator('#begin-mfa').click();page.locator('#mfa-enrollment-form').wait_for()
   secret=page.locator('#workspace-main pre').first.inner_text()
   page.locator('#mfa-enrollment-form [name=code]').fill(AuthenticationEngine.generate_totp_code(secret))
   page.locator('#mfa-enrollment-form button').click()
   page.locator('[data-route=identity]').wait_for()
   evidence.append({'mfa_enrollment_browser':'passed','reload_preserves_required_factor':True})
   context.close()
   browser.close()
 finally:
  server.should_exit=True;worker.join(timeout=10);listener.close()
 out=Path('reports/roles-2026-10-08');out.mkdir(parents=True,exist_ok=True)
 (out/'browser-matrix.json').write_text(json.dumps(evidence,indent=2),encoding='utf-8')
