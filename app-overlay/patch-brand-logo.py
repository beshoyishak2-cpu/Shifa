import re
from pathlib import Path

app_path = Path("src/App.tsx")
css_path = Path("src/style.css")
if not app_path.is_file() or not css_path.is_file():
    raise SystemExit("Brand logo patch requires src/App.tsx and src/style.css")

app = app_path.read_text()
green = "const SAREE_LOGO_SRC = 'brand/sari3-lockup-green.png';"
white = "const SAREE_LOGO_WHITE_SRC = 'brand/sari3-lockup-white.png';"
pattern = re.compile(r"(?m)^\s*(?:export\s+)?(?:const|let|var)\s+SAREE_LOGO_SRC\s*=\s*[^;\n]+;")
matches = list(pattern.finditer(app))
if len(matches) > 1:
    raise SystemExit(f"Found {len(matches)} SAREE_LOGO_SRC declarations; refusing ambiguous edit")
if matches:
    app = pattern.sub(green, app, count=1)
else:
    anchor = "type Role = 'customer' | 'merchant' | 'driver' | 'admin';"
    if anchor not in app:
        raise SystemExit("Could not find stable App.tsx insertion point for SAREE_LOGO_SRC")
    app = app.replace(anchor, green + "\n" + anchor, 1)

if "SAREE_LOGO_WHITE_SRC" not in app:
    # Keep the paired lockup constant adjacent to the green source declaration.
    app = app.replace(green, green + "\n" + white, 1)

conditional = "src={'/' + (dark ? SAREE_LOGO_WHITE_SRC : SAREE_LOGO_SRC)}"
app = app.replace("src={SAREE_LOGO_SRC}", conditional)
app = app.replace("src={SAREE_LOGO_GREEN_SRC}", conditional)

header_match = re.search(r"<header\b[\s\S]*?</header>", app)
if not header_match:
    raise SystemExit("Could not locate the app header to bind the approved lockups")
header = header_match.group(0)

# Convert the temporary text-only brand wordmark, if this header still has one.
text_logo = re.compile(r"<(?:b|strong|span)[^>]*>\s*سريع\s*</(?:b|strong|span)>")
if "SAREE_LOGO_SRC" not in header and not re.search(r"<img\b[^>]*src=", header):
    header, count = text_logo.subn(
        '<img src={\'/\' + (dark ? SAREE_LOGO_WHITE_SRC : SAREE_LOGO_SRC)} alt="سريع" className="brand-logo" />',
        header, count=1
    )
    if count != 1:
        excerpt = header[:1200].replace("\n", " ")
        raise SystemExit("Could not identify the temporary text logo in header. Header excerpt: " + excerpt)

# If a header logo already exists, make its source theme-aware.
if "SAREE_LOGO_SRC" in header and "SAREE_LOGO_WHITE_SRC" in app:
    header = header.replace("src={SAREE_LOGO_SRC}", conditional)
    header = header.replace("src={SAREE_LOGO_GREEN_SRC}", conditional)

app = app[:header_match.start()] + header + app[header_match.end():]
app_path.write_text(app)

css = css_path.read_text()
css += """
/* Approved Saree3 lockup in the responsive application header. */
.brand-logo{display:block;width:clamp(112px,18vw,174px);height:48px;object-fit:contain;object-position:right center}
@media(max-width:650px){.brand-logo{width:clamp(105px,31vw,140px);height:42px}}
"""
css_path.write_text(css)
print("Applied approved green/white Saree3 lockups to the app header.")
