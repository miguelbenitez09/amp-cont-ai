"""Keep all authored card surfaces in the shared palette contract."""
import re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]/'src/serving/static'
def test_all_authored_card_types_have_theme_styles():
 css=(ROOT/'css/cards.css').read_text(encoding='utf-8')
 sources=[ROOT/'index.html',ROOT/'landing.html',*list((ROOT/'js').glob('*.js'))]
 cards=set()
 for path in sources:
  for value in re.findall(r"class=[\"']([^\"']+)",path.read_text(encoding='utf-8')):
   cards.update(c for c in value.split() if c.endswith('-card'))
 # Settings is a modal surface, not a content card.
 cards.discard('settings-card')
 assert not {c for c in cards if '.'+c not in css}
def test_every_surface_loads_shared_card_styles():
 for file in ['index.html','landing.html','framework/index.html','framework/app.html']:
  assert '/static/css/cards.css' in (ROOT/file).read_text(encoding='utf-8')
def test_interface_defaults_do_not_override_theme_palettes():
 css=(ROOT/'css/interface.css').read_text(encoding='utf-8')
 ops=re.search(r'\.ops-app\s*\{([^}]+)',css).group(1)
 assert '--bg-card:' not in ops
 portal=re.search(r'\.portal\s*\{([^}]+)',css).group(1)
 assert '--portal-cyan:' not in portal
