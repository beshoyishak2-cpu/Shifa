"""Splash screen on the agreed design: white canvas, lime mark, no bottom nav."""
from pathlib import Path

CSS = Path("src/style.css")
LOC = Path("src/LocationSystem.tsx")

# the Leaflet default marker points at marker-icon.png, which 404s inside the
# bundled app and shows a broken image with alt text; use an inline pin instead
body = LOC.read_text(encoding="utf-8")
old = "marker=L.marker([lat,lng],{draggable:true})"
new = ("marker=L.marker([lat,lng],{draggable:true,icon:L.divIcon({className:'s3-loc-pin',"
       "html:'<span></span>',iconSize:[26,26],iconAnchor:[13,26]})})")
if old in body:
    LOC.write_text(body.replace(old, new, 1), encoding="utf-8")
elif "s3-loc-pin" not in body:
    raise SystemExit("marker anchor missing")

EXTRA = """
/* splash: white canvas, lime badge, no white plate behind the logo, no nav */
.saree-splash{background:#fff;color:#141B0D;z-index:2147483647}
.saree-splash-brand{background:#F1FAD3;border-radius:34px;box-shadow:0 14px 40px #141b0d14}
.saree-splash-brand img{mix-blend-mode:multiply}
.saree-splash-track{border-bottom-color:#CFDDB0}
.saree-splash-caption{color:#5C6650}
.saree-splash-wordmark{color:#141B0D}
body:has(.saree-splash) .mobile-bottom-nav{display:none!important}

/* map pin drawn inline so no marker image can fail to load */
.s3-loc-pin{background:transparent;border:0}
.s3-loc-pin span{display:block;width:22px;height:22px;border-radius:50% 50% 50% 0;transform:rotate(-45deg);background:#6FCB00;border:3px solid #fff;box-shadow:0 4px 10px #141b0d33}
.leaflet-container{background:#EFF3E8}

/* store thumbnails: readable placeholder instead of clipped text */
.store-icon span{font-size:12px;font-weight:700;color:#4E9A00;line-height:1.25;padding:2px 4px;text-align:center;overflow:hidden;white-space:normal;word-break:break-word}
"""

style = CSS.read_text(encoding="utf-8")
if "splash: white canvas" not in style:
    CSS.write_text(style.rstrip() + "\n" + EXTRA, encoding="utf-8")

print("Applied splash theme.")
