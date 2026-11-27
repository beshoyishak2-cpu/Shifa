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

# Explicitly import the stylesheet from the component entry. The extracted app's
# entrypoint did not guarantee style.css was part of the web bundle.
if "import './style.css';" not in app and 'import "./style.css";' not in app:
    app = "import './style.css';\n" + app

# Portable inline SVGs for the welcome/promo artwork; do not depend on emoji fonts.
icon_component = r"""
function SareeInlineIcon({name,size=24}:{name:'bag'|'sparkle'|'scooter'|'all'|'restaurant'|'arrow';size?:number}){
 const common={width:size,height:size,viewBox:'0 0 24 24',fill:'none',stroke:'currentColor',strokeWidth:1.8,strokeLinecap:'round' as const,strokeLinejoin:'round' as const,focusable:false,'aria-hidden':true as const};
 const paths:Record<string,any>={
  bag:<><path d="M5 8h14l1 12H4L5 8Z"/><path d="M9 9V6a3 3 0 0 1 6 0v3"/><path d="M9 13h6"/></>,
  sparkle:<><path d="m12 2 1.8 6.2L20 10l-6.2 1.8L12 18l-1.8-6.2L4 10l6.2-1.8L12 2Z"/><path d="m19 15 .8 2.2L22 18l-2.2.8L19 21l-.8-2.2L16 18l2.2-.8L19 15Z"/></>,
  scooter:<><circle cx="6" cy="18" r="2.5"/><circle cx="18" cy="18" r="2.5"/><path d="M8.5 18h5l-2-7H8l-2 7"/><path d="M11 11h4l2 7M14 11l1-3h3"/><path d="M8 8h3"/></>,
  all:<><path d="m12 2 2.2 6.8L21 11l-6.8 2.2L12 20l-2.2-6.8L3 11l6.8-2.2L12 2Z"/><path d="m19 16 .6 1.8 1.8.6-1.8.6L19 21l-.6-2-1.8-.6 1.8-.6L19 16Z"/></>,
  restaurant:<><path d="M6 3v7M3.5 3v4a2.5 2.5 0 0 0 5 0V3M6 9.5V21"/><path d="M15 3v18M15 3c3 2 4 5 4 8h-4"/></>,
  arrow:<><path d="M19 12H5"/><path d="m12 19-7-7 7-7"/></>
 };
 return <svg {...common}>{paths[name]}</svg>;
}
"""
if "function SareeInlineIcon(" not in app:
    marker="type Role = 'customer' | 'merchant' | 'driver' | 'admin';"
    if marker not in app: raise SystemExit("Could not locate Role type for SVG icon component")
    app=app.replace(marker,icon_component+"\n"+marker,1)

# Replace all requested symbols in the customer welcome/promo flow with SVG components.
app=app.replace('<span className="saree-splash-scooter">🛵</span>','<span className="saree-splash-scooter"><SareeInlineIcon name="scooter" size={30}/></span>')
app=app.replace('<span>🛍️</span><i>✦</i>','<span><SareeInlineIcon name="bag" size={52}/></span><i><SareeInlineIcon name="sparkle" size={23}/></i>')
app=app.replace('<span>←</span>','<span className="saree-inline-arrow"><SareeInlineIcon name="arrow" size={15}/></span>')
app=app.replace("{id:'all',label:'الكل',emoji:'✨'},{id:'restaurant',label:'مطاعم',emoji:'🍽️'},{id:'cafe',label:'كافيهات',emoji:'☕'},{id:'grocery',label:'سوبر ماركت',emoji:'🛒'},{id:'vegetables',label:'خضار وفاكهة',emoji:'🥬'},{id:'pharmacy',label:'صيدليات',emoji:'💊'},{id:'errand',label:'مشوار خاص',emoji:'🛵'},{id:'doctors',label:'الأطباء',emoji:'🩺'}","{id:'all',label:'الكل',icon:'all'},{id:'restaurant',label:'مطاعم',icon:'restaurant'},{id:'cafe',label:'كافيهات',icon:'cafe'},{id:'grocery',label:'سوبر ماركت',icon:'grocery'},{id:'vegetables',label:'خضار وفاكهة',icon:'vegetables'},{id:'pharmacy',label:'صيدليات',icon:'pharmacy'},{id:'errand',label:'مشوار خاص',icon:'scooter'},{id:'doctors',label:'الأطباء',icon:'doctor'}")
app=app.replace("as {id:Service;label:string;emoji:string}[]).map(x=><button","as {id:Service;label:string;icon:string}[]).map(x=><button")
app=app.replace("<span>{x.emoji}</span>{x.label}</button>)}</div>","<span>{x.icon==='all'?<SareeInlineIcon name=\"all\"/>:x.icon==='restaurant'?<SareeInlineIcon name=\"restaurant\"/>:x.icon==='scooter'?<SareeInlineIcon name=\"scooter\"/>:x.icon==='cafe'?<SareeInlineIcon name=\"sparkle\"/>:x.icon==='grocery'?<SareeInlineIcon name=\"bag\"/>:<SareeInlineIcon name=\"sparkle\"/>}</span>{x.label}</button>)}</div>",1)
# Search suggestion emoji array rendered as raw text: replace it with icon component elements.
app=app.replace("{['🍽️','💊','🛒','🥬'][i]} {term}","{i===0?<SareeInlineIcon name=\"restaurant\" size={16}/>:<SareeInlineIcon name=\"bag\" size={16}/>} {term}")
# STORE_TYPES.icon is a symbolic data field; keep a stable icon key instead of a glyph.
app=app.replace("icon:'🍽️'","icon:'restaurant'")
app_path.write_text(app)

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

# Render the customer bar directly under document.body. This escapes any transformed,
# clipped, or scrolling app ancestor that can turn position:fixed into page-relative positioning.
if "createPortal(" not in app:
    start = app.find("{role==='customer'&&<nav className={`mobile-bottom-nav")
    if start < 0:
        raise SystemExit("Could not locate customer navigation JSX for body portal")
    end = app.find("</nav>}", start)
    if end < 0:
        raise SystemExit("Could not locate end of customer navigation JSX")
    end += len("</nav>}")
    block = app[start:end]
    nav_markup = block[len("{role==='customer'&&"):-1]
    app = app[:start] + "{role==='customer'&&createPortal((" + nav_markup + "),document.body)}" + app[end:]
    app = app.replace("${searchKeyboardOpen?' keyboard-open':''}", "${searchKeyboardOpen?' keyboard-open':''}${dark?' dark':''}", 1)

if "from 'react-dom'" not in app:
    app = app.replace("from 'react';", "from 'react';\nimport { createPortal } from 'react-dom';", 1)
if "createPortal((" not in app or "document.body" not in app:
    raise SystemExit("Customer navigation was not moved into document.body")

# Replace the delivery-location emoji with a deterministic inline SVG pin.
location_path = Path("src/LocationSystem.tsx")
if location_path.exists():
    location = location_path.read_text()
    location_old = '<span>📍</span>'
    location_new = '<span className="s3-location-pin" aria-hidden="true"><svg viewBox="0 0 24 24" focusable="false"><path d="M20 10c0 5.2-8 12-8 12S4 15.2 4 10a8 8 0 1 1 16 0Z" fill="#0b9a79"/><circle cx="12" cy="10" r="2.8" fill="#fff"/></svg></span>'
    if location_old in location:
        location = location.replace(location_old, location_new, 1)
    elif 'className="s3-location-pin"' not in location:
        raise SystemExit("Could not locate delivery-location emoji")
    location_path.write_text(location)

app_path.write_text(app)

# Keep the bottom bar fixed and above every customer screen at mobile and desktop widths.
css += r"""

/* Web + mobile customer navigation: loaded from App.tsx and anchored to the viewport. */
#root .app.customer-nav-enabled{padding-bottom:calc(82px + env(safe-area-inset-bottom,0px))!important}
body .mobile-bottom-nav{position:fixed!important;inset-inline:0!important;left:0!important;right:0!important;bottom:0!important;top:auto!important;z-index:2147483647!important;display:grid!important;grid-template-columns:repeat(5,minmax(0,1fr));align-items:center;gap:0;width:100%;min-height:66px;margin:0;padding-top:7px;padding-left:8px;padding-right:8px;padding-bottom:env(safe-area-inset-bottom,0px)!important;box-sizing:border-box;background:#fff;border-top:1px solid #e3ece7;box-shadow:0 -8px 24px #00000014;direction:rtl;isolation:isolate;transform:none!important;contain:none!important}
.mobile-bottom-nav.dark{background:#20352d;border-color:#344c41}
.mobile-bottom-nav button{color:#80938c}
.mobile-bottom-nav.dark button{color:#a5b9ae}
.mobile-bottom-nav button.active{color:#087f68}
.mobile-bottom-nav.dark button.active{color:#4bc49d}
.s3-location-pin{display:inline-grid;place-items:center;flex:none;width:22px;height:22px}
.s3-location-pin svg{display:block;width:22px;height:22px}
.mobile-bottom-nav button{display:flex;flex-direction:column;align-items:center;justify-content:center;min-width:0;min-height:48px;padding:4px 2px;gap:4px;background:transparent;color:var(--muted);font:inherit;font-size:11px;border:0;border-radius:10px;white-space:nowrap}
.mobile-bottom-nav button.active{color:var(--green);font-weight:800}
.mobile-bottom-nav button.active:after{top:-7px}
.mobile-bottom-nav .nav-cart-icon{position:relative;display:inline-flex;align-items:center;justify-content:center}
.hero-art{display:grid;place-items:center;overflow:hidden}
.hero-art svg{display:block;width:100%;height:100%;max-width:160px;max-height:160px}\n.saree-promo-art>span,.saree-promo-art>i{display:grid;place-items:center}.saree-promo-art svg{display:block}.saree-splash-scooter svg{color:#fff;display:block}.saree-inline-arrow{display:inline-grid;vertical-align:middle;place-items:center}.saree-inline-arrow svg{display:block}
@media(max-width:700px){#root .app.customer-nav-enabled{padding-bottom:calc(82px + env(safe-area-inset-bottom,0px))!important}.mobile-bottom-nav{min-height:64px;padding-left:5px;padding-right:5px}.mobile-bottom-nav button{font-size:10px}}
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
  assert.ok(css.includes('body .mobile-bottom-nav{position:fixed!important'));
  assert.ok(source.includes("import './style.css';"));
  assert.ok(css.includes('padding-bottom:env(safe-area-inset-bottom,0px)!important'));
  assert.ok(css.includes('z-index:2147483647!important'));
  assert.ok(css.includes('.app.customer-nav-enabled{padding-bottom:'));
  assert.ok(source.includes('createPortal(('));
  assert.ok(source.includes('document.body'));
  assert.ok(source.includes('function SareeInlineIcon('));
  assert.ok(!source.includes('🛍️'));
  assert.ok(!source.includes('>✦</i>'));
  assert.ok(!source.includes('>🛵</span>'));
  assert.ok(!source.includes('<span>←</span>'));
  assert.ok(!source.includes('🏡'));
  assert.ok(!source.includes('✨'));
  assert.ok(!source.includes('🍽️'));
  assert.ok(css.includes('env(safe-area-inset-bottom,0px)'));
});
test('delivery location indicator is inline SVG rather than an emoji glyph', () => {
  const location = fs.readFileSync(path.join(root, 'src/LocationSystem.tsx'), 'utf8');
  assert.ok(location.includes('className="s3-location-pin"'));
  assert.ok(location.includes('<svg viewBox="0 0 24 24"'));
  assert.ok(!location.includes('<span>📍</span>'));
});
'''
    if "polish uses imported React hooks and cannot throw React is not defined" not in tests:
        test_path.write_text(tests + additions)

print("Applied web/customer runtime fixes.")
