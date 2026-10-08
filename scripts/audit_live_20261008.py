"""Read-only runtime evidence for the local operational UI."""
import json
from pathlib import Path
import requests
from playwright.sync_api import sync_playwright

OUT = Path('reports/audit-2026-10-08')
OUT.mkdir(parents=True, exist_ok=True)
evidence = {'http': [], 'ui': []}
for path in ['/app', '/health/ready', '/api/admin/governance', '/api/v1/infra/config', '/api/config', '/api/v1/gateway/status']:
    r = requests.get('http://127.0.0.1:8000' + path, timeout=15)
    evidence['http'].append({'path': path, 'status': r.status_code, 'headers': dict(r.headers)})
for origin in ['http://localhost:8000.evil.example', 'http://127.0.0.1:8000.evil.example', 'https://example.com']:
    r = requests.options('http://127.0.0.1:8000/api/config', headers={'Origin': origin, 'Access-Control-Request-Method': 'POST'}, timeout=15)
    evidence['http'].append({'origin': origin, 'status': r.status_code, 'allow_origin': r.headers.get('Access-Control-Allow-Origin'), 'allow_credentials': r.headers.get('Access-Control-Allow-Credentials')})
    r = requests.get('http://127.0.0.1:8000/api/admin/governance', headers={'Origin': origin}, timeout=15)
    evidence['http'].append({'method':'GET','origin':origin,'status':r.status_code,'allow_origin':r.headers.get('Access-Control-Allow-Origin'),'allow_credentials':r.headers.get('Access-Control-Allow-Credentials')})
with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    for width, height in [(390,844),(768,1024),(1440,900)]:
        page = browser.new_page(viewport={'width':width,'height':height})
        errors, failures = [], []
        page.on('pageerror', lambda e: errors.append(str(e)))
        page.on('response', lambda r: failures.append({'url':r.url,'status':r.status}) if r.status >= 400 else None)
        page.goto('http://127.0.0.1:8000/app', wait_until='domcontentloaded', timeout=30000)
        page.wait_for_timeout(4000)
        result = page.evaluate('''() => ({overflow:document.documentElement.scrollWidth>innerWidth, scrollWidth:document.documentElement.scrollWidth, width:innerWidth, unnamedButtons:[...document.querySelectorAll('button')].filter(e=>e.getClientRects().length&&!e.innerText.trim()&&!e.getAttribute('aria-label')&&!e.getAttribute('title')).map(e=>e.id||e.outerHTML.slice(0,150)), unlabelledInputs:[...document.querySelectorAll('input,select,textarea')].filter(e=>e.getClientRects().length&&!e.getAttribute('aria-label')&&!e.getAttribute('aria-labelledby')&&!e.labels?.length).map(e=>({id:e.id,type:e.type})), visibleDialogs:[...document.querySelectorAll('[id*=modal]')].filter(e=>e.getClientRects().length).map(e=>({id:e.id,role:e.getAttribute('role'),ariaModal:e.getAttribute('aria-modal')}))})''')
        result.update({'viewport':[width,height], 'errors':errors, 'httpFailures':failures})
        page.locator('#btn-auth-iam').click()
        page.wait_for_timeout(200)
        result['authModal'] = page.evaluate('''() => {const m=document.querySelector('#auth-iam-modal');return {role:m.getAttribute('role'),ariaModal:m.getAttribute('aria-modal'),focusInside:m.contains(document.activeElement),focusedId:document.activeElement.id}}''')
        page.keyboard.press('Escape')
        result['authModal']['escapeCloses'] = not page.locator('#auth-iam-modal').is_visible()
        page.evaluate('window.closeAuthModal()')
        if page.locator('#workspace-navigation-toggle').is_visible():
            page.locator('#workspace-navigation-toggle').click()
        page.locator('#tab-btn-customs').click()
        page.locator('#btn-calc-customs').click()
        result['emptyCalculator'] = page.locator('#customs-calc-results').inner_text()
        page.locator('#calc-hs-code').fill('2710.19.21.00.00')
        page.locator('#calc-cif-usd').fill('10000')
        page.locator('#btn-calc-customs').click()
        page.wait_for_timeout(1500)
        result['calculator'] = page.locator('#customs-calc-results').inner_text()
        page.locator('#btn-validate-container').click()
        result['emptyContainer'] = page.locator('#container-validation-results').inner_text()
        result['customsLayout'] = page.evaluate('''() => ({width:innerWidth,documentWidth:document.documentElement.scrollWidth,bodyWidth:document.body.scrollWidth,height:document.documentElement.scrollHeight,overflows:[...document.querySelectorAll('body *')].filter(e=>e.getClientRects().length&&e.getBoundingClientRect().right>innerWidth+1).slice(0,12).map(e=>({id:e.id,tag:e.tagName,right:Math.round(e.getBoundingClientRect().right)}))})''')
        page.screenshot(path=str(OUT/f'customs-viewport-{width}.png'))
        result['languages'] = {}
        for lang in ['es','en','pt']:
            page.locator('#nav-lang-select').select_option(lang)
            result['languages'][lang] = page.locator('html').get_attribute('lang')
        page.screenshot(path=str(OUT/f'initial-{width}.png'), full_page=True)
        evidence['ui'].append(result)
        page.close()
    browser.close()
(OUT/'evidence.json').write_text(json.dumps(evidence,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(evidence,ensure_ascii=False,indent=2))
