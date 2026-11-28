from pathlib import Path
import re

app_path = Path("src/App.tsx")
css_path = Path("src/style.css")
app = app_path.read_text()
css = css_path.read_text()

# One replaceable asset variable shared by the splash wordmark/icon treatment.
if "const SAREE_LOGO_SRC" not in app:
    marker = "type Role = 'customer' | 'merchant' | 'driver' | 'admin';"
    if marker not in app:
        raise SystemExit("Could not locate app role declaration for splash component")
    splash = r"""
const SAREE_LOGO_SRC = ''; // ضع مسار ملف الشعار هنا لاحقًا، ويُستخدم في شاشة البداية
function SareeSplash(){
 const [visible,setVisible]=useState(true);
 useEffect(()=>{
  const reduce=window.matchMedia?.('(prefers-reduced-motion: reduce)').matches;
  const timer=window.setTimeout(()=>setVisible(false),reduce?650:2350);
  return()=>window.clearTimeout(timer);
 },[]);
 if(!visible)return null;
 return <div className="saree-splash" role="status" aria-label="جاري فتح سريع">
  <div className="saree-splash-brand">
   {SAREE_LOGO_SRC?<img src={SAREE_LOGO_SRC} alt="سريع"/>:<span className="saree-splash-wordmark">سريع</span>}
  </div>
  <div className="saree-splash-track"><span className="saree-splash-scooter">🛵</span></div>
  <span className="saree-splash-caption">كل خدمات ملوي في مكان واحد</span>
  <span className="saree-splash-dots"><i/><i/><i/></span>
 </div>;
}
"""
    app = app.replace(marker, splash + "\n" + marker, 1)

# Mount the overlay immediately after the app header; fixed positioning covers the app.
if "<SareeSplash/>" not in app:
    header_end = app.find("</header>")
    if header_end < 0:
        raise SystemExit("Could not find app header to mount splash")
    header_end += len("</header>")
    app = app[:header_end] + "<SareeSplash/>" + app[header_end:]

# Track the actual remote catalog fetch and show placeholders instead of a blank grid.
state_anchor = " const [role,setRole]=useState<Role>('customer'),[tab,setTabState]=useState('home')"
if "const [catalogLoading,setCatalogLoading]" not in app:
 if state_anchor not in app:
  raise SystemExit("Could not locate app state for catalog loading")
 app = app.replace(state_anchor, " const [catalogLoading,setCatalogLoading]=useState(false);\n" + state_anchor, 1)
load_start = "if(!supabase||!signedInPhone)return;let alive=true;(async()=>{const [{data:merchantRows,error},{data:categoryRows}]"
if load_start in app and "setCatalogLoading(true)" not in app:
 app = app.replace(load_start, "if(!supabase||!signedInPhone)return;let alive=true;setCatalogLoading(true);(async()=>{const [{data:merchantRows,error},{data:categoryRows}]", 1)
load_end = "})();return()=>{alive=false}},[signedInPhone]);"
if load_end in app:
 app = app.replace(load_end, "})().finally(()=>{if(alive)setCatalogLoading(false)});return()=>{alive=false}},[signedInPhone]);", 1)

# Home-only promo and repeat-order shortcuts; no discount or price is fabricated.
if "طلبك أقرب مما تتخيل" not in app:
    m = re.search(r"\{role\s*===\s*'customer'\s*&&\s*tab\s*===\s*'home'\s*&&\s*<>", app)
    if not m:
        raise SystemExit("Could not locate customer home screen section for promo banner")
    insert = r"""
{catalogLoading&&<div className="saree-catalog-skeleton" aria-label="جار تحميل المتاجر والمنتجات"><div className="saree-skeleton-card"><i/><span/><span/></div><div className="saree-skeleton-card"><i/><span/><span/></div><div className="saree-skeleton-card"><i/><span/><span/></div></div>}<div className="saree-home-promo">
 <div className="saree-promo-copy"><span className="saree-promo-eyebrow">سريع · ملوي</span><b>طلبك أقرب مما تتخيل</b><small>مطاعم ومتاجر وخدمات يومية في مكان واحد</small><button onClick={()=>setTab('search')}>اكتشف المتاجر <span>←</span></button></div>
 <div className="saree-promo-art" aria-hidden="true"><span>🛍️</span><i>✦</i></div>
</div>
<div className="saree-repeat-row"><div><b>اطلب تاني</b><small>راجع طلباتك السابقة وكرر طلبك بسهولة</small></div><button onClick={()=>setTab('orders')}>طلباتي <span>←</span></button></div>
"""
    pos = m.end()
    app = app[:pos] + insert + app[pos:]

if 'className="saree-home-promo"' not in app:
    raise SystemExit("Home promo banner was not inserted")
if "اطلب تاني" not in app:
    raise SystemExit("Repeat-order shortcut was not inserted below the home promo")

# Re-mount the cart badge when its count changes, so the pop animation restarts.
app = app.replace('<i className="nav-cart-badge">', '<i key={count} className="nav-cart-badge">')

app_path.write_text(app)

css += r"""

/* Saree polish layer — scoped additions, no changes to business logic */
.saree-catalog-skeleton{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:12px;margin:0 0 16px}.saree-skeleton-card{display:grid;grid-template-columns:62px 1fr;grid-template-rows:18px 14px;gap:8px 11px;align-items:center;padding:12px;border:1px solid var(--line);border-radius:16px;background:var(--surface)}.saree-skeleton-card i{grid-row:1/3;width:62px;height:62px;border-radius:13px;background:linear-gradient(100deg,var(--line) 20%,color-mix(in srgb,var(--green) 12%,var(--surface)) 45%,var(--line) 70%);background-size:220% 100%;animation:saree-skeleton 1.2s ease-in-out infinite}.saree-skeleton-card span{height:11px;border-radius:8px;background:var(--line)}.saree-skeleton-card span:last-child{width:65%}.saree-splash{position:fixed;inset:0;z-index:9999;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:20px;background:var(--green,#078568);color:#fff;animation:saree-splash-in .42s ease-out both}
.saree-splash-brand{width:124px;height:124px;display:grid;place-items:center;border-radius:34px;background:#ffffff18;box-shadow:0 18px 48px #003e2d30;animation:saree-logo-in .72s cubic-bezier(.2,.8,.2,1) both}
.saree-splash-brand img{max-width:82%;max-height:82%;object-fit:contain}
.saree-splash-wordmark{font-size:42px;font-weight:950;letter-spacing:-2px}
.saree-splash-track{position:relative;width:190px;height:34px;border-bottom:2px solid #ffffff65;overflow:hidden}
.saree-splash-scooter{position:absolute;bottom:3px;left:-38px;font-size:27px;animation:saree-scooter-run 1.65s cubic-bezier(.4,0,.2,1) .35s both}
.saree-splash-caption{font-size:12px;font-weight:650;letter-spacing:.2px;opacity:.9}
.saree-splash-dots{display:flex;gap:6px}.saree-splash-dots i{width:5px;height:5px;border-radius:50%;background:#fff;opacity:.45;animation:saree-dot .8s ease-in-out infinite alternate}.saree-splash-dots i:nth-child(2){animation-delay:.15s}.saree-splash-dots i:nth-child(3){animation-delay:.3s}
@keyframes saree-splash-in{from{opacity:0}to{opacity:1}}
@keyframes saree-logo-in{from{opacity:0;transform:translateY(14px) scale(.88)}to{opacity:1;transform:translateY(0) scale(1)}}
@keyframes saree-scooter-run{0%{left:-38px;transform:translateY(0) rotate(-2deg)}25%{transform:translateY(-3px) rotate(1deg)}70%{transform:translateY(0) rotate(-1deg)}100%{left:calc(100% + 38px);transform:translateY(-2px)}}
@keyframes saree-dot{to{opacity:1;transform:translateY(-3px)}}
@keyframes saree-page-in{from{opacity:.65;transform:translateY(7px)}to{opacity:1;transform:translateY(0)}}
@keyframes saree-cart-pop{0%{transform:scale(.65)}65%{transform:scale(1.22)}100%{transform:scale(1)}}
.saree-home-promo{position:relative;display:flex;align-items:center;justify-content:space-between;gap:12px;min-height:148px;margin:0 0 20px;padding:20px 22px;overflow:hidden;border-radius:22px;background:linear-gradient(115deg,#087b5d 0%,#0b9b70 58%,#37b77d 100%);color:#fff;box-shadow:0 10px 24px #087b5d20}
.saree-promo-copy{position:relative;z-index:1;display:flex;flex-direction:column;align-items:flex-start;gap:7px}.saree-promo-eyebrow{font-size:10px;font-weight:850;opacity:.82}.saree-promo-copy>b{font-size:21px;font-weight:900;line-height:1.35}.saree-promo-copy>small{font-size:11px;opacity:.9}.saree-promo-copy>button,.saree-repeat-row>button{display:flex;align-items:center;gap:9px;margin-top:5px;padding:9px 13px;border:0;border-radius:11px;background:#fff;color:#087b5d;font:inherit;font-size:11px;font-weight:850;cursor:pointer}.saree-promo-art{position:relative;display:grid;place-items:center;flex:none;width:105px;height:105px;border-radius:50%;background:#ffffff20}.saree-promo-art>span{font-size:54px;filter:drop-shadow(0 7px 8px #004b3633);transform:rotate(-8deg)}.saree-promo-art>i{position:absolute;top:8px;right:8px;font-size:25px;font-style:normal;color:#d5ff86}
.saree-repeat-row{display:flex;align-items:center;justify-content:space-between;gap:12px;margin:0 0 20px;padding:13px 15px;border:1px solid var(--line);border-radius:16px;background:var(--surface);box-shadow:0 4px 14px #00000007}.saree-repeat-row>div{display:flex;flex-direction:column;gap:4px}.saree-repeat-row b{font-size:13px}.saree-repeat-row small{font-size:10px;color:var(--muted)}.saree-repeat-row>button{margin:0;background:color-mix(in srgb,var(--green) 10%,var(--surface));color:var(--green);white-space:nowrap}
@media(prefers-reduced-motion:no-preference){.app main>section,.app .layout>section{animation:saree-page-in .22s ease-out both}.nav-cart-badge{animation:saree-cart-pop .34s cubic-bezier(.2,.8,.2,1) both}.saree-home-promo{animation:saree-page-in .3s ease-out both}}
button,.store-card,.product,.category-card,.service-card{transition:transform .16s ease,box-shadow .16s ease,background-color .16s ease}
button:active,.store-card:active,.product:active,.category-card:active,.service-card:active{transform:scale(.975)}
.store-card,.product,.category-card,.service-card{border-radius:17px;box-shadow:0 4px 15px #00000008}
.store-icon,.product-art{border-radius:15px;overflow:hidden;background-color:color-mix(in srgb,var(--green) 8%,var(--surface))}
.store-icon:empty,.product-art:empty{background-image:linear-gradient(100deg,transparent 20%,#ffffff70 45%,transparent 70%);background-size:220% 100%;animation:saree-skeleton 1.35s ease-in-out infinite}
@keyframes saree-skeleton{to{background-position-x:-220%}}
@media(prefers-reduced-motion:reduce){.saree-splash,.saree-splash-brand,.saree-splash-scooter,.saree-splash-dots i,.saree-home-promo,.app main>section,.app .layout>section,.nav-cart-badge{animation:none!important;transition:none!important}.saree-splash-scooter{left:calc(100% - 30px)}button,.store-card,.product,.category-card,.service-card{transition:none!important}}
@media(max-width:700px){.saree-home-promo{min-height:138px;padding:17px 16px;border-radius:18px}.saree-promo-copy>b{font-size:18px}.saree-promo-copy>small{max-width:230px;line-height:1.6}.saree-promo-art{width:82px;height:82px}.saree-promo-art>span{font-size:43px}.saree-repeat-row{padding:12px;border-radius:14px}}
"""
css_path.write_text(css)
print("Applied Saree visual polish layer.")
