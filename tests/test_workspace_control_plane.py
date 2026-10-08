"""Control-plane regressions use an isolated identity database and vault."""
import json
from pathlib import Path
import sqlite3
import pytest
from fastapi.testclient import TestClient
from src.serving import api, v1_router as iam, workspace_router as workspace
from src.auth.authentication import AuthenticationEngine
from src.auth.audit import SecurityAuditLogger
from src.infrastructure.secrets.manager import SecretManager

PASSWORD='Workspace-Test-2026!'
@pytest.fixture
def control(tmp_path,monkeypatch):
 path=tmp_path/'identity.db'
 with sqlite3.connect(path) as db:
  db.executescript((Path(__file__).resolve().parents[1]/'db/migrations/001_initial_schema.sql').read_text(encoding='utf-8'))
  db.executescript((Path(__file__).resolve().parents[1]/'db/migrations/002_telemetry_feedback_policies.sql').read_text(encoding='utf-8'))
  for role in workspace.DEFAULT_ROLES:
   db.execute('INSERT OR IGNORE INTO roles(role_id,role_name,tier,is_assignable,requires_mfa) VALUES(?,?,?,1,0)',(role,role,'test'))
  for username,role,root in [('root_test','root',1),('platform_test','platform_admin',0),('security_test','security_admin',0),('mlops_test','mlops_engineer',0),('viewer_test','readonly_viewer',0)]:
   hashed,salt=AuthenticationEngine.hash_password(PASSWORD)
   db.execute('INSERT INTO users(user_id,username,email,password_hash,salt,is_root,must_change_password,created_at,updated_at) VALUES(?,?,?,?,?,?,0,?,?)',(username,username,username+'@test.invalid',hashed,salt,root,'2026-10-08','2026-10-08'))
   db.execute('INSERT INTO user_roles VALUES(?,?,?,?)',(username,role,'test','2026-10-08'))
 monkeypatch.setattr(iam,'DB_PATH',path)
 import src.infrastructure.security.governance_panel as panel
 monkeypatch.setattr(panel,'DB_PATH',path)
 monkeypatch.setattr(api.audit_manager,'record_request_audit',lambda **kwargs:None)
 monkeypatch.setattr(SecurityAuditLogger,'log_event',lambda *args,**kwargs:None)
 import src.infrastructure.secrets.manager as vault
 monkeypatch.setattr(vault,'VAULT_FILE',tmp_path/'vault.json')
 monkeypatch.delenv('PORTOPS_VAULT_KEY',raising=False)
 monkeypatch.delenv('CUSTOMS_ANA_API_KEY',raising=False)
 monkeypatch.setenv('TRAINING_MAX_ROWS','10000')
 monkeypatch.setenv('LOG_LEVEL','INFO')
 workspace.initialize()
 with workspace.connect() as db:
  db.execute('UPDATE workspace_config SET revision=1 WHERE id=1')
  db.execute('UPDATE workspace_setup SET completed=1 WHERE id=1')
 client=TestClient(api.app)
 return client,path

def login(client,name='root_test'):
 response=client.post('/api/v1/auth/login',json={'username':name,'password':PASSWORD})
 assert response.status_code==200,response.text
 csrf=client.get('/api/v1/auth/me').json()['csrf_token']
 client.headers['X-CSRF-Token']=csrf
 return response.json()

def test_browser_management_persists_password_gate_and_confirms_changes(control, tmp_path):
 import socket, threading, time
 import uvicorn
 from playwright.sync_api import sync_playwright
 _, path = control
 with sqlite3.connect(path) as db:
  db.execute("UPDATE users SET must_change_password=1 WHERE username='root_test'")
 listener=socket.socket();listener.bind(('127.0.0.1',0));listener.listen(128)
 port=listener.getsockname()[1]
 server=uvicorn.Server(uvicorn.Config(api.app,log_level='error',lifespan='off'))
 worker=threading.Thread(target=server.run,kwargs={'sockets':[listener]},daemon=True);worker.start()
 for _ in range(100):
  if server.started:break
  time.sleep(.05)
 errors=[]
 try:
  with sync_playwright() as playwright:
   browser=playwright.chromium.launch()
   page=browser.new_page(viewport={'width':1440,'height':960})
   page.on('pageerror',lambda error:errors.append(str(error)))
   page.goto(f'http://127.0.0.1:{port}/static/workspace/index.html')
   page.locator('#login-form input[name=username]').fill('root_test')
   page.locator('#login-form input[name=password]').fill(PASSWORD)
   page.locator('#login-form button').click()
   page.locator('#rotation-form').wait_for()
   page.reload();page.locator('#rotation-form').wait_for()
   assert page.locator('#management-nav button').count()==0
   page.goto(f'http://127.0.0.1:{port}/app')
   page.locator('#mandatory-logout').wait_for()
   page.evaluate('window.closeAuthModal()')
   page.keyboard.press('Escape')
   assert page.locator('#auth-iam-modal').is_visible()
   assert page.locator('#atab-password').is_visible()
   page.reload();page.locator('#mandatory-logout').wait_for()
   assert page.locator('#auth-iam-modal').is_visible()
   page.goto(f'http://127.0.0.1:{port}/static/workspace/index.html')
   page.locator('#rotation-form').wait_for()
   page.locator('[name=old]').fill(PASSWORD)
   page.locator('[name=new]').fill('Browser-New-Password-2026!')
   page.locator('[name=confirm]').fill('Browser-New-Password-2026!')
   page.locator('#rotation-form button').click()
   page.locator('#management-nav [data-route=configuration]').wait_for()
   for route in ['identity','modules','datasets','models','agents','secrets','security','configuration']:
    page.locator(f'[data-route={route}]').click()
    page.locator('main[aria-busy]').wait_for(state='detached')
    assert not page.locator('#retry-view').count(),page.locator('main').inner_text()
   form=page.locator('#config-form')
   form.locator('[name=display_name]').fill('Instancia verificada')
   form.locator('button[type=submit]').click()
   page.locator('#critical-confirmation[open]').wait_for()
   page.locator('#confirmation-cancel').click()
   with sqlite3.connect(path) as db:assert json.loads(db.execute('SELECT value FROM workspace_config').fetchone()[0])['display_name']!='Instancia verificada'
   form.locator('button[type=submit]').click()
   page.locator('#confirmation-accept').click()
   page.locator('#management-notice').filter(has_text='guardada').wait_for()
   with sqlite3.connect(path) as db:assert json.loads(db.execute('SELECT value FROM workspace_config').fetchone()[0])['display_name']=='Instancia verificada'
   for theme in ['theme-cyber-ocean','theme-radar-amber','theme-canal-emerald','theme-tactical-mono','theme-pacific-sunset','theme-midnight-cobalt']:
    page.locator('#management-theme').select_option(theme)
    assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
   evidence=Path('reports/control-plane-2026-10-08');evidence.mkdir(parents=True,exist_ok=True)
   page.screenshot(path=str(evidence/'management-desktop.png'),full_page=True)
   page.set_viewport_size({'width':390,'height':844})
   assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
   page.screenshot(path=str(evidence/'management-mobile.png'),full_page=True)
   assert not errors,errors
   browser.close()
 finally:
  server.should_exit=True;worker.join(timeout=10);listener.close()

def confirmed(client,action,path,payload,method='post'):
 response=client.post('/api/workspace/confirmations',json={'action':action,'payload':payload})
 assert response.status_code==200,response.text
 token=response.json()['confirmation_token']
 return getattr(client,method)('/api/workspace'+path,json={**payload,'confirmation_token':token})

def test_anonymous_bootstrap_cannot_mint_root_session(control):
 client,path=control
 for route in ['create-admins','change-root-password']:
  response=client.post('/api/v1/auth/first-run/'+route,json={})
  assert response.status_code==410
  assert not client.cookies.get('portops_session')
 with sqlite3.connect(path) as db:
  assert db.execute('SELECT count(*) FROM sessions').fetchone()[0]==0

def test_setup_confirmation_rechecks_concurrent_configuration(control,monkeypatch):
 client,path=control;login(client)
 with sqlite3.connect(path) as db:db.execute('UPDATE workspace_setup SET completed=0')
 original=workspace.consume
 def concurrent_change(user,action,body):
  original(user,action,body)
  with sqlite3.connect(path) as db:db.execute('UPDATE workspace_config SET revision=revision+1')
 monkeypatch.setattr(workspace,'consume',concurrent_change)
 assert confirmed(client,'setup.complete','/setup/complete',{'revision':1}).status_code==409
 with sqlite3.connect(path) as db:assert db.execute('SELECT completed FROM workspace_setup').fetchone()[0]==0

def test_saved_row_limit_controls_dataset_import(control):
 client,_=control;login(client)
 config=client.get('/api/workspace/configuration').json()
 config['value']['environment']['TRAINING_MAX_ROWS']='10'
 assert confirmed(client,'configuration.save','/configuration',config,'put').status_code==200
 csv='date,x,y\n'+'\n'.join(f'2026-01-{i+1:02d},{i},{2*i}' for i in range(11))
 response=client.post('/api/workspace/datasets',json={'name':'Too many rows','date_column':'date','target_column':'y','feature_columns':['x'],'csv_text':csv})
 assert response.status_code==422 and '10 filas' in response.text

def test_password_obligation_blocks_all_operational_apis_and_survives_session_reload(control):
 client,path=control
 with sqlite3.connect(path) as db:db.execute("UPDATE users SET must_change_password=1 WHERE username='root_test'")
 login(client)
 for method,path in [('get','/api/history/Puerto Balboa'),('get','/api/workspace/identity'),('post','/api/simulation/run'),('post','/api/config')]:
  response=getattr(client,method)(path)
  assert response.status_code==403,response.text
  assert response.json()['code']=='password_change_required'
 assert client.get('/api/v1/auth/me').json()['must_change_password']
 session=client.get('/api/workspace/session').json()
 assert session['workflow']['current_step']=='password' and not session['capabilities']
 response=client.post('/api/v1/auth/password/change',json={'old_password':PASSWORD,'new_password':PASSWORD})
 assert response.status_code==400
 response=client.post('/api/v1/auth/password/change',json={'old_password':PASSWORD,'new_password':'Workspace-New-Test-2026!'})
 assert response.status_code==200,response.text
 assert not client.get('/api/v1/auth/me').json()['must_change_password']
 client.headers['X-CSRF-Token']=client.get('/api/v1/auth/me').json()['csrf_token']
 assert client.post('/api/v1/auth/password/change',json={'old_password':'Workspace-New-Test-2026!','new_password':PASSWORD}).status_code==400
 assert client.post('/api/config',json={'default_monte_carlo_paths':100},headers={'X-CSRF-Token':client.get('/api/v1/auth/me').json()['csrf_token']}).status_code==200

def test_setup_uses_roles_not_usernames_and_blocks_operational_bypass(control):
 client,path=control;login(client)
 with sqlite3.connect(path) as db:
  db.execute('UPDATE workspace_setup SET completed=0 WHERE id=1')
  db.execute("DELETE FROM user_roles WHERE role_id='mlops_engineer'")
 session=client.get('/api/workspace/session').json()
 assert session['workflow']['current_step']=='administrators'
 assert client.post('/api/config',json={}).json()['code']=='setup_required'
 result=confirmed(client,'setup.complete','/setup/complete',{'revision':1})
 assert result.status_code==409
 result=confirmed(client,'identity.create','/identity/users',{'username':'model_operator','password':PASSWORD,'role_id':'mlops_engineer'})
 assert result.status_code==200,result.text
 assert client.get('/api/workspace/session').json()['workflow']['current_step']=='confirmation'
 result=confirmed(client,'setup.complete','/setup/complete',{'revision':1})
 assert result.status_code==200 and result.json()['current_step']=='ready'

def test_confirmation_is_actor_payload_bound_one_use_and_configuration_is_versioned(control):
 client,_=control;login(client)
 config=client.get('/api/workspace/configuration').json();payload={'revision':config['revision'],'value':config['value']}
 token=client.post('/api/workspace/confirmations',json={'action':'configuration.save','payload':payload}).json()['confirmation_token']
 changed=json.loads(json.dumps(payload));changed['value']['display_name']='tampered'
 assert client.put('/api/workspace/configuration',json={**changed,'confirmation_token':token}).status_code==409
 response=client.put('/api/workspace/configuration',json={**payload,'confirmation_token':token})
 assert response.status_code==200 and response.json()['revision']==2
 assert client.put('/api/workspace/configuration',json={**payload,'confirmation_token':token}).status_code==409
 response=confirmed(client,'configuration.save','/configuration',payload,'put')
 assert response.status_code==409
 assert client.get('/api/workspace/configuration').json()['revision']==2

def test_rbac_denies_viewer_and_prevents_privilege_delegation(control):
 client,_=control;login(client,'viewer_test')
 for path in ['/identity','/secrets','/security']:
  assert client.get('/api/workspace'+path).status_code==403
 assert client.get('/api/workspace/datasets').status_code==200
 login(client,'security_test')
 response=confirmed(client,'identity.create','/identity/users',{'username':'escalation','password':PASSWORD,'role_id':'platform_admin'})
 assert response.status_code==403
 response=confirmed(client,'identity.role','/identity/roles',{'role_id':'elevated','capabilities':['config.write']},'put')
 assert response.status_code==403

def test_root_protection_and_custom_role_persistence(control):
 client,_=control;login(client)
 response=confirmed(client,'identity.access','/identity/users',{'username':'root_test','roles':['readonly_viewer'],'active':False},'put')
 assert response.status_code==403
 response=confirmed(client,'identity.role','/identity/roles',{'role_id':'dataset_reviewer','capabilities':['workspace.read','datasets.read']},'put')
 assert response.status_code==200,response.text
 assert any(role['role_id']=='dataset_reviewer' for role in client.get('/api/workspace/identity').json()['roles'])

def test_secret_is_encrypted_not_echoed_or_audited(control,monkeypatch):
 client,_=control;login(client);value='opaque-secret-test-value'
 monkeypatch.setenv('CUSTOMS_ANA_API_KEY','')
 response=confirmed(client,'secret.rotate','/secrets',{'key':'CUSTOMS_ANA_API_KEY','value':value},'put')
 assert response.status_code==200,response.text
 import src.infrastructure.secrets.manager as vault
 stored=vault.VAULT_FILE.read_text()
 assert 'fernet:v1:' in stored and value not in stored
 assert SecretManager.get_secret('CUSTOMS_ANA_API_KEY')==value
 assert value not in client.get('/api/workspace/secrets').text
 assert value not in client.get('/api/workspace/security').text

def sample_csv():return 'fecha,objetivo,variable\n'+''.join(f'2026-01-{day:02d},{day*2+3},{day}\n' for day in range(1,21))

def test_dataset_versions_review_training_checksum_and_real_inference(control):
 client,_=control;login(client)
 payload={'name':'serie','csv_text':sample_csv(),'date_column':'fecha','target_column':'objetivo','feature_columns':['variable']}
 response=client.post('/api/workspace/datasets',json=payload);assert response.status_code==200,response.text
 ident=response.json()['id']
 train={'dataset_id':ident,'recipe_id':'ridge_numeric'}
 # Use the real recipe identifier exposed by the backend.
 train['recipe_id']=next(r['id'] for r in client.get('/api/workspace/models').json()['recipes'] if r['id']!='mean_baseline')
 assert confirmed(client,'model.train','/models/train',train).status_code==422
 assert confirmed(client,'dataset.review','/datasets/review',{'dataset_id':ident}).status_code==200
 trained=confirmed(client,'model.train','/models/train',train);assert trained.status_code==200,trained.text
 result=trained.json();assert result['metrics']['validation_rows']==4
 artifact=client.get('/api/workspace/models/'+result['model_id']+'/artifact');assert artifact.status_code==200
 assert artifact.json()['sha256']==result['artifact_sha256']
 prediction=client.post('/api/workspace/models/predict',json={'model_id':result['model_id'],'features':{'variable':25}})
 assert prediction.status_code==200 and abs(prediction.json()['prediction']-53)<3
 version=client.post('/api/workspace/datasets',json={**payload,'name':'segunda','parent_id':ident})
 assert version.status_code==200
 assert any(d['parent_id']==ident for d in client.get('/api/workspace/datasets').json()['items'])
 assert client.post('/api/workspace/models/predict',json={'model_id':result['model_id'],'features':{'wrong':1}}).status_code==422

def test_modules_enforced_agent_tool_allowlist_and_execution(control):
 client,_=control;login(client)
 payload={'id':'container-validator','name':'Container','description':'ValidaciÃ³n','tools':['validate_iso6346_container'],'enabled':True,'revision':0}
 assert confirmed(client,'agent.save','/agents',payload,'put').status_code==200
 result=confirmed(client,'agent.run','/agents/run',{'agent_id':payload['id'],'tool':'validate_iso6346_container','arguments':{'container_id':'MSCU6639871'}})
 assert result.status_code==200,result.text
 assert result.json()['source']=='local_backend'
 result=confirmed(client,'agent.run','/agents/run',{'agent_id':payload['id'],'tool':'get_port_forecast','arguments':{'port_name':'Puerto Balboa'}})
 assert result.status_code==403
 modules={'revision':1,'modules':{'datasets':True,'training':True,'agents':False}}
 assert confirmed(client,'modules.save','/modules',modules,'put').status_code==200
 assert confirmed(client,'agent.run','/agents/run',{'agent_id':payload['id'],'tool':'validate_iso6346_container','arguments':{'container_id':'MSCU6639871'}}).status_code==409

def test_audit_append_only_and_detects_storage_tampering(control):
 client,path=control;login(client)
 confirmed(client,'identity.role','/identity/roles',{'role_id':'read_only','capabilities':['workspace.read']},'put')
 assert client.get('/api/workspace/security').json()['chain']['valid']
 with sqlite3.connect(path) as db:
  with pytest.raises(sqlite3.IntegrityError):db.execute("UPDATE workspace_audit SET payload='{}'")
  db.execute('DROP TRIGGER workspace_audit_no_update')
  db.execute("UPDATE workspace_audit SET payload='{}'")
 assert not client.get('/api/workspace/security').json()['chain']['valid']

def test_configuration_rejects_external_paths_and_metadata_services(control):
 client,_=control;login(client)
 config=client.get('/api/workspace/configuration').json()
 config['value']['paths']['models']='../../outside'
 assert confirmed(client,'configuration.save','/configuration',config,'put').status_code==422
 config=client.get('/api/workspace/configuration').json()
 config['value']['services']['wazuh']['url']='http://169.254.169.254'
 assert confirmed(client,'configuration.save','/configuration',config,'put').status_code==422
