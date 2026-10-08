"""Regression checks for card palettes, layout and hover in every available theme."""
import json
from pathlib import Path
from playwright.sync_api import sync_playwright
OUT=Path("reports/card-themes-2026-10-08")
OUT.mkdir(parents=True,exist_ok=True)
results=[]
issues=[]
with sync_playwright() as p:
 browser=p.chromium.launch()
 for width in [390,1440]:
  page=browser.new_page(viewport={"width":width,"height":900})
  page.goto("http://127.0.0.1:8000/app")
  page.wait_for_timeout(700)
  themes=page.locator("#theme-selector option").evaluate_all("os=>os.map(o=>o.value)")
  tabs=page.locator(".tabs-nav > .tab-btn").evaluate_all("bs=>bs.map(b=>b.dataset.tab)")
  for theme in themes:
   page.locator("#theme-selector").select_option(theme)
   for tab in tabs:
    toggle=page.locator("#workspace-navigation-toggle")
    if toggle.is_visible() and toggle.get_attribute("aria-expanded")=="false":toggle.click()
    page.locator(f'.tabs-nav > [data-tab="{tab}"]').click()
    page.wait_for_timeout(60)
    result=page.evaluate("""() => {
     const probe=document.createElement('span');document.body.append(probe);
     probe.style.background='var(--bg-card)';const expected=getComputedStyle(probe).backgroundColor;
     probe.style.background='var(--bg-card-hover)';const hovered=getComputedStyle(probe).backgroundColor;
     probe.style.background='var(--bg-input)';const nested=getComputedStyle(probe).backgroundColor;probe.remove();
     const cards=[...document.querySelectorAll('main > .tab-content.active :is(.card,.algo-stat-card,.kpi-card,.diag-metric-card,.cot-step-card,.inner-card,.method-phase-card)')].filter(e=>e.getClientRects().length);
     return {expected,nested,count:cards.length,failures:cards.filter(e=>getComputedStyle(e).backgroundColor!==((e.matches(':hover')||e.matches(':focus-within'))?hovered:expected)||e.getBoundingClientRect().right>innerWidth+1).map(e=>({class:e.className,bg:getComputedStyle(e).backgroundColor,right:e.getBoundingClientRect().right})),previewFailures:[...document.querySelectorAll('.tab-content.active .card-hover-preview')].filter(e=>getComputedStyle(e).backgroundColor!==nested).length};
    }""")
    result.update(width=width,theme=theme,tab=tab)
    if result['failures'] or result['previewFailures']:issues.append(result)
    results.append(result)
    if tab=='tab-landing':
     page.locator('.capabilities-grid').screenshot(path=str(OUT/f'cards-{theme}-{width}.png'))
   page.locator('#btn-settings-gear').click();page.wait_for_timeout(100)
   page.screenshot(path=str(OUT/f'settings-{theme}-{width}.png'));page.keyboard.press('Escape')
  page.goto('http://127.0.0.1:8000/')
  page.wait_for_timeout(700)
  themes=page.locator('#landing-theme-select option').evaluate_all('os=>os.map(o=>o.value)')
  for theme in themes:
   page.locator('#landing-theme-select').select_option(theme)
   result=page.evaluate("""()=>{const probe=document.createElement('span');document.body.append(probe);probe.style.background='var(--portal-surface-card)';const expected=getComputedStyle(probe).backgroundColor;probe.remove();return {expected,failures:[...document.querySelectorAll('.feature-card,.port-card,.telemetry-card,.vision-card,.medallion-card,.cta-inner-card')].filter(e=>getComputedStyle(e).backgroundColor!==expected||e.getBoundingClientRect().right>innerWidth+1).map(e=>e.className)}}""")
   result.update(surface='portal',width=width,theme=theme)
   if result['failures']:issues.append(result)
   results.append(result)
   page.screenshot(path=str(OUT/f'portal-{theme}-{width}.png'))
  page.close()
 browser.close()
(OUT/'verification.json').write_text(json.dumps(dict(results=results,issues=issues),indent=2),encoding='utf-8')
print(json.dumps(dict(checks=len(results),issues=issues),indent=2))
raise SystemExit(bool(issues))
