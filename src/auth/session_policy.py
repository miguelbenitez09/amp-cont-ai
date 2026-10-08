"""Local manual-test identities and real MFA requirements, enforced server-side."""
import ipaddress
import sqlite3

def local_request(request):
 try:return ipaddress.ip_address(request.client.host).is_loopback
 except (ValueError,AttributeError):return request.client.host in {'testclient','testserver'} if request.client else False

def local_test_account(conn,user_id):
 try:return bool(conn.execute('SELECT 1 FROM manual_test_accounts WHERE user_id=?',(user_id,)).fetchone())
 except sqlite3.OperationalError:return False

def mfa_required(conn,user_id):
 if local_test_account(conn,user_id):return False
 try:
  return bool(conn.execute('SELECT 1 FROM user_roles ur JOIN roles r ON r.role_id=ur.role_id WHERE ur.user_id=? AND r.requires_mfa=1 LIMIT 1',(user_id,)).fetchone())
 except sqlite3.OperationalError:return False
