from pathlib import Path
import re

app_path = Path("src/App.tsx")
css_path = Path("src/style.css")
app = app_path.read_text()
css = css_path.read_text()

# Runtime-safe React hooks: use the named hooks already imported by App.tsx.
app = app.replace("React.useState(", "useState(").replace("React.useEffect(", "useEffect(")
react_import = re.search(r"import\s*\{([^}]+)\}\s*from\s*['\"]react['\"]\s*;", app)
if not react_import:
    raise SystemExit("Could not find named React hooks import in App.tsx")
imports = [x.strip() for x in react_import.group(1).split(",") if x.strip()]
for hook in ("useState", "useEffect"):
    if hook not in imports:
        imports.append(hook)
app = app[:react_import.start()] + "import { " + ", ".join(imports) + " } from 'react';" + app[react_import.end():]
if "React.useState(" in app or "React.useEffect(" in app:
    raise SystemExit("React namespace hook usage remains after runtime fix")

# Add a customer-only root class so the bottom navigation can reserve page space.
root_old = "return <div className={dark?'app dark':'app'}>"
root_new = "return <div className={role==='customer'?(dark?'app dark customer-nav-enabled':'app customer-nav-enabled'):(dark?'app dark':'app')}>"
if root_old in app:
    app = app.replace(root_old, root_new, 1)
elif root_new not in app:
    raise SystemExit("Could not locate the app root to scope customer navigation")

# Replace the welcome artwork with a self-contained inline SVG (no external asset).
hero_old = '<div className="hero-art">🏡<i>🛵</i></div>'
hero_new = """<div className="hero-art" aria-hidden="true"><svg viewBox="0 0 160 160" focusable="false"><circle cx="80" cy="80" r="70" fill="#c5e9db"/><path d="M34 76 80 38l46 38" fill="none" stroke="#087f68" strokeWidth="8" strokeLinecap="round" strokeLinejoin="round"/><path d="M47 74v47h66V74" fill="#fff" stroke="#087f68" strokeWidth="6" strokeLinejoin="round"/><rect x="70" y="91" width="20" height="30" rx="3" fill="#0b9a79"/><path d="M27 130h28l8-15h23l10 15h17" fill="none" stroke="#164e63" strokeWidth="5" strokeLinecap="round" strokeLinejoin="round"/><circle cx="42" cy="132" r="9" fill="#164e63"/><circle cx="106" cy="132" r="9" fill="#164e63"/><path d="M85 113h15l8 8" fill="none" stroke="#164e63" strokeWidth="5" strokeLinecap="round"/></svg></div>"""
if hero_old in app:
    app = app.replace(hero_old, hero_new, 1)
elif 'className="hero-art" aria-hidden="true"><svg viewBox="0 0 160 160"' not in app:
    m = re.search(r'<div className="hero-art"[^>]*>.*?</div>', app, flags=re.S)
    if not m:
        raise SystemExit("Could not locate welcome-card artwork")
    app = app[:m.start()] + hero_new + app[m.end():]

if "mobile-bottom-nav" not in app:
    raise SystemExit("Customer bottom navigation markup is missing")

app_path.write_text(app)

# Keep the bottom bar fixed and above every customer screen at mobile and desktop widths.
css += r"""

/* Web + mobile customer navigation: fixed, always visible, and above page content. */
.app.customer-nav-enabled{padding-bottom:calc(78px + env(safe-area-inset-bottom,0px))}
.mobile-bottom-nav{position:fixed!important;left:0!important;right:0!important;bottom:0!important;z-index:2147483000!important;display:grid!important;grid-template-columns:repeat(5,minmax(0,1fr));align-items:center;gap:0;width:100%;min-height:66px;margin:0;padding:7px 8px calc(7px + env(safe-area-inset-bottom,0px));box-sizing:border-box;background:var(--surface);border-top:1px solid var(--line);box-shadow:0 -8px 24px #00000014;direction:rtl}
.mobile-bottom-nav button{display:flex;flex-direction:column;align-items:center;justify-content:center;min-width:0;min-height:48px;padding:4px 2px;gap:4px;background:transparent;color:var(--muted);font:inherit;font-size:11px;border:0;border-radius:10px;white-space:nowrap}
.mobile-bottom-nav button.active{color:var(--green);font-weight:800}
.mobile-bottom-nav button.active:after{top:-7px}
.mobile-bottom-nav .nav-cart-icon{position:relative;display:inline-flex;align-items:center;justify-content:center}
.hero-art{display:grid;place-items:center;overflow:hidden}
.hero-art svg{display:block;width:100%;height:100%;max-width:160px;max-height:160px}
@media(max-width:700px){.app.customer-nav-enabled{padding-bottom:calc(78px + env(safe-area-inset-bottom,0px))}.mobile-bottom-nav{min-height:64px;padding-left:5px;padding-right:5px}.mobile-bottom-nav button{font-size:10px}}
@media(max-width:700px){.mobile-bottom-nav.keyboard-open{display:none!important}}
"""
css_path.write_text(css)

# Make the copied admin panel safe too, even if a later step recopies it.
for component_path in (Path("src/SareeAdvancedAdmin.tsx"), Path("app-overlay/src/SareeAdvancedAdmin.tsx")):
    if component_path.exists():
        component = component_path.read_text()
        old = "if(!admin)return <div style={css.wrap}>"
        if old in component:
            component = component.replace(old, "if(!admin)return null;", 1)
        if "if(!admin)return null;" in component:
            start = component.index("if(!admin)return null;") + len("if(!admin)return null;")
            admin_marker = "return <div style={css.wrap}>{!opened?<button style={css.trigger} onClick={()=>{setOpened(true);void load();}}>إدارة متقدمة"
            end = component.find(admin_marker, start)
            if end >= 0:
                component = component[:start] + "\n" + component[end:]
        component_path.write_text(component)

# Runtime/UI regression tests (npm test runs before the production bundle build).
test_path = Path("tests/source-smoke.test.cjs")
if test_path.exists():
    tests = test_path.read_text()
    additions = r'''
test('polish uses imported React hooks and cannot throw React is not defined', () => {
  const source = app();
  assert.ok(source.includes("from 'react'"));
  assert.ok(source.includes('useState('));
  assert.ok(source.includes('useEffect('));
  assert.ok(!source.includes('React.useState('));
  assert.ok(!source.includes('React.useEffect('));
});
test('legacy pharmacy floating search is not rendered to non-admin customers', () => {
  const panel = fs.readFileSync(path.join(root, 'src/SareeAdvancedAdmin.tsx'), 'utf8');
  assert.ok(panel.includes('if(!admin)return null;'));
  assert.ok(!panel.includes('البحث عن دواء بالصيدليات'));
});
test('welcome artwork is inline and customer navigation is fixed on every viewport', () => {
  const source = app();
  const css = fs.readFileSync(path.join(root, 'src/style.css'), 'utf8');
  assert.ok(source.includes('className="hero-art" aria-hidden="true"><svg viewBox="0 0 160 160"'));
  assert.ok(source.includes('customer-nav-enabled'));
  assert.ok(source.includes('mobile-bottom-nav'));
  assert.ok(css.includes('.mobile-bottom-nav{position:fixed!important'));
  assert.ok(css.includes('z-index:2147483000!important'));
  assert.ok(css.includes('.app.customer-nav-enabled{padding-bottom:'));
});
'''
    if "polish uses imported React hooks and cannot throw React is not defined" not in tests:
        test_path.write_text(tests + additions)

print("Applied web/customer runtime fixes.")
