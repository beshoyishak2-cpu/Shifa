import re
from pathlib import Path

app_path=Path("src/App.tsx")
css_path=Path("src/style.css")
if not app_path.is_file() or not css_path.is_file():
    raise SystemExit("Brand logo patch requires src/App.tsx and src/style.css")
app=app_path.read_text()

def set_constant(name,value):
    global app
    pattern=re.compile(r"(?m)^(\s*(?:export\s+)?(?:const|let|var)\s+"+re.escape(name)+r"\s*=\s*)[^;\n]+(;[^\n]*)?")
    found=list(pattern.finditer(app))
    if len(found)>1: raise SystemExit(f"Multiple {name} declarations found")
    if found:
        app=pattern.sub(lambda m:m.group(1)+"'"+value+"';",app,count=1)
    elif name=="SAREE_LOGO_WHITE_SRC":
        green=re.search(r"(?m)^.*const SAREE_LOGO_SRC\s*=\s*[^;]+;.*$",app)
        if not green: raise SystemExit("Cannot add white logo constant: SAREE_LOGO_SRC is missing")
        app=app[:green.end()]+"\nconst SAREE_LOGO_WHITE_SRC = '"+value+"';"+app[green.end():]
    elif name=="SAREE_LOGO_SRC":
        anchor="type Role = 'customer' | 'merchant' | 'driver' | 'admin';"
        if anchor not in app: raise SystemExit("Cannot insert SAREE_LOGO_SRC: role declaration is missing")
        app=app.replace(anchor,"const SAREE_LOGO_SRC = '"+value+"';\nconst SAREE_LOGO_WHITE_SRC = 'brand/sari3-lockup-white.png';\n"+anchor,1)
    else: raise SystemExit(f"{name} declaration is missing")

set_constant("SAREE_LOGO_SRC","brand/sari3-lockup-green.png")
set_constant("SAREE_LOGO_WHITE_SRC","brand/sari3-lockup-white.png")

# Splash is always rendered on the green brand background: white lockup only, no text fallback.
splash_pattern=re.compile(r'<div className="saree-splash-brand">[\s\S]*?</div>')
app,splash_count=splash_pattern.subn(
    '''<div className="saree-splash-brand"><img src={'/' + SAREE_LOGO_WHITE_SRC} alt="سريع" /></div>''',
    app,count=1
)
# Some platform overlays do not include the separate splash component; the native splash is still generated.

header_match=re.search(r"<header\b[\s\S]*?</header>",app)
if not header_match: raise SystemExit("Could not locate the app header")
header=header_match.group(0)
desired="src={'/' + (dark ? SAREE_LOGO_WHITE_SRC : SAREE_LOGO_SRC)}"
img_pattern=re.compile(r"(<img\b[^>]*?\bsrc=)\{[^}]*\}")
header,new_count=img_pattern.subn(
    lambda m:m.group(1)+"{"+ "'/' + (dark ? SAREE_LOGO_WHITE_SRC : SAREE_LOGO_SRC)" + "}",
    header,count=1
)
if new_count==0:
    text_logo=re.compile(r"<(?:b|strong|span)[^>]*>\s*سريع\s*</(?:b|strong|span)>")
    header,count=text_logo.subn(
        '''<img src={'/' + (dark ? SAREE_LOGO_WHITE_SRC : SAREE_LOGO_SRC)} alt="سريع" className="brand-logo" />''',
        header,count=1
    )
if desired not in header: raise SystemExit("Could not bind header logo to the light/dark brand lockups")
app=app[:header_match.start()]+header+app[header_match.end():]
app_path.write_text(app)

css=css_path.read_text()+"""
/* Approved Saree3 lockup in the responsive application header and splash. */
.brand-logo{display:block;width:clamp(112px,18vw,174px);height:48px;object-fit:contain;object-position:right center}
.saree-splash-brand img{display:block;width:min(68vw,320px);max-height:150px;object-fit:contain}
@media(max-width:650px){.brand-logo{width:clamp(105px,31vw,140px);height:42px}}
"""
css_path.write_text(css)
print("Applied approved green/white Saree3 lockups to header and splash.")
