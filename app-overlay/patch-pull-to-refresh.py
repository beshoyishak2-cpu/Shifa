"""Pull-to-refresh on the main screens.

A downward swipe from the top of the page shows an indicator and refreshes the
data: the admin panels re-run their own loader, other screens reload the app so
every list refetches from the server. Nothing is written, only re-read.
"""
from pathlib import Path

APP = Path("src/App.tsx")
OPS = Path("src/SareeOperationsPanel.tsx")
ADV = Path("src/SareeAdvancedAdmin.tsx")
CSS = Path("src/style.css")

COMPONENT = '''
function SareePullToRefresh(){
  const [pull,setPull]=useState(0);const [busy,setBusy]=useState(false);
  const dist=useRef(0);const active=useRef(false);const startY=useRef(0);
  useEffect(()=>{
    const blocked=()=>window.scrollY>0||!!document.querySelector('.overlay,.s3-loc-overlay');
    const onStart=(e:any)=>{if(blocked())return;const t=e.touches&&e.touches[0];if(!t)return;startY.current=t.clientY;active.current=true;};
    const onMove=(e:any)=>{if(!active.current)return;const t=e.touches&&e.touches[0];if(!t)return;
      const d=t.clientY-startY.current;if(d<=0){dist.current=0;setPull(0);return;}
      dist.current=Math.min(110,d*0.55);setPull(dist.current);
      if(d>18&&e.cancelable)e.preventDefault();};
    const onEnd=()=>{if(!active.current)return;active.current=false;const p=dist.current;dist.current=0;setPull(0);
      if(p<58)return;setBusy(true);let handled=false;
      const mark=()=>{handled=true;};
      window.addEventListener('saree:soft-refresh',mark,{once:true});
      window.dispatchEvent(new Event('saree:soft-refresh'));
      window.setTimeout(()=>{window.removeEventListener('saree:soft-refresh',mark);
        if(!handled){window.location.reload();return;}setBusy(false);},450);};
    window.addEventListener('touchstart',onStart,{passive:true});
    window.addEventListener('touchmove',onMove,{passive:false});
    window.addEventListener('touchend',onEnd);
    return ()=>{window.removeEventListener('touchstart',onStart);window.removeEventListener('touchmove',onMove);window.removeEventListener('touchend',onEnd);};
  },[]);
  const shown=pull>6||busy;
  return <div className={'saree-ptr'+(shown?' show':'')+(busy?' busy':'')} style={{height:busy?52:pull}} aria-hidden="true"><span>{busy?'↻':'↓'}</span></div>;
}

export default function App(){'''

text = APP.read_text(encoding="utf-8")
if "SareePullToRefresh" not in text:
    if "export default function App(){" not in text:
        raise SystemExit("App component anchor missing")
    if "import { useEffect, useMemo, useState } from 'react'" not in text:
        raise SystemExit("react import anchor missing")
    text = text.replace("import { useEffect, useMemo, useState } from 'react'",
                        "import { useEffect, useMemo, useRef, useState } from 'react'", 1)
    text = text.replace("export default function App(){", COMPONENT.lstrip("\n"), 1)
    if "<SareeSplash/><LocationSystem/>" not in text:
        raise SystemExit("splash anchor missing")
    text = text.replace("<SareeSplash/><LocationSystem/>", "<SareePullToRefresh/><SareeSplash/><LocationSystem/>", 1)
    APP.write_text(text, encoding="utf-8")

LISTENER = '''
  useEffect(()=>{const h=()=>{void load();};window.addEventListener('saree:soft-refresh',h);return()=>window.removeEventListener('saree:soft-refresh',h);},[]);
'''

for path, anchor in ((OPS, "  useEffect(() => {"), (ADV, " useEffect(()=>{if(!client)return;client.auth.getSession()")):
    body = path.read_text(encoding="utf-8")
    if "saree:soft-refresh" in body:
        continue
    if anchor not in body:
        raise SystemExit(f"listener anchor missing in {path}")
    body = body.replace(anchor, LISTENER + anchor, 1)
    path.write_text(body, encoding="utf-8")

EXTRA = """
/* pull to refresh indicator */
.saree-ptr{display:flex;align-items:center;justify-content:center;height:0;overflow:hidden;transition:height .18s ease;background:#fff;color:#4E9A00}
.saree-ptr.show{height:auto}
.saree-ptr span{display:grid;place-items:center;width:30px;height:30px;border-radius:50%;background:#F1FAD3;color:#4E9A00;font-size:15px;font-weight:800}
.saree-ptr.busy span{animation:saree-ptr-spin .9s linear infinite}
@keyframes saree-ptr-spin{from{transform:rotate(0)}to{transform:rotate(360deg)}}
"""
style = CSS.read_text(encoding="utf-8")
if "pull to refresh indicator" not in style:
    CSS.write_text(style.rstrip() + "\n" + EXTRA, encoding="utf-8")

print("Added pull-to-refresh.")
