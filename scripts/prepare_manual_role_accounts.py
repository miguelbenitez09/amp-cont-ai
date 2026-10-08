"""Explicitly provision local-only manual test identities, never production defaults.

Requires --apply and PORTOPS_MANUAL_TEST_PASSWORD. Existing unrelated accounts
are preserved. The original identity database is backed up outside static files.
"""
import argparse
from datetime import datetime, timezone
import os
from pathlib import Path
import sqlite3
import sys
import uuid

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from src.serving import workspace_router as workspace, v1_router as iam
from src.auth.authentication import AuthenticationEngine
from src.auth.password_policy import PasswordPolicy

ACCOUNTS={'root':'root','plataforma':'platform_admin','seguridad':'security_admin',
 'datos':'data_engineer','custodio':'data_steward','mlops':'mlops_engineer','revisor':'ml_reviewer',
 'operador':'port_operator','simulacion':'simulation_analyst','auditor':'compliance_auditor',
 'api':'api_consumer','lector':'readonly_viewer'}

def prepare(password,database=None,private_dir=None):
 if database is not None:iam.DB_PATH=Path(database)
 valid,errors=PasswordPolicy.validate_complexity(password)
 if not valid:raise ValueError(' '.join(errors))
 backup_dir=Path(private_dir) if private_dir else ROOT/'.bootstrap';backup_dir.mkdir(parents=True,exist_ok=True)
 backup=backup_dir/('before-manual-roles-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%f')+'.sqlite3')
 with sqlite3.connect(iam.DB_PATH) as source,sqlite3.connect(backup) as destination:source.backup(destination)
 workspace.initialize()
 stamp=workspace.now();actor={'user_id':'local-manual-provisioner'}
 with workspace.connect() as db:
  db.execute('BEGIN IMMEDIATE')
  db.execute('CREATE TABLE IF NOT EXISTS manual_test_accounts(user_id TEXT PRIMARY KEY,created_at TEXT NOT NULL)')
  columns={r[1] for r in db.execute('PRAGMA table_info(password_history)')}
  if 'salt' not in columns:db.execute('ALTER TABLE password_history ADD COLUMN salt TEXT')
  for username,role in ACCOUNTS.items():
   existing=db.execute('SELECT * FROM users WHERE username=?',(username,)).fetchone()
   if existing and username!='root' and not db.execute('SELECT 1 FROM manual_test_accounts WHERE user_id=?',(existing['user_id'],)).fetchone():
    raise ValueError(f'{username} ya existe como cuenta ajena a las pruebas; no se sobrescribirá.')
   if existing and existing['mfa_enabled']:raise ValueError(f'{username} tiene MFA activo; no se retira un factor existente.')
   hashed,salt=AuthenticationEngine.hash_password(password)
   uid=existing['user_id'] if existing else str(uuid.uuid4())
   if existing:
    db.execute('INSERT INTO password_history(user_id,password_hash,salt,created_at) VALUES(?,?,?,?)',(uid,existing['password_hash'],existing['salt'],stamp))
    db.execute('UPDATE users SET password_hash=?,salt=?,must_change_password=0,is_active=1,failed_attempts=0,locked_until=NULL,updated_at=? WHERE user_id=?',(hashed,salt,stamp,uid))
   else:
    db.execute('INSERT INTO users(user_id,username,email,password_hash,salt,is_root,must_change_password,created_at,updated_at) VALUES(?,?,?,?,?,?,0,?,?)',(uid,username,username+'@manual.local',hashed,salt,int(username=='root'),stamp,stamp))
   db.execute('DELETE FROM user_roles WHERE user_id=?',(uid,))
   db.execute('INSERT INTO user_roles VALUES(?,?,?,?)',(uid,role,actor['user_id'],stamp))
   db.execute('INSERT OR REPLACE INTO manual_test_accounts VALUES(?,?)',(uid,stamp))
   db.execute('UPDATE sessions SET is_revoked=1 WHERE user_id=?',(uid,))
   workspace.audit(db,actor,'manual_test_account.prepared',{'username':username,'role':role,'local_only':True})
  config=db.execute('SELECT * FROM workspace_config WHERE id=1').fetchone()
  import json
  workspace.validate_config(json.loads(config['value']))
  if config['revision']==0:db.execute('UPDATE workspace_config SET revision=1 WHERE id=1')
  db.execute('UPDATE workspace_setup SET completed=1,completed_at=? WHERE id=1',(stamp,))
  workspace.audit(db,actor,'manual_test_setup.confirmed',{'configuration_revision':max(1,config['revision']),'external_services_verified':False})
 # Bootstrap documentation is private and explicitly reflects the reset requested by the operator.
 credentials=backup_dir/'manual-role-credentials.txt'
 credentials.write_text('LOCAL MANUAL TEST ACCOUNTS\nURL: http://127.0.0.1:8000/static/workspace/\nPassword: '+password+'\n'+'\n'.join(name+' : '+role for name,role in ACCOUNTS.items())+'\n',encoding='utf-8')
 os.chmod(credentials,0o600)
 root_credentials=backup_dir/'root-credentials.txt'
 root_credentials.write_text('LOCAL MANUAL TEST ACCOUNT\nUsername: root\nDefault Pass:  '+password+'\nLocal-only: true\n',encoding='utf-8')
 os.chmod(root_credentials,0o600)
 return {'accounts':ACCOUNTS,'local_only':True,'backup_created':True}

def main():
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--apply',action='store_true');args=parser.parse_args()
 if not args.apply:raise SystemExit('Use --apply para el cambio solicitado explícitamente.')
 password=os.environ.get('PORTOPS_MANUAL_TEST_PASSWORD','')
 if not password:raise SystemExit('Defina PORTOPS_MANUAL_TEST_PASSWORD sin incluirlo en argumentos de procesos.')
 import json
 print(json.dumps(prepare(password),indent=2))

if __name__=='__main__':main()
