import re
from pathlib import Path

app_path = Path("src/App.tsx")
css_path = Path("src/style.css")
if not app_path.is_file() or not css_path.is_file():
    raise SystemExit("Brand logo patch requires src/App.tsx and src/style.css")
app = app_path.read_text()

def set_constant(name: str, value: str) -> None:
    global app
    pattern = re.compile(r"(?m)^(\s*(?:export\s+)?(?:const|let|var)\s+" + re.escape(name) + r"\s*=\s*)[^;\n]+(;[^\n]*)?")
    matches = list(pattern.finditer(app))
    if len(matches) > 1:
        raise SystemExit(f"Expected at most one {name} declaration, found {len(matches)}")
    if matches:
        app = pattern.sub(lambda m: m.group(1) + "'" + value + "';", app, count=1)
    elif name == "SAREE_LOGO_WHITE_SRC":
        green_decl = re.search(r"(?m)^.*const SAREE_LOGO_SRC\s*=\s*[^;]+;.*$", app)
        if not green_decl:
            raise SystemExit("Cannot add white lockup constant without SAREE_LOGO_SRC")
        app = app[:green_decl.end()] + "\nconst SAREE_LOGO_WHITE_SRC = '" + value + "';" + app[green_decl.end():]
    else:
        raise SystemExit(f"Expected one {name} declaration, found none")

set_constant("SAREE_LOGO_SRC", "brand/sari3-lockup-green.png")
set_constant("SAREE_LOGO_WHITE_SRC", "brand/sari3-lockup-white.png")

# The splash is always on the green brand background, so it always uses the white lockup.
splash_pattern = re.compile(
    r"\{SAREE_LOGO_SRC\?\s*<img\b[^>]*src=\{[^}]*SAREE_LOGO_SRC[^}]*\}[^>]*/>\s*:\s*<span[^>]*>سريع</span>\}"
)
app, splash_count = splash_pattern.subn(
    '''<img src={'/' + SAREE_LOGO_WHITE_SRC} alt="سريع" />''', app, count=1
)
if splash_count != 1:
    # Also accept a fallback block with slightly different whitespace/attributes.
    if "saree-splash-wordmark" in app:
        raise SystemExit("Could not safely replace the temporary splash text fallback")

header = re.search(r"<header\b[\s\S]*?</header>", app)
if not header:
    raise SystemExit("Could not locate the app header")
header_text = header.group(0)
desired = "src={'/' + (dark ? SAREE_LOGO_WHITE_SRC : SAREE_LOGO_SRC)}"
if desired not in header_text:
    header_text = re.sub(r"src=\{[^}]*SAREE_LOGO_SRC[^}]*\}", desired, header_text, count=1)
    if desired not in header_text:
        raise SystemExit("Could not bind header logo to the dark/light theme")
app = app[:header.start()] + header_text + app[header.end():]
app_path.write_text(app)

css = css_path.read_text()
css += """
/* Approved Saree3 lockup in the responsive application header and splash. */
.brand-logo{display:block;width:clamp(112px,18vw,174px);height:48px;object-fit:contain;object-position:right center}
.saree-splash-brand img{display:block;width:min(68vw,320px);max-height:150px;object-fit:contain}
@media(max-width:650px){.brand-logo{width:clamp(105px,31vw,140px);height:42px}}
"""
css_path.write_text(css)
print("Applied approved green/white Saree3 lockups to header and splash; removed text-only splash fallback.")
