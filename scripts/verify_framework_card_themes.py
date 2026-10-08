"""Static presentation regression; does not simulate successful backend operations."""
import functools,json,threading
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
from playwright.sync_api import sync_playwright
class QuietHandler(SimpleHTTPRequestHandler):
 def log_message(self,*args):pass
handler=functools.partial(QuietHandler,directory=str(Path('src/serving').resolve()))
server=ThreadingHTTPServer(('127.0.0.1',0),handler)
thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
out=Path('reports/card-themes-2026-10-08');out.mkdir(parents=True,exist_ok=True)
results=[]
try:
 with sync_playwright() as p:
  b=p.chromium.launch()
  for width in [390,1440]:
   page=b.new_page(viewport={'width':width,'height':900})
   page.goto(f'http://127.0.0.1:{server.server_port}/static/framework/index.html#login')
   page.locator('#login-user').wait_for()
   for theme in ['ocean','obsidian','forest','amber','light']:
    page.locator('#theme-select').select_option(theme)
    for route in ['login','overview','models','datasets','training','agents','setup','security','backups']:
     page.evaluate('(route)=>location.hash=route',route);page.wait_for_timeout(90)
     page.mouse.move(0,0)
     result=page.evaluate("""()=>{const probe=document.createElement('span');document.body.append(probe);probe.style.background='var(--surface)';const expected=getComputedStyle(probe).backgroundColor;probe.remove();return {expected,count:document.querySelectorAll('main .card').length,failures:[...document.querySelectorAll('main .card')].filter(e=>getComputedStyle(e).backgroundColor!==expected||e.getBoundingClientRect().right>innerWidth+1).map(e=>e.className)}}""")
     result.update(width=width,theme=theme,route=route);results.append(result)
     if route=='overview':page.screenshot(path=str(out/f'framework-{theme}-{width}.png'))
   page.close()
  b.close()
finally:
 server.shutdown();server.server_close()
issues=[r for r in results if r['failures']]
(out/'framework-verification.json').write_text(json.dumps(dict(results=results,issues=issues),indent=2),encoding='utf-8')
print(json.dumps(dict(checks=len(results),issues=issues)))
raise SystemExit(bool(issues))
