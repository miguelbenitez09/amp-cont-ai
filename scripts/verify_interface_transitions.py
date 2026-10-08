"""Verify exclusive panels, reduced motion and late route response isolation."""
import functools,json,threading,time
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
from playwright.sync_api import sync_playwright
out=Path('reports/transitions-2026-10-08');out.mkdir(parents=True,exist_ok=True)
results=[]
class Handler(SimpleHTTPRequestHandler):
 def log_message(self,*args):pass
 def do_GET(self):
  if self.path in ['/api/models','/api/datasets']:
   time.sleep(.6 if self.path=='/api/models' else .02)
   self.send_response(200);self.send_header('Content-Type','application/json');self.end_headers();self.wfile.write(b'{"items":[]}');return
  super().do_GET()
server=ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Handler,directory=str(Path('src/serving').resolve())))
threading.Thread(target=server.serve_forever,daemon=True).start()
try:
 with sync_playwright() as p:
  b=p.chromium.launch()
  for width in [390,1440]:
   for reduced in ['no-preference','reduce']:
    page=b.new_page(viewport={'width':width,'height':900},reduced_motion=reduced)
    errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
    page.goto('http://127.0.0.1:8000/app');page.wait_for_timeout(600)
    samples=page.evaluate("""async()=>{
     const snapshots=[];
     const buttons=[...document.querySelectorAll('.tabs-nav > .tab-btn')];
     for(const button of [...buttons,...buttons.slice().reverse()]) {
      button.click();
      for(let frame=0;frame<3;frame++) {
       await new Promise(requestAnimationFrame);
       const visible=[...document.querySelectorAll('main > .tab-content')].filter(e=>e.getClientRects().length);
       snapshots.push({target:button.dataset.tab,visible:visible.map(e=>e.id),animations:visible.flatMap(e=>e.getAnimations()).length});
      }
     }
     return snapshots;
    }""")
    assert all(s['visible']==[s['target']] for s in samples)
    if reduced=='reduce':assert all(s['animations']==0 for s in samples)
    assert not errors,errors
    results.append({'surface':'operations','width':width,'motion':reduced,'frames':len(samples),'passed':True})
    page.close()
  page=b.new_page()
  page.goto(f'http://127.0.0.1:{server.server_port}/static/framework/index.html#overview')
  page.locator('main h1').first.wait_for()
  page.evaluate("location.hash='models'")
  page.wait_for_timeout(100)
  assert page.locator('main .loading').is_visible()
  page.evaluate("location.hash='datasets'")
  page.wait_for_timeout(900)
  assert page.locator('main h1').inner_text()=='Datasets'
  assert page.locator('#dataset-help').is_visible()
  assert page.locator('main').get_attribute('aria-busy') is None
  results.append({'surface':'framework','lateResponseIgnored':True,'passed':True})
  page.screenshot(path=str(out/'framework-latest-route.png'));page.close();b.close()
finally:
 server.shutdown();server.server_close()
(out/'verification.json').write_text(json.dumps(results,indent=2),encoding='utf-8')
print(json.dumps(results,indent=2))
