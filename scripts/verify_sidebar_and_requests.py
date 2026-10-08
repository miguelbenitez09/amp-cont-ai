"""Live regressions for sidebar, expired sessions and request recovery."""
import json
from pathlib import Path
from playwright.sync_api import sync_playwright
out=Path('reports/sidebar-requests-2026-10-08');out.mkdir(parents=True,exist_ok=True)
results=[]
with sync_playwright() as p:
 b=p.chromium.launch()
 for width in [390,1440]:
  context=b.new_context(viewport={'width':width,'height':900})
  context.add_cookies([{'name':'portops_session','value':'expired-test-cookie','url':'http://127.0.0.1:8000'}])
  page=context.new_page();errors=[];failed=[]
  page.on('pageerror',lambda e:errors.append(str(e)))
  page.on('response',lambda r:failed.append({'url':r.url,'status':r.status}) if r.status>=400 and '/api/' in r.url else None)
  page.goto('http://127.0.0.1:8000/app');page.wait_for_timeout(1500)
  assert not any(c['name']=='portops_session' for c in context.cookies()), 'Expired cookie persisted'
  if width>800:
   page.locator('#sidebar-toggle').click()
   assert page.locator('body').evaluate('e=>e.classList.contains("ops-sidebar-collapsed")')
   page.reload();page.wait_for_timeout(700)
   assert page.locator('body').evaluate('e=>e.classList.contains("ops-sidebar-collapsed")')
   page.keyboard.press('Control+Shift+S')
   assert not page.locator('body').evaluate('e=>e.classList.contains("ops-sidebar-collapsed")')
  else:
   page.keyboard.press('Control+Shift+S')
   assert page.locator('#workspace-navigation-toggle').get_attribute('aria-expanded')=='true'
  tabs=page.locator('.tabs-nav > .tab-btn').evaluate_all('bs=>bs.map(b=>b.dataset.tab)')
  def select(tab):
   toggle=page.locator('#workspace-navigation-toggle')
   if toggle.is_visible() and toggle.get_attribute('aria-expanded')=='false':toggle.click()
   page.locator(f'.tabs-nav > [data-tab="{tab}"]').click()
  for tab in tabs:select(tab);page.wait_for_timeout(300)
  select('tab-simulation')
  page.route('**/api/simulation/run',lambda r:r.fulfill(status=503,content_type='application/json',body='{"detail":"Motor temporalmente no disponible"}'))
  page.locator('#btn-simulate').click()
  page.locator('#simulation-request-status[data-state="error"]').wait_for()
  assert page.locator('#btn-simulate').is_enabled()
  page.unroute('**/api/simulation/run')
  page.locator('#btn-simulate').click()
  page.locator('#simulation-request-status[data-state="success"]').wait_for(timeout=65000)
  assert page.locator('#simChart').evaluate('e=>!!window.Chart.getChart(e)')
  assert page.locator('#sim-run-status-badge').inner_text().startswith('Bloque WORM #')
  page.screenshot(path=str(out/f'simulation-{width}.png'))
  select('tab-forecast');page.locator('#btn-predict').click();page.wait_for_timeout(2500)
  page.screenshot(path=str(out/f'forecast-{width}.png'))
  if width>800:
   page.locator('#sidebar-toggle').click()
   assert page.locator('.tabs-nav .tab-btn > span').first.evaluate('e=>e.getBoundingClientRect().width')<=1
   page.evaluate('window.scrollTo(0,0)')
   page.screenshot(path=str(out/'sidebar-collapsed.png'))
  results.append({'width':width,'pageErrors':errors,'apiFailures':failed})
  assert not errors,errors
  context.close()
 b.close()
(out/'verification.json').write_text(json.dumps(results,indent=2),encoding='utf-8')
print(json.dumps(results,indent=2))
