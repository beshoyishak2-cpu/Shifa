from pathlib import Path
app_path=Path("src/App.tsx"); css_path=Path("src/style.css")
if not app_path.is_file() or not css_path.is_file(): raise SystemExit("Brand logo patch requires src/App.tsx and src/style.css")
app=app_path.read_text()
anchor="type Role = 'customer' | 'merchant' | 'driver' | 'admin';"
if anchor not in app: raise SystemExit("Could not find stable App.tsx insertion point for Saree3 logo constants")
if "const SAREE_LOGO_SRC" in app: raise SystemExit("SAREE_LOGO_SRC already exists; refusing to overwrite unknown implementation")
constants="const SAREE_LOGO_SRC = 'brand/sari3-lockup-green.png';\nconst SAREE_LOGO_WHITE_SRC = 'brand/sari3-lockup-white.png';\n"
app=app.replace(anchor,constants+anchor,1)
old='<div className="brand"><b>سريع</b><small>كل خدمات ملوي في مكان واحد</small></div>'
new=('<div className="brand brand-image"><img src={\'/\' + (dark ? SAREE_LOGO_WHITE_SRC : SAREE_LOGO_SRC)} '
     'alt="سريع" className="brand-logo" /></div>')
if app.count(old)!=1: raise SystemExit(f"Expected exactly one temporary text-only brand header, found {app.count(old)}")
app=app.replace(old,new,1); app_path.write_text(app)
css=css_path.read_text()+"""
/* Approved Saree3 lockup in the responsive application header. */
.brand-image{display:flex;align-items:center;justify-content:center;min-width:0}
.brand-logo{display:block;width:clamp(112px,18vw,174px);height:48px;object-fit:contain;object-position:right center}
@media(max-width:650px){.brand-logo{width:clamp(105px,31vw,140px);height:42px}}
"""
css_path.write_text(css); print("Applied approved light/dark Saree3 lockups to the app header.")
