"""Integrated control plane: the operational identity is the only authority.

Desired configuration is persisted; listeners and external services are never silently
restarted. Critical mutations require an expiring actor-and-payload confirmation.
"""
from __future__ import annotations
from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
import ipaddress
import json
import os
from pathlib import Path
import secrets
import socket
import sqlite3
import time
import uuid
from urllib.parse import urlsplit

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, ConfigDict
import httpx
from src.serving import v1_router as iam
from src.framework.ml import ModelService
from src.auth.authentication import AuthenticationEngine
from src.auth.password_policy import PasswordPolicy
from src.infrastructure.secrets.manager import SecretManager
from src.mcp.tools import get_available_tools_schema

router = APIRouter(prefix='/api/workspace', tags=['Integrated Workspace'])
CAPABILITIES = ['workspace.read','config.read','config.write','iam.write','audit.read','audit.verify','secrets.write',
 'services.write','agents.write','modules.write','datasets.read','datasets.write','datasets.review',
 'models.read','models.train','models.predict','models.review','forecast.read','simulation.run','simulation.export']
DEFAULT_ROLES = {
 'root': CAPABILITIES,
 'platform_admin': ['workspace.read','config.read','config.write','iam.write','audit.read','audit.verify','services.write','agents.write','modules.write','datasets.read','models.read','forecast.read','simulation.run','simulation.export'],
 'security_admin': ['workspace.read','config.read','iam.write','audit.read','audit.verify','secrets.write','services.write'],
 'mlops_engineer': ['workspace.read','datasets.read','datasets.write','datasets.review','models.read','models.train','models.predict','agents.write','modules.write','audit.read','forecast.read','simulation.run'],
 'data_engineer': ['workspace.read','datasets.read','datasets.write','models.read','audit.read','forecast.read'],
 'data_steward': ['workspace.read','datasets.read','datasets.review','audit.read'],
 'ml_reviewer': ['workspace.read','datasets.read','models.read','models.review','audit.read','audit.verify'],
 'port_operator': ['workspace.read','datasets.read','audit.read','forecast.read','simulation.run'],
 'simulation_analyst': ['workspace.read','datasets.read','audit.read','forecast.read','simulation.run','simulation.export'],
 'api_consumer': ['workspace.read','forecast.read'],
 'readonly_viewer': ['workspace.read','datasets.read','models.read','forecast.read','audit.verify'],
 'compliance_auditor': ['workspace.read','config.read','audit.read','audit.verify','datasets.read','models.read','models.review'],
}
DEFAULT_CONFIG = {'display_name':'Panamá PortOps-AI','gateway_port':8000,'api_port':8001,
 'paths':{'datasets':'data/workspace/datasets','models':'data/workspace/models','artifacts':'data/workspace/artifacts'},
 'modules':{'datasets':True,'training':True,'agents':True},
 'environment':{'LOG_LEVEL':'INFO','TRAINING_MAX_ROWS':'10000'},
 'services':{name:{'url':'','enabled':False,'secret_ref':''} for name in ['wazuh','ollama','vllm','mlflow','minio']}}
EXECUTABLE_TOOLS={'validate_iso6346_container','lookup_panama_customs_tariff','get_port_forecast','query_maritime_knowledge'}
SERVICE_PATHS={'wazuh':'/manager/status','ollama':'/api/tags','vllm':'/v1/models','mlflow':'/health','minio':'/minio/health/live'}
SAFE_ENV={'LOG_LEVEL','TRAINING_MAX_ROWS','OMP_NUM_THREADS','OPENAI_MODEL','DEFAULT_OLLAMA_MODEL','DEFAULT_VLLM_MODEL'}
ROLE_LEVELS={'platform_admin':80,'security_admin':80,'mlops_engineer':50,'ml_reviewer':40,
 'data_engineer':30,'compliance_auditor':30,'data_steward':20,'port_operator':20,
 'simulation_analyst':20,'readonly_viewer':10,'api_consumer':10}

def now(): return datetime.now(timezone.utc).isoformat()
def canonical(value): return json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False)
def digest(value): return hashlib.sha256(canonical(value).encode()).hexdigest()

@contextmanager
def connect():
 with sqlite3.connect(iam.DB_PATH,timeout=20) as db:
  db.row_factory=sqlite3.Row
  db.execute('PRAGMA foreign_keys=ON')
  yield db

def initialize():
 with connect() as db:
  db.executescript("""
  CREATE TABLE IF NOT EXISTS workspace_config(id INTEGER PRIMARY KEY CHECK(id=1),revision INTEGER NOT NULL,value TEXT NOT NULL);
  CREATE TABLE IF NOT EXISTS workspace_roles(role_id TEXT PRIMARY KEY,capabilities TEXT NOT NULL);
  CREATE TABLE IF NOT EXISTS workspace_confirmations(token_hash TEXT PRIMARY KEY,actor TEXT NOT NULL,action TEXT NOT NULL,payload_hash TEXT NOT NULL,expires REAL NOT NULL);
  CREATE TABLE IF NOT EXISTS workspace_audit(id INTEGER PRIMARY KEY AUTOINCREMENT,actor TEXT NOT NULL,action TEXT NOT NULL,payload TEXT NOT NULL,created_at TEXT NOT NULL,prev_hash TEXT NOT NULL,block_hash TEXT NOT NULL);
  CREATE TRIGGER IF NOT EXISTS workspace_audit_no_update BEFORE UPDATE ON workspace_audit BEGIN SELECT RAISE(ABORT,'Audit is append-only'); END;
  CREATE TRIGGER IF NOT EXISTS workspace_audit_no_delete BEFORE DELETE ON workspace_audit BEGIN SELECT RAISE(ABORT,'Audit is append-only'); END;
  CREATE TABLE IF NOT EXISTS workspace_setup(id INTEGER PRIMARY KEY CHECK(id=1),completed INTEGER NOT NULL DEFAULT 0,completed_at TEXT);
  CREATE TABLE IF NOT EXISTS workspace_dataset_versions(id TEXT PRIMARY KEY,parent_id TEXT);
  CREATE TABLE IF NOT EXISTS workspace_model_reviews(model_id TEXT PRIMARY KEY,decision TEXT NOT NULL,actor TEXT NOT NULL,created_at TEXT NOT NULL,note TEXT NOT NULL);
  CREATE TABLE IF NOT EXISTS workspace_agents(id TEXT PRIMARY KEY,name TEXT NOT NULL,description TEXT NOT NULL,tools TEXT NOT NULL,enabled INTEGER NOT NULL,revision INTEGER NOT NULL);
  """)
  db.execute('INSERT OR IGNORE INTO workspace_config VALUES(1,0,?)',(canonical(DEFAULT_CONFIG),))
  db.execute('INSERT OR IGNORE INTO workspace_setup VALUES(1,0,NULL)')
  for role,caps in DEFAULT_ROLES.items():
   db.execute('INSERT OR IGNORE INTO workspace_roles VALUES(?,?)',(role,canonical(caps)))
  db.execute('UPDATE workspace_roles SET capabilities=? WHERE role_id=?',(canonical(CAPABILITIES),'root'))
  previous_defaults={
   'platform_admin':['workspace.read','config.write','iam.write','audit.read','services.write','agents.write','modules.write','datasets.read','models.read'],
   'security_admin':['workspace.read','iam.write','audit.read','secrets.write','services.write'],
   'mlops_engineer':['workspace.read','datasets.read','datasets.write','models.read','models.train','models.predict','agents.write','modules.write'],
   'data_engineer':['workspace.read','datasets.read','datasets.write','models.read'],
   'readonly_viewer':['workspace.read','datasets.read','models.read'],
   'compliance_auditor':['workspace.read','audit.read','datasets.read','models.read']}
  db.execute('CREATE TABLE IF NOT EXISTS workspace_migrations(version INTEGER PRIMARY KEY)')
  if not db.execute('SELECT 1 FROM workspace_migrations WHERE version=2').fetchone():
   for role,previous in previous_defaults.items():
    row=db.execute('SELECT capabilities FROM workspace_roles WHERE role_id=?',(role,)).fetchone()
    if row and set(json.loads(row[0]))==set(previous):db.execute('UPDATE workspace_roles SET capabilities=? WHERE role_id=?',(canonical(DEFAULT_ROLES[role]),role))
   db.execute('INSERT INTO workspace_migrations VALUES(2)')
 service().initialize()

def service():
 try:
  with connect() as db:row=db.execute('SELECT value FROM workspace_config WHERE id=1').fetchone()
  maximum=int(json.loads(row[0])['environment'].get('TRAINING_MAX_ROWS','10000')) if row else 10000
 except sqlite3.OperationalError:maximum=10000
 return ModelService(iam.DB_PATH,iam.DB_PATH.parent/'workspace',max_rows=maximum)

def capabilities(user):
 if user.get('is_root'): return list(CAPABILITIES)
 with connect() as db:
  rows=db.execute('SELECT role_id,capabilities FROM workspace_roles').fetchall()
 caps={c for row in rows if row['role_id']!='root' and row['role_id'] in user.get('roles',[]) for c in json.loads(row['capabilities'])}
 # Explicit capabilities only; no invented grant from presentation state.
 return sorted(caps)

def check_delegation(user,roles):
 if user.get('is_root'):return
 own=set(capabilities(user))
 with connect() as db:
  grants={row['role_id']:set(json.loads(row['capabilities'])) for row in db.execute('SELECT * FROM workspace_roles')}
 level=max((ROLE_LEVELS.get(role,0) for role in user.get('roles',[])),default=0)
 for role in roles:
  grant=grants.get(role,set())
  standard_lower=role in ROLE_LEVELS and ROLE_LEVELS[role]<level and grant<=set(DEFAULT_ROLES[role])
  if role=='root' or (grant-own and not standard_lower):raise HTTPException(403,'Sólo root puede delegar o modificar roles superiores o administrativos equivalentes con otros privilegios.')

def authenticated(user=Depends(iam.get_current_user_and_session)):
 if not user.get('is_authenticated'): raise HTTPException(401,'Inicia sesión para acceder al espacio de gestión.')
 if user.get('must_change_password'): raise HTTPException(403,'Completa el cambio obligatorio de contraseña.')
 if user.get('mfa_setup_required') or user.get('mfa_verification_required'):raise HTTPException(403,'Completa MFA antes de continuar.')
 initialize()
 return user

def require(cap):
 def check(user=Depends(authenticated)):
  if cap not in capabilities(user): raise HTTPException(403,f'Esta operación requiere {cap}.')
  return user
 return check

def audit(db,user,action,payload):
 previous=db.execute('SELECT block_hash FROM workspace_audit ORDER BY id DESC LIMIT 1').fetchone()
 prev=previous[0] if previous else '0'*64
 stamp=now();encoded=canonical(payload)
 block=hashlib.sha256(canonical([prev,user['user_id'],action,encoded,stamp]).encode()).hexdigest()
 db.execute('INSERT INTO workspace_audit(actor,action,payload,created_at,prev_hash,block_hash) VALUES(?,?,?,?,?,?)',(user['user_id'],action,encoded,stamp,prev,block))

def consume(user,action,body):
 token=body.confirmation_token
 payload=body.model_dump(exclude={'confirmation_token'})
 with connect() as db:
  db.execute('BEGIN IMMEDIATE')
  row=db.execute('SELECT * FROM workspace_confirmations WHERE token_hash=?',(hashlib.sha256(token.encode()).hexdigest(),)).fetchone()
  if not row or row['actor']!=user['user_id'] or row['action']!=action or row['payload_hash']!=digest(payload) or row['expires']<time.time():
   raise HTTPException(409,'La confirmación venció o no coincide con esta operación. Revisa y confirma de nuevo.')
  db.execute('DELETE FROM workspace_confirmations WHERE token_hash=?',(row['token_hash'],))
 return payload

class Strict(BaseModel): model_config=ConfigDict(extra='forbid')
class Confirm(Strict):
 action:str=Field(min_length=1,max_length=80)
 payload:dict
class Critical(Strict): confirmation_token:str=Field(min_length=20,max_length=160)
class ConfigUpdate(Critical):
 revision:int=Field(ge=0)
 value:dict
class UserCreate(Critical):
 username:str=Field(min_length=3,max_length=80,pattern=r'^[A-Za-z0-9_.-]+$')
 password:str=Field(min_length=12,max_length=128)
 role_id:str
class UserAccess(Critical):
 username:str
 roles:list[str]=Field(min_length=1,max_length=8)
 active:bool
class RoleUpdate(Critical):
 role_id:str=Field(min_length=3,max_length=60,pattern=r'^[a-z][a-z0-9_]+$')
 capabilities:list[str]=Field(max_length=40)
class SecretUpdate(Critical):
 key:str=Field(pattern=r'^[A-Z][A-Z0-9_]{2,80}$')
 value:str=Field(min_length=1,max_length=8192)
class DatasetImport(Strict):
 name:str=Field(min_length=1,max_length=120)
 csv_text:str=Field(min_length=1,max_length=2_000_000)
 date_column:str
 target_column:str
 feature_columns:list[str]=Field(min_length=1,max_length=12)
 parent_id:str|None=None
class DatasetReview(Critical): dataset_id:str
class Train(Critical):
 dataset_id:str
 recipe_id:str
class Predict(Strict):
 model_id:str
 features:dict[str,float]
class AgentUpdate(Critical):
 id:str=Field(min_length=3,max_length=60,pattern=r'^[a-z0-9_-]+$')
 name:str=Field(min_length=1,max_length=100)
 description:str=Field(max_length=1000)
 tools:list[str]=Field(max_length=15)
 enabled:bool
 revision:int=Field(ge=0)
class ServiceTest(Strict): name:str
class ModelReview(Critical):
 model_id:str
 decision:str=Field(pattern=r'^(approved|rejected)$')
 note:str=Field(min_length=5,max_length=1000)
class Finish(Critical): revision:int=Field(ge=0)

def configuration():
 with connect() as db:
  row=db.execute('SELECT * FROM workspace_config WHERE id=1').fetchone()
 return {'revision':row['revision'],'value':json.loads(row['value'])}

def workflow(user):
 with connect() as db:
  assigned={row[0] for row in db.execute('SELECT ur.role_id FROM user_roles ur JOIN users u ON u.user_id=ur.user_id WHERE u.is_active=1 AND u.is_root=0')}
  setup=db.execute('SELECT completed,completed_at FROM workspace_setup WHERE id=1').fetchone()
 config=configuration()
 roles=['platform_admin','security_admin','mlops_engineer']
 steps=[{'id':'password','label':'Cambiar contraseña temporal','complete':not user.get('must_change_password',True)},
 {'id':'administrators','label':'Asignar administración de plataforma, seguridad y modelos','complete':all(role in assigned for role in roles),'missing_roles':[role for role in roles if role not in assigned]},
 {'id':'configuration','label':'Guardar configuración de instancia','complete':config['revision']>0},
 {'id':'confirmation','label':'Confirmar la configuración inicial','complete':bool(setup['completed'])}]
 if user.get('mfa_required'):steps.insert(1,{'id':'mfa','label':'Confirmar segundo factor requerido por el rol','complete':bool(user.get('mfa_verified'))})
 return {'steps':steps,'current_step':next((s['id'] for s in steps if not s['complete']),'ready'),'completed_at':setup['completed_at']}

@router.get('/session')
def session(user=Depends(iam.get_current_user_and_session)):
 if not user.get('is_authenticated'): return {'authenticated':False,'capabilities':[],'workflow':{'current_step':'login'}}
 initialize()
 restricted=user.get('must_change_password') or user.get('mfa_setup_required') or user.get('mfa_verification_required')
 return {'authenticated':True,'user':{k:v for k,v in user.items() if k!='token'},'capabilities':[] if restricted else capabilities(user),'workflow':workflow(user)}

@router.post('/confirmations')
def confirmation(body:Confirm,user=Depends(authenticated)):
 if len(canonical(body.payload))>2_100_000: raise HTTPException(422,'Operación demasiado grande.')
 token=secrets.token_urlsafe(32)
 with connect() as db:
  db.execute('DELETE FROM workspace_confirmations WHERE expires<?',(time.time(),))
  db.execute('INSERT INTO workspace_confirmations VALUES(?,?,?,?,?)',(hashlib.sha256(token.encode()).hexdigest(),user['user_id'],body.action,digest(body.payload),time.time()+120))
 return {'confirmation_token':token,'expires_in':120}

@router.get('/configuration')
def read_config(user=Depends(require('config.read'))): return configuration()

def validate_config(value):
 if set(value)!=set(DEFAULT_CONFIG): raise HTTPException(422,'Campos de configuración no reconocidos o incompletos.')
 if not isinstance(value['display_name'],str) or not 1<=len(value['display_name'])<=100: raise HTTPException(422,'Nombre de instancia inválido.')
 for key in ['gateway_port','api_port']:
  if type(value[key]) is not int or not 1024<=value[key]<=65535: raise HTTPException(422,'Puertos entre 1024 y 65535 requeridos.')
 if value['gateway_port']==value['api_port']: raise HTTPException(422,'Los puertos de gateway y API deben ser diferentes.')
 if not isinstance(value['paths'],dict) or set(value['paths'])!=set(DEFAULT_CONFIG['paths']): raise HTTPException(422,'Declara los tres paths del espacio de trabajo.')
 for path in value['paths'].values():
  if not isinstance(path,str) or len(path)>500 or not path.strip() or '\x00' in path: raise HTTPException(422,'Path inválido.')
  resolved=(iam.PROJECT_ROOT/path).resolve()
  if not resolved.is_relative_to(iam.PROJECT_ROOT.resolve()): raise HTTPException(422,'Los paths gestionados deben permanecer dentro del proyecto.')
 if not isinstance(value['modules'],dict) or set(value['modules'])!=set(DEFAULT_CONFIG['modules']) or any(type(v) is not bool for v in value['modules'].values()): raise HTTPException(422,'Módulos no reconocidos.')
 if not isinstance(value['environment'],dict) or set(value['environment'])-SAFE_ENV or any(not isinstance(v,str) or len(v)>256 for v in value['environment'].values()): raise HTTPException(422,'Variables no permitidas; almacena credenciales en Secretos.')
 for key,minimum,maximum in [('TRAINING_MAX_ROWS',10,10000),('OMP_NUM_THREADS',1,256)]:
  if key in value['environment']:
   raw=value['environment'][key]
   if not raw.isdigit() or not minimum<=int(raw)<=maximum:raise HTTPException(422,f'{key} debe estar entre {minimum} y {maximum}.')
 if value['environment'].get('LOG_LEVEL','INFO') not in {'DEBUG','INFO','WARNING','ERROR','CRITICAL'}:raise HTTPException(422,'Nivel de registro inválido.')
 if not isinstance(value['services'],dict) or set(value['services'])!=set(SERVICE_PATHS): raise HTTPException(422,'Servicios no reconocidos.')
 for name,item in value['services'].items():
  if not isinstance(item,dict) or set(item)!={'url','enabled','secret_ref'} or type(item['enabled']) is not bool: raise HTTPException(422,'Esquema de servicio inválido.')
  if item['url']: validate_url(item['url'])
  if item['enabled'] and not item['url']: raise HTTPException(422,f'{name} necesita URL.')
  if item['secret_ref'] and (not isinstance(item['secret_ref'],str) or not item['secret_ref'].replace('_','').isalnum()): raise HTTPException(422,'Referencia de secreto inválida.')
 return value

def validate_url(value):
 if not isinstance(value,str) or len(value)>500: raise HTTPException(422,'URL inválida.')
 parsed=urlsplit(value)
 try: port=parsed.port
 except ValueError: raise HTTPException(422,'Puerto inválido.')
 if parsed.scheme not in {'http','https'} or not parsed.hostname or parsed.username or parsed.password or parsed.query or parsed.fragment: raise HTTPException(422,'URL HTTP(S) sin credenciales ni parámetros requerida.')
 if parsed.hostname in {'169.254.169.254','metadata.google.internal','metadata'}: raise HTTPException(422,'No se permiten endpoints de metadatos.')
 return parsed

@router.put('/configuration')
def save_config(body:ConfigUpdate,user=Depends(require('config.write'))):
 value=validate_config(body.value)
 consume(user,'configuration.save',body)
 with connect() as db:
  db.execute('BEGIN IMMEDIATE')
  old=db.execute('SELECT revision,value FROM workspace_config WHERE id=1').fetchone()
  if old['revision']!=body.revision: raise HTTPException(409,'Otro usuario cambió la configuración. Recarga antes de guardar.')
  db.execute('UPDATE workspace_config SET revision=revision+1,value=? WHERE id=1',(canonical(value),))
  db.execute('UPDATE workspace_setup SET completed=0,completed_at=NULL WHERE id=1')
  audit(db,user,'configuration.saved',{'revision':body.revision+1,'fields':list(value)})
 # Runtime environment allowlist is explicit; listeners never change in-process.
 for key,val in value['environment'].items(): os.environ[key]=val
 import logging
 logging.getLogger().setLevel(value['environment'].get('LOG_LEVEL','INFO'))
 return {**configuration(),'restart_required':True,'message':'Configuración deseada guardada. Los puertos y servicios externos requieren aplicar/reiniciar sus procesos; no se ha reiniciado ningún servicio.'}

@router.post('/setup/complete')
def complete_setup(body:Finish,user=Depends(require('config.write'))):
 state=workflow(user)
 if any(not step['complete'] for step in state['steps'][:-1]): raise HTTPException(409,'Completa contraseña, MFA si corresponde, administradores y configuración antes de finalizar.')
 if configuration()['revision']!=body.revision: raise HTTPException(409,'La configuración cambió; revisa la versión actual.')
 consume(user,'setup.complete',body)
 with connect() as db:
  db.execute('BEGIN IMMEDIATE')
  if db.execute('SELECT revision FROM workspace_config WHERE id=1').fetchone()[0]!=body.revision:
   raise HTTPException(409,'La configuración cambió durante la confirmación; revisa la versión actual.')
  db.execute('UPDATE workspace_setup SET completed=1,completed_at=? WHERE id=1',(now(),));audit(db,user,'setup.completed',{'revision':body.revision})
 return workflow(user)

@router.get('/identity')
def identity(user=Depends(require('iam.write'))):
 with connect() as db:
  users=[dict(row) for row in db.execute('SELECT user_id,username,email,is_active,is_root,must_change_password FROM users ORDER BY username')]
  for item in users: item['roles']=[r[0] for r in db.execute('SELECT role_id FROM user_roles WHERE user_id=?',(item['user_id'],))]
  roles=[{'role_id':r['role_id'],'capabilities':json.loads(r['capabilities'])} for r in db.execute('SELECT * FROM workspace_roles')]
 assignable=[];manageable=[]
 for role in roles:
  try:
   check_delegation(user,[role['role_id']])
   if role['role_id']!='root':assignable.append(role['role_id'])
  except HTTPException:pass
 for item in users:
  try:
   check_delegation(user,item['roles'])
   if not item['is_root'] and item['user_id']!=user['user_id']:manageable.append(item['username'])
  except HTTPException:pass
 return {'users':users,'roles':roles,'capabilities':CAPABILITIES,'assignable_roles':assignable,'manageable_users':manageable}

@router.post('/identity/users')
def create_user(body:UserCreate,user=Depends(require('iam.write'))):
 ok,errors=PasswordPolicy.validate_complexity(body.password)
 if not ok: raise HTTPException(422,' '.join(errors))
 if body.role_id=='root': raise HTTPException(403,'No se crean cuentas root desde este formulario.')
 with connect() as db:
  if not db.execute('SELECT 1 FROM workspace_roles WHERE role_id=?',(body.role_id,)).fetchone(): raise HTTPException(422,'Rol no reconocido.')
 check_delegation(user,[body.role_id])
 consume(user,'identity.create',body)
 hashed,salt=AuthenticationEngine.hash_password(body.password);ident=str(uuid.uuid4());stamp=now()
 try:
  with connect() as db:
   db.execute('BEGIN IMMEDIATE')
   db.execute('INSERT INTO users(user_id,username,email,password_hash,salt,is_active,is_root,must_change_password,mfa_enabled,failed_attempts,created_at,updated_at) VALUES(?,?,?,?,?,1,0,1,0,0,?,?)',(ident,body.username,body.username+'@portops.local',hashed,salt,stamp,stamp))
   db.execute('INSERT INTO user_roles VALUES(?,?,?,?)',(ident,body.role_id,user['user_id'],stamp));audit(db,user,'identity.created',{'username':body.username,'role':body.role_id})
 except sqlite3.IntegrityError: raise HTTPException(409,'La cuenta ya existe o el rol no está disponible en IAM.')
 return {'username':body.username,'must_change_password':True}

@router.put('/identity/users')
def access(body:UserAccess,user=Depends(require('iam.write'))):
 with connect() as db:
  target=db.execute('SELECT user_id,is_root FROM users WHERE username=?',(body.username,)).fetchone()
  if not target: raise HTTPException(404,'Cuenta no encontrada.')
  if target['is_root'] or 'root' in body.roles: raise HTTPException(403,'El root canónico no se modifica ni se asigna desde este formulario.')
  if target['user_id']==user['user_id']: raise HTTPException(403,'No puedes modificar tu propio acceso desde este formulario.')
  known={r[0] for r in db.execute('SELECT role_id FROM workspace_roles')}
  if set(body.roles)-known: raise HTTPException(422,'Roles no reconocidos.')
 with connect() as db:current_roles=[r[0] for r in db.execute('SELECT role_id FROM user_roles WHERE user_id=?',(target['user_id'],))]
 check_delegation(user,current_roles)
 check_delegation(user,body.roles)
 consume(user,'identity.access',body)
 with connect() as db:
  db.execute('BEGIN IMMEDIATE');db.execute('DELETE FROM user_roles WHERE user_id=?',(target['user_id'],))
  for role in set(body.roles):db.execute('INSERT INTO user_roles VALUES(?,?,?,?)',(target['user_id'],role,user['user_id'],now()))
  db.execute('UPDATE users SET is_active=?,updated_at=? WHERE user_id=?',(int(body.active),now(),target['user_id']))
  db.execute('UPDATE sessions SET is_revoked=1 WHERE user_id=?',(target['user_id'],))
  db.execute('UPDATE workspace_setup SET completed=0,completed_at=NULL WHERE id=1')
  audit(db,user,'identity.access.changed',{'username':body.username,'roles':body.roles,'active':body.active})
 return {'saved':True,'sessions_revoked':True}

@router.put('/identity/roles')
def role(body:RoleUpdate,user=Depends(require('iam.write'))):
 if body.role_id=='root' or set(body.capabilities)-set(CAPABILITIES): raise HTTPException(422,'Root es inmutable y sólo se admiten capacidades del catálogo.')
 # Only root may delegate a capability beyond the caller's own access.
 if not user.get('is_root') and set(body.capabilities)-set(capabilities(user)): raise HTTPException(403,'No puedes delegar capacidades que no tienes.')
 check_delegation(user,[body.role_id])
 if not user.get('is_root') and body.role_id in user.get('roles',[]):raise HTTPException(403,'No puedes modificar un rol asignado a tu propia cuenta.')
 consume(user,'identity.role',body)
 with connect() as db:
  db.execute('BEGIN IMMEDIATE')
  db.execute('INSERT OR IGNORE INTO roles(role_id,role_name,tier,is_assignable,requires_mfa,description) VALUES(?,?,?,1,0,?)',(body.role_id,body.role_id,'custom','Rol gestionado desde el espacio de trabajo'))
  db.execute('INSERT INTO workspace_roles VALUES(?,?) ON CONFLICT(role_id) DO UPDATE SET capabilities=excluded.capabilities',(body.role_id,canonical(sorted(set(body.capabilities)))))
  db.execute('UPDATE sessions SET is_revoked=1 WHERE user_id IN (SELECT user_id FROM user_roles WHERE role_id=?)',(body.role_id,))
  audit(db,user,'identity.role.changed',{'role_id':body.role_id,'capabilities':body.capabilities})
 return {'saved':True,'sessions_revoked':True}

@router.get('/secrets')
def inventory(user=Depends(require('secrets.write'))):
 return {'items':[{'key':key,'configured':bool(SecretManager.get_secret(key)),'masked':'********' if SecretManager.get_secret(key) else ''} for key in sorted(set(SecretManager._SYSTEM_KEYS+SecretManager._LLM_KEYS+['WAZUH_API_TOKEN','MINIO_ACCESS_KEY','MINIO_SECRET_KEY','WAZUH_USERNAME','WAZUH_PASSWORD']))],
 'storage':'Fernet authenticated encryption; protect the vault key with OS permissions or PORTOPS_VAULT_KEY. Values are never returned.'}

@router.put('/secrets')
def write_secret(body:SecretUpdate,user=Depends(require('secrets.write'))):
 allowed=set(SecretManager._SYSTEM_KEYS+SecretManager._LLM_KEYS+['WAZUH_API_TOKEN','MINIO_ACCESS_KEY','MINIO_SECRET_KEY','WAZUH_USERNAME','WAZUH_PASSWORD'])
 if body.key not in allowed: raise HTTPException(422,'Clave no admitida en el catálogo.')
 consume(user,'secret.rotate',body)
 SecretManager.set_secret(body.key,body.value)
 with connect() as db:audit(db,user,'secret.rotated',{'key':body.key})
 return {'key':body.key,'configured':True,'message':'Valor guardado en bóveda y aplicado al proceso API. Otros procesos deben recargar su configuración.'}

@router.post('/services/test')
def test_service(body:ServiceTest,user=Depends(require('services.write'))):
 if body.name not in SERVICE_PATHS: raise HTTPException(422,'Servicio no reconocido.')
 config=configuration()['value']['services'][body.name]
 if not config['url']: return {'status':'unconfigured','reachable':False,'message':'Guarda la URL del servicio antes de probar.'}
 parsed=validate_url(config['url'])
 try:
  addresses=socket.getaddrinfo(parsed.hostname,parsed.port or (443 if parsed.scheme=='https' else 80))
  if any(ipaddress.ip_address(item[4][0]).is_link_local or ipaddress.ip_address(item[4][0]).is_multicast or ipaddress.ip_address(item[4][0]).is_unspecified for item in addresses): raise HTTPException(422,'Destino de red no permitido.')
  headers={}
  if config['secret_ref']:
   key=SecretManager.get_secret(config['secret_ref'])
   if key: headers['Authorization']='Bearer '+key
  with httpx.Client(timeout=5,follow_redirects=False,trust_env=False) as client:
   if body.name=='wazuh' and not headers:
    username=SecretManager.get_secret('WAZUH_USERNAME')
    password=SecretManager.get_secret('WAZUH_PASSWORD')
    if username and password:
     authentication=client.post(config['url'].rstrip('/')+'/security/user/authenticate',auth=(username,password))
     if authentication.is_success:
      token=authentication.json().get('data',{}).get('token')
      if token:headers['Authorization']='Bearer '+token
   response=client.get(config['url'].rstrip('/')+SERVICE_PATHS[body.name],headers=headers)
  result={'reachable':True,'status':'ready' if 200<=response.status_code<300 else 'authentication_required' if response.status_code in [401,403] else 'http_error','http_status':response.status_code,'message':'Respuesta HTTP real del endpoint configurado; no confirma ingesta ni despliegue de agentes.'}
 except (httpx.HTTPError,OSError,ValueError,TypeError,AttributeError): result={'reachable':False,'status':'unreachable','message':'No se pudo verificar el servicio. Revisa URL, TLS, credenciales y proceso del servicio.'}
 with connect() as db:audit(db,user,'service.tested',{'service':body.name,'result':result['status']})
 return result

@router.get('/datasets')
def datasets(user=Depends(require('datasets.read'))):
 items=service().list_datasets()
 with connect() as db: parents={r['id']:r['parent_id'] for r in db.execute('SELECT * FROM workspace_dataset_versions')}
 for item in items:item['parent_id']=parents.get(item['id'])
 return {'items':items}

@router.get('/datasets/{dataset_id}')
def dataset_content(dataset_id:str,user=Depends(require('datasets.read'))):
 import csv,io
 with connect() as db:row=db.execute('SELECT * FROM fw_datasets WHERE id=?',(dataset_id,)).fetchone()
 if not row:raise HTTPException(404,'Dataset no encontrado.')
 columns=[row['date_column'],row['target_column'],*json.loads(row['features_json'])]
 buffer=io.StringIO();writer=csv.DictWriter(buffer,fieldnames=columns);writer.writeheader();writer.writerows(json.loads(row['rows_json']))
 return {'id':dataset_id,'name':row['name'],'csv_text':buffer.getvalue(),'date_column':row['date_column'],'target_column':row['target_column'],'feature_columns':json.loads(row['features_json'])}


@router.post('/datasets')
def import_data(body:DatasetImport,user=Depends(require('datasets.write'))):
 if not configuration()['value']['modules']['datasets']: raise HTTPException(409,'El módulo datasets está deshabilitado.')
 if body.parent_id:
  if not any(item['id']==body.parent_id for item in service().list_datasets()): raise HTTPException(404,'Dataset padre no encontrado.')
 try: result=service().import_csv(body.name,body.csv_text,body.date_column,body.target_column,body.feature_columns)
 except ValueError as error: raise HTTPException(422,str(error))
 with connect() as db:
  db.execute('INSERT INTO workspace_dataset_versions VALUES(?,?)',(result['id'],body.parent_id))
  audit(db,user,'dataset.imported',{'id':result['id'],'parent_id':body.parent_id,'name':body.name})
 return result

@router.post('/datasets/review')
def review(body:DatasetReview,user=Depends(require('datasets.review'))):
 consume(user,'dataset.review',body)
 try: result=service().review(body.dataset_id,user['user_id'])
 except ValueError as error: raise HTTPException(404,str(error))
 with connect() as db:audit(db,user,'dataset.reviewed',{'id':body.dataset_id})
 return result

@router.get('/models')
def models(user=Depends(require('models.read'))):
 items=service().models()
 with connect() as db:reviews={row['model_id']:dict(row) for row in db.execute('SELECT * FROM workspace_model_reviews')}
 for item in items:item['review']=reviews.get(item['id'])
 return {'items':items,'recipes':service().recipes()}

@router.post('/models/review')
def review_model(body:ModelReview,user=Depends(require('models.review'))):
 try:service().artifact(body.model_id)
 except ValueError as error:raise HTTPException(404,str(error))
 with connect() as db:
  run=db.execute('SELECT r.actor FROM fw_models m JOIN fw_training_runs r ON r.id=m.run_id WHERE m.id=?',(body.model_id,)).fetchone()
 if run and run[0]==user['user_id']:raise HTTPException(403,'El autor del entrenamiento no puede aprobar su propio modelo.')
 consume(user,'model.review',body)
 with connect() as db:
  db.execute('INSERT INTO workspace_model_reviews VALUES(?,?,?,?,?) ON CONFLICT(model_id) DO UPDATE SET decision=excluded.decision,actor=excluded.actor,created_at=excluded.created_at,note=excluded.note',(body.model_id,body.decision,user['user_id'],now(),body.note))
  audit(db,user,'model.reviewed',{'model_id':body.model_id,'decision':body.decision,'note':body.note})
 return {'saved':True,'decision':body.decision,'scope':'local_review_only'}

@router.get('/services')
def services(user=Depends(require('services.write'))):
 return {'items':configuration()['value']['services']}

@router.post('/models/train')
def train(body:Train,user=Depends(require('models.train'))):
 if not configuration()['value']['modules']['training']: raise HTTPException(409,'El módulo entrenamiento está deshabilitado.')
 consume(user,'model.train',body)
 try:result=service().train(body.dataset_id,body.recipe_id,user['user_id'])
 except ValueError as error:raise HTTPException(422,str(error))
 with connect() as db:audit(db,user,'model.trained',{'run_id':result['id'],'model_id':result['model_id'],'dataset_id':body.dataset_id,'artifact_sha256':result['artifact_sha256']})
 return result

@router.get('/models/{model_id}/artifact')
def artifact(model_id:str,user=Depends(require('models.read'))):
 try:return service().artifact(model_id)
 except ValueError as error:raise HTTPException(404,str(error))

@router.post('/models/predict')
def predict(body:Predict,user=Depends(require('models.predict'))):
 try:return service().predict(body.model_id,body.features)
 except (ValueError,KeyError) as error:raise HTTPException(422,str(error))

@router.get('/agents')
def agents(user=Depends(require('workspace.read'))):
 with connect() as db:
  items=[{**dict(r),'tools':json.loads(r['tools']),'enabled':bool(r['enabled'])} for r in db.execute('SELECT * FROM workspace_agents')]
 return {'items':items,'tool_catalog':[tool for tool in get_available_tools_schema() if tool['name'] in EXECUTABLE_TOOLS],'notice':'Los perfiles controlan herramientas locales; guardar no despliega un agente externo.'}

@router.put('/agents')
def agent(body:AgentUpdate,user=Depends(require('agents.write'))):
 known=EXECUTABLE_TOOLS
 if set(body.tools)-known:raise HTTPException(422,'Herramienta no incluida en el catálogo permitido.')
 consume(user,'agent.save',body)
 with connect() as db:
  db.execute('BEGIN IMMEDIATE');old=db.execute('SELECT revision FROM workspace_agents WHERE id=?',(body.id,)).fetchone()
  if (old['revision'] if old else 0)!=body.revision:raise HTTPException(409,'El agente cambió; recarga antes de guardar.')
  db.execute('INSERT INTO workspace_agents VALUES(?,?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET name=excluded.name,description=excluded.description,tools=excluded.tools,enabled=excluded.enabled,revision=excluded.revision',(body.id,body.name,body.description,canonical(body.tools),int(body.enabled),body.revision+1))
  audit(db,user,'agent.saved',{'id':body.id,'tools':body.tools,'enabled':body.enabled})
 return {'saved':True,'revision':body.revision+1}

@router.get('/security')
def security(user=Depends(require('audit.read'))):
 with connect() as db:
  rows=[dict(r) for r in db.execute('SELECT * FROM workspace_audit ORDER BY id')]
  sessions=[dict(r) for r in db.execute('SELECT session_id,user_id,expires_at,is_revoked,last_activity_at FROM sessions ORDER BY last_activity_at DESC LIMIT 50')]
 prev='0'*64;valid=True;first_bad=None
 for row in rows:
  expected=hashlib.sha256(canonical([prev,row['actor'],row['action'],row['payload'],row['created_at']]).encode()).hexdigest()
  if row['prev_hash']!=prev or row['block_hash']!=expected:valid=False;first_bad=row['id'];break
  prev=row['block_hash']
 try:
  from src.serving import api
  verified=api.audit_manager.verify_worm_chain()
  operational={key:verified[key] for key in ['valid','tampering_detected','verified_blocks','failed_block_id','last_hash'] if key in verified}
  operational['status']='verified' if verified.get('valid') else 'integrity_failure'
 except Exception:
  operational={'status':'not_verified','message':'El registro operativo no pudo verificarse. Revise el almacenamiento y su configuración.'}
 return {'chain':{'valid':valid,'verified_blocks':len(rows) if valid else first_bad-1,'first_bad_block':first_bad,'head':prev},
 'events':rows[-100:][::-1],'sessions':sessions,'operational_chain':operational,
 'meaning':{'security':'Estado comprobado de sesiones, controles y conectores.','iam':'Identidades, roles y capacidades aplicadas por el servidor.','worm':'Eventos append-only con hashes encadenados y verificación; el administrador del archivo aún puede manipular almacenamiento. No equivale a retención WORM certificada.'}}


class AgentRun(Critical):
 agent_id:str
 tool:str
 arguments:dict

@router.post('/agents/run')
def run_agent(body:AgentRun,user=Depends(require('agents.write'))):
 if not configuration()['value']['modules']['agents']:raise HTTPException(409,'El módulo agentes está deshabilitado.')
 with connect() as db:profile=db.execute('SELECT * FROM workspace_agents WHERE id=?',(body.agent_id,)).fetchone()
 if not profile or not profile['enabled']:raise HTTPException(409,'Agente no encontrado o deshabilitado.')
 if body.tool not in EXECUTABLE_TOOLS or body.tool not in json.loads(profile['tools']):raise HTTPException(403,'El perfil no permite esa herramienta.')
 tool=next(t for t in get_available_tools_schema() if t['name']==body.tool)
 import jsonschema
 try:jsonschema.validate(body.arguments,tool['inputSchema'])
 except jsonschema.ValidationError:raise HTTPException(422,'Los argumentos no coinciden con el esquema de la herramienta.')
 consume(user,'agent.run',body)
 from src.serving import api
 try:
  if body.tool=='get_port_forecast':
   from pydantic import ValidationError
   request=api.PredictionRequest(port=body.arguments['port_name'],horizon_months=body.arguments.get('horizon_months',3))
   result=api.predict_container_throughput(request).model_dump()
  elif body.tool=='query_maritime_knowledge':
   query=body.arguments['query']
   if not isinstance(query,str) or not 1<=len(query)<=1000:raise HTTPException(422,'Consulta entre 1 y 1000 caracteres requerida.')
   result=api.rag_engine.query(query,top_k=max(1,min(5,int(body.arguments.get('top_k',3)))))
  elif body.tool=='validate_iso6346_container':
   from src.data.parsers.container_iso6346 import ISO6346ContainerValidator
   result=ISO6346ContainerValidator.parse_full_manifest_entry(container_id=body.arguments['container_id'],size_type=body.arguments.get('size_type','45G1'))
  else:
   cif=float(body.arguments.get('cif_value_usd',0))
   if not 0<cif<=1e12:raise HTTPException(422,'Valor CIF positivo y acotado requerido.')
   result=api.PanamaTariffDatabase.calculate_landed_customs_cost(hs_code=body.arguments['hs_code'],cif_value_usd=cif)
 except (ValueError,KeyError,TypeError) as error:raise HTTPException(422,'Argumentos inválidos para la herramienta.') from error
 with connect() as db:audit(db,user,'agent.executed',{'agent_id':body.agent_id,'tool':body.tool})
 return {'tool':body.tool,'result':result,'source':'local_backend'}

class Modules(Critical):
 revision:int
 modules:dict[str,bool]

@router.put('/modules')
def save_modules(body:Modules,user=Depends(require('modules.write'))):
 if set(body.modules)!=set(DEFAULT_CONFIG['modules']):raise HTTPException(422,'Módulos no reconocidos.')
 consume(user,'modules.save',body)
 with connect() as db:
  db.execute('BEGIN IMMEDIATE');row=db.execute('SELECT * FROM workspace_config WHERE id=1').fetchone()
  if row['revision']!=body.revision:raise HTTPException(409,'La configuración cambió. Recarga.')
  config=json.loads(row['value']);config['modules']=body.modules
  db.execute('UPDATE workspace_config SET revision=revision+1,value=? WHERE id=1',(canonical(config),))
  audit(db,user,'modules.changed',{'modules':body.modules})
 return configuration()

@router.get('/modules')
def module_settings(user=Depends(require('modules.write'))):
 config=configuration()
 return {'revision':config['revision'],'value':{'modules':config['value']['modules']}}
