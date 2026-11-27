#!/usr/bin/env python3
"""Generate native Saree3 launcher icons and splash assets from approved PNGs."""
from __future__ import annotations
import json
from pathlib import Path
try:
    from PIL import Image
except ImportError as exc:
    raise SystemExit("Pillow is required. Install it with: python3 -m pip install Pillow") from exc
ROOT=Path.cwd()
ICON=ROOT/"public/brand/sari3-icon.png"
WHITE=ROOT/"public/brand/sari3-lockup-white.png"
GREEN=ROOT/"public/brand/sari3-lockup-green.png"
MAGIC=b"\x89PNG\r\n\x1a\n"
def load_png(path):
    if not path.is_file(): raise SystemExit(f"Brand asset is missing: {path.relative_to(ROOT)}")
    try:
        with path.open("rb") as f:
            if f.read(8)!=MAGIC: raise SystemExit(f"Brand asset is not PNG (invalid signature): {path.relative_to(ROOT)}")
        im=Image.open(path); im.load()
        if im.format!="PNG": raise SystemExit(f"Brand asset is not PNG: {path.relative_to(ROOT)}")
        return im.convert("RGBA")
    except SystemExit: raise
    except Exception as e: raise SystemExit(f"Cannot read PNG asset {path.relative_to(ROOT)}: {e}") from e
def save(im,path):
    path.parent.mkdir(parents=True,exist_ok=True); im.save(path,format="PNG",optimize=True)
def contain(src,size,fraction=1.0):
    out=Image.new("RGBA",size,(0,0,0,0)); im=src.copy()
    im.thumbnail((max(1,round(size[0]*fraction)),max(1,round(size[1]*fraction))),Image.Resampling.LANCZOS)
    out.alpha_composite(im,((size[0]-im.width)//2,(size[1]-im.height)//2)); return out
def isolate_foreground(icon):
    """Remove edge-connected green background while preserving enclosed green artwork."""
    from collections import deque
    from PIL import ImageChops
    rgb=icon.convert("RGB"); pixels=rgb.load(); width,height=rgb.size
    seen=bytearray(width*height); queue=deque()
    def is_bg(x,y):
        r,g,b=pixels[x,y]
        return g>r*1.12 and g>b*1.12 and g-r>28 and g-b>22
    def add(x,y):
        i=y*width+x
        if not seen[i] and is_bg(x,y):
            seen[i]=1; queue.append((x,y))
    for x in range(width): add(x,0); add(x,height-1)
    for y in range(height): add(0,y); add(width-1,y)
    while queue:
        x,y=queue.popleft()
        if x: add(x-1,y)
        if x+1<width: add(x+1,y)
        if y: add(x,y-1)
        if y+1<height: add(x,y+1)
    mask=Image.new("L",(width,height),255); mp=mask.load()
    for y in range(height):
        row=y*width
        for x in range(width):
            if seen[row+x]: mp[x,y]=0
    out=icon.copy()
    out.putalpha(ImageChops.multiply(out.getchannel("A"),mask))
    if out.getbbox() is None: raise SystemExit("Could not isolate scooter artwork from green icon background.")
    return out

def generate_android(icon,bg,white):
    res=ROOT/"android/app/src/main/res"
    for density,px in {"mdpi":48,"hdpi":72,"xhdpi":96,"xxhdpi":144,"xxxhdpi":192}.items():
        save(icon.resize((px,px),Image.Resampling.LANCZOS),res/f"mipmap-{density}/ic_launcher.png")
    foreground_art=isolate_foreground(icon)
    for density,px in {"mdpi":108,"hdpi":162,"xhdpi":216,"xxhdpi":324,"xxxhdpi":432}.items():
        save(contain(foreground_art,(px,px),.66),res/f"mipmap-{density}/ic_launcher_foreground.png")
    p=res/"mipmap-anydpi-v26"; p.mkdir(parents=True,exist_ok=True)
    (p/"ic_launcher.xml").write_text('<?xml version="1.0" encoding="utf-8"?>\n<adaptive-icon xmlns:android="http://schemas.android.com/apk/res/android">\n    <background android:drawable="@color/ic_launcher_background" />\n    <foreground android:drawable="@mipmap/ic_launcher_foreground" />\n</adaptive-icon>\n',encoding="utf-8")
    p=res/"values"; p.mkdir(parents=True,exist_ok=True)
    (p/"ic_launcher_background.xml").write_text('<?xml version="1.0" encoding="utf-8"?>\n<resources>\n    <color name="ic_launcher_background">'+bg+'</color>\n</resources>\n',encoding="utf-8")
    splash=Image.new("RGBA",(2732,2732),bg); splash.alpha_composite(contain(white,(2732,2732),.62))
    save(splash,res/"drawable/splash.png")
def generate_ios(icon,bg,white):
    assets=ROOT/"ios/App/App/Assets.xcassets"; appicon=assets/"AppIcon.appiconset"; appicon.mkdir(parents=True,exist_ok=True)
    slots=[("20x20","2x",40),("20x20","3x",60),("29x29","2x",58),("29x29","3x",87),("40x40","2x",80),("40x40","3x",120),("60x60","2x",120),("60x60","3x",180),("76x76","1x",76),("76x76","2x",152),("83.5x83.5","2x",167),("1024x1024","1x",1024)]
    images=[]
    for logical,scale,px in slots:
        filename=f"AppIcon-{logical.replace('.','_')}-{scale}.png"
        save(icon.resize((px,px),Image.Resampling.LANCZOS),appicon/filename)
        images.append({"filename":filename,"idiom":"universal","platform":"ios","size":logical,"scale":scale})
    (appicon/"Contents.json").write_text(json.dumps({"images":images,"info":{"author":"xcode","version":1}},indent=2)+"\n",encoding="utf-8")
    splashset=assets/"Splash.imageset"; splashset.mkdir(parents=True,exist_ok=True)
    splash=Image.new("RGBA",(2732,2732),bg); splash.alpha_composite(contain(white,(2732,2732),.62))
    save(splash,splashset/"splash.png")
    (splashset/"Contents.json").write_text(json.dumps({"images":[{"filename":"splash.png","idiom":"universal"}],"info":{"author":"xcode","version":1}},indent=2)+"\n",encoding="utf-8")
icon=load_png(ICON); white=load_png(WHITE); load_png(GREEN)
bg="#{:02X}{:02X}{:02X}".format(*icon.getpixel((0,0))[:3])
android_present=(ROOT/"android/app").is_dir()
ios_present=(ROOT/"ios/App/App").is_dir()
if not android_present and not ios_present:
    raise SystemExit("No native platform found. Run npx cap add android or npx cap add ios before icon generation.")
if android_present:
    generate_android(icon,bg,white)
    print("Generated Android mipmap/adaptive icons and drawable splash.")
if ios_present:
    generate_ios(icon,bg,white)
    print("Generated iOS AppIcon.appiconset and Splash.imageset.")
print(f"Brand asset generation complete; background={bg}")
