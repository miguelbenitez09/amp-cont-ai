"""Read-only UI traversal using the explicitly prepared local manual accounts."""
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from playwright.sync_api import sync_playwright
from scripts.prepare_manual_role_accounts import ACCOUNTS
from src.serving.workspace_router import DEFAULT_ROLES

def main():
 password=(ROOT/'.bootstrap/manual-role-credentials.txt').read_text(encoding='utf-8').split('Password: ',1)[1].splitlines()[0]
 out=ROOT/'reports/roles-2026-10-08';out.mkdir(parents=True,exist_ok=True)
 results=[]
 expected_caps={'overview':'workspace.read','configuration':'config.write','services':'services.write','modules':'modules.write','identity':'iam.write',
  'datasets':'datasets.read','models':'models.read','agents':'workspace.read','secrets':'secrets.write','security':'audit.read'}
 with sync_playwright() as p:
  browser=p.chromium.launch()
  for name,role in ACCOUNTS.items():
   context=browser.new_context(viewport={'width':1440,'height':960});page=context.new_page();errors=[]
   page.on('pageerror',lambda error:errors.append(str(error)))
   page.goto('http://127.0.0.1:8000/static/workspace/')
   page.locator('#login-form [name=username]').fill(name)
   page.locator('#login-form [name=password]').fill(password)
   page.locator('#login-form button').click()
   page.locator('[data-route=overview]').wait_for()
   page.locator('main[aria-busy]').wait_for(state='detached')
   caps=DEFAULT_ROLES[role]
   expected=[route for route,cap in expected_caps.items() if cap in caps]
   observed=page.locator('#management-nav button').evaluate_all('(buttons)=>buttons.map(b=>b.dataset.route)')
   assert observed==expected,(name,observed)
   assert 'prueba local' in page.locator('#management-identity').inner_text()
   page.screenshot(path=str(out/(name+'-workspace.png')))
   for route in expected:
    page.locator(f'[data-route={route}]').click()
    page.locator('main[aria-busy]').wait_for(state='detached')
    assert not page.locator('#retry-view').count(),(name,route)
    if route=='models':assert bool(page.locator('#training-form').count())==('models.train' in caps)
    if route=='datasets':assert bool(page.locator('#dataset-form').count())==('datasets.write' in caps)
   page.locator('#management-logout').click()
   page.locator('#login-form').wait_for()
   assert not errors,(name,errors)
   results.append({'username':name,'role':role,'navigation':observed,'screens_verified':len(expected),'javascript_errors':errors,'logout':'passed'})
   context.close()
  browser.close()
 (out/'live-browser-matrix.json').write_text(json.dumps(results,indent=2),encoding='utf-8')
 print(json.dumps({'accounts':len(results),'screens_verified':sum(result['screens_verified'] for result in results),'javascript_errors':sum(len(result['javascript_errors']) for result in results)},indent=2))

if __name__=='__main__':main()
