"""Exercise all operational views and collect responsive interface evidence."""
import json
from pathlib import Path
from playwright.sync_api import sync_playwright

OUT = Path('reports/ui-redesign-2026-10-08')
OUT.mkdir(parents=True, exist_ok=True)
results, issues = [], []
with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    for width, height in [(390,844),(768,1024),(1440,900)]:
        page = browser.new_page(viewport={'width':width,'height':height})
        errors = []
        page.on('pageerror', lambda error: errors.append(str(error)))
        page.goto('http://127.0.0.1:8000/app', wait_until='domcontentloaded')
        page.wait_for_timeout(1000)
        theme = page.locator('#theme-selector')
        if theme.count():
            values = theme.locator('option').evaluate_all('(options)=>options.map(o=>o.value)')
            for value in values:
                theme.select_option(value)
                if not page.locator('body').evaluate('(body)=>body.classList.contains("ops-app")'):
                    issues.append({'width':width,'theme':value,'error':'Theme removed interface identity'})
            theme.select_option(values[0])
        tabs = page.locator('.tabs-nav > .tab-btn').evaluate_all('(buttons) => buttons.map(b=>b.dataset.tab)')
        for tab in tabs:
            toggle = page.locator('#workspace-navigation-toggle')
            if toggle.is_visible() and toggle.get_attribute('aria-expanded')=='false':
                toggle.click()
            page.locator(f'.tabs-nav > [data-tab="{tab}"]').click()
            page.wait_for_timeout(400)
            observation = page.evaluate('''() => ({
                visiblePanels:[...document.querySelectorAll('main > .tab-content')].filter(e=>e.getClientRects().length).map(e=>e.id),
                viewport:innerWidth, bodyWidth:document.body.scrollWidth,
                wideCards:[...document.querySelectorAll('main > .tab-content.active .card')].filter(e=>e.getClientRects().length&&e.getBoundingClientRect().width>innerWidth+1).map(e=>({id:e.id,width:Math.round(e.getBoundingClientRect().width)})),
                activeTab:document.querySelector('.tabs-nav .tab-btn.active')?.getAttribute('aria-current')
            })''')
            observation.update({'width':width,'tab':tab})
            if observation['visiblePanels'] != [tab] or observation['wideCards'] or observation['activeTab'] != 'page':
                issues.append(observation)
            page.screenshot(path=str(OUT/f'{tab}-{width}.png'))
            results.append(observation)
        page.locator('#btn-auth-iam').click()
        page.wait_for_timeout(350)
        page.screenshot(path=str(OUT/f'auth-{width}.png'))
        page.keyboard.press('Escape')
        page.locator('#btn-settings-gear').click()
        page.wait_for_timeout(200)
        page.screenshot(path=str(OUT/f'settings-{width}.png'))
        page.keyboard.press('Escape')
        if page.locator('#settings-modal').is_visible():
            issues.append({'width':width,'error':'Settings did not close with Escape'})
        page.goto('http://127.0.0.1:8000/',wait_until='domcontentloaded')
        page.wait_for_timeout(500)
        portal = page.evaluate('() => ({viewport:innerWidth,documentWidth:document.documentElement.scrollWidth,bodyWidth:document.body.scrollWidth})')
        if portal['bodyWidth'] > width+1:
            issues.append({'surface':'portal','width':width,**portal})
        page.screenshot(path=str(OUT/f'portal-{width}.png'))
        results.append({'surface':'portal','width':width,**portal,'errors':errors})
        if errors:
            issues.append({'width':width,'errors':errors})
        page.close()
    browser.close()
(OUT/'verification.json').write_text(json.dumps({'results':results,'issues':issues},ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'views':len(results),'issues':issues},ensure_ascii=False,indent=2))
raise SystemExit(bool(issues))

