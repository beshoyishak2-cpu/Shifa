"""Match the agreed reference design and fix the mobile UI defects.

Applied after every other overlay patch. Covers:
  * floating admin pills no longer overlap each other
  * dialogs draw above the floating pills and the bottom nav
  * the bottom nav hides while a dialog or the address sheet is open
  * the obsolete doctors/clinics menu entries are gone
  * header wordmark, lime hero, reference search field, four coloured category
    tiles with "عرض كل", list-style store rows, four-item bottom navigation
  * the delivery address sheet and its buttons follow the same design
"""
import base64
import gzip
from pathlib import Path

_THEME_B64 = (
    "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"
    "mm0hAAA="
)
THEME_CSS = gzip.decompress(base64.b64decode("".join(_THEME_B64))).decode("utf-8")

app = Path("src/App.tsx")
css = Path("src/style.css")
text = app.read_text(encoding="utf-8")


def patch(path: Path, pairs):
    body = path.read_text(encoding="utf-8")
    for old, new in pairs:
        if old not in body:
            raise SystemExit(f"missing anchor in {path}: {old[:70]}")
        body = body.replace(old, new, 1)
    path.write_text(body, encoding="utf-8")

app = Path("src/App.tsx")
css = Path("src/style.css")
ops = Path("src/SareeOperationsPanel.tsx")
adv = Path("src/SareeAdvancedAdmin.tsx")


def patch(path: Path, pairs):
    text = path.read_text(encoding="utf-8")
    for old, new in pairs:
        if old not in text:
            raise SystemExit(f"missing anchor in {path}: {old[:70]}")
        text = text.replace(old, new, 1)
    path.write_text(text, encoding="utf-8")


patch(app, [
    # 3. drop the obsolete admin providers entry
    ("['providers','الأطباء والعيادات',Stethoscope],", ""),
    # 2. no bottom nav under an open dialog
    ("{role==='customer'&&createPortal(",
     "{role==='customer'&&!modal&&createPortal("),
])

patch(css, [
    # 2. dialogs above the floating tools and the bottom nav
    (".overlay{position:fixed;inset:0;background:#0d2b248c;z-index:20;",
     ".overlay{position:fixed;inset:0;background:#0d2b248c;z-index:2147483600;"),
    # keep toasts visible above dialogs
    (".toast{position:fixed;bottom:20px;left:50%;transform:translateX(-50%);background:#123f35;color:white;padding:12px 17px;border-radius:10px;z-index:30;",
     ".toast{position:fixed;bottom:20px;left:50%;transform:translateX(-50%);background:#123f35;color:white;padding:12px 17px;border-radius:10px;z-index:2147483645;"),
    # menu drawer uses the full phone height instead of clipping at 90vh
    (".dialog{width:min(440px,100%);background:var(--surface);border-radius:16px;padding:22px;position:relative;max-height:90vh;overflow:auto;color:var(--ink)}",
     ".dialog{width:min(440px,100%);background:var(--surface);border-radius:16px;padding:22px;position:relative;max-height:calc(100dvh - 28px);overflow:auto;color:var(--ink);overscroll-behavior:contain}"),
])

patch(adv, [
    # 1. same bottom line as the operations pill, capped width, below dialogs
    ("wrap:{position:'fixed',zIndex:2147483002,right:12,bottom:'max(88px, calc(env(safe-area-inset-bottom) + 84px))',direction:'rtl',fontFamily:'inherit',color:'#183a34'}",
     "wrap:{position:'fixed',zIndex:2147482900,right:10,bottom:'max(88px, calc(env(safe-area-inset-bottom) + 84px))',direction:'rtl',fontFamily:'inherit',color:'#183a34',maxWidth:'46vw'}"),
    ("trigger:{border:0,borderRadius:999,background:'#164e63',color:'#fff',padding:'12px 16px',fontWeight:800,boxShadow:'0 7px 24px #052f2750'}",
     "trigger:{border:0,borderRadius:999,background:'#164e63',color:'#fff',padding:'11px 14px',fontSize:12,fontWeight:800,boxShadow:'0 7px 24px #052f2750',maxWidth:'46vw',whiteSpace:'nowrap',overflow:'hidden',textOverflow:'ellipsis'}"),
    ("إدارة متقدمة · سريع", "إدارة متقدمة"),
])

patch(ops, [
    # 1. opposite corner with the same bottom line, capped width, below dialogs
    ("shell: { position: 'fixed', zIndex: 2147483001, left: 12, bottom: 'max(88px, calc(env(safe-area-inset-bottom) + 84px))', direction: 'rtl', fontFamily: 'inherit', color: '#183a34' },",
     "shell: { position: 'fixed', zIndex: 2147482901, left: 10, bottom: 'max(88px, calc(env(safe-area-inset-bottom) + 84px))', direction: 'rtl', fontFamily: 'inherit', color: '#183a34', maxWidth: '46vw' },"),
    ("trigger: { border: 0, borderRadius: 999, background: '#087f68', color: '#fff', padding: '12px 17px', fontWeight: 800, boxShadow: '0 7px 24px #052f2750' },",
     "trigger: { border: 0, borderRadius: 999, background: '#087f68', color: '#fff', padding: '11px 14px', fontSize: 12, fontWeight: 800, boxShadow: '0 7px 24px #052f2750', maxWidth: '46vw', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' },"),
])

print("Applied mobile overlap, drawer stacking and menu cleanup fixes.")

app = Path("src/App.tsx")
css = Path("src/style.css")

text = app.read_text(encoding="utf-8")


def sub(old, new, label):
    global text
    if old not in text:
        raise SystemExit(f"missing anchor: {label}")
    text = text.replace(old, new, 1)


# --- state for the category expansion
sub("const [searchKeyboardOpen,setSearchKeyboardOpen]=useState(false);",
    "const [searchKeyboardOpen,setSearchKeyboardOpen]=useState(false);const [allCats,setAllCats]=useState(false);",
    "allCats state")

# --- header: wordmark, location line, cart, bell, menu
sub('<button className="icon-btn" aria-label="فتح القائمة" onClick={()=>setModal(\'menu\')}><Menu/></button>'
    '<div className="brand"><img src={\'/\' + (dark ? SAREE_LOGO_WHITE_SRC : SAREE_LOGO_SRC)} alt="سريع" className="brand-logo" />'
    '<small>كل خدمات ملوى في مكان واحد</small></div>'
    '<div className="head-actions"><button className="icon-btn" aria-label="الإشعارات" '
    'onClick={()=>notify(\'الإشعارات الفعلية تحتاج ربط FCM وخادم الإرسال\')}><Bell/></button></div>',
    '<div className="brand"><b>سريع<span className="brand-dot">.</span></b><small>الوصول إلى: ملوى</small></div>'
    '<div className="head-actions">'
    '{role===\'customer\'&&<button className="icon-btn" aria-label="السلة" onClick={()=>{setTab(\'cart\');setSelectedStore(null)}}>'
    '<ShoppingCart size={20}/>{count>0&&<i className="head-cart-badge">{count>99?\'99+\':count}</i>}</button>}'
    '<button className="icon-btn" aria-label="الإشعارات" '
    'onClick={()=>notify(\'الإشعارات الفعلية تحتاج ربط FCM وخادم الإرسال\')}><Bell/></button>'
    '<button className="icon-btn" aria-label="فتح القائمة" onClick={()=>setModal(\'menu\')}><Menu/></button>'
    '</div>',
    "header")

# --- hero: reference copy, chips, whole card opens the catalogue
sub('<div className="saree-home-promo">',
    '<div className="saree-home-promo" role="button" tabIndex={0} onClick={()=>setTab(\'search\')}>',
    "hero wrapper")
sub('<span className="saree-promo-eyebrow">سريع · ملوى</span><b>طلبك أقرب مما تتخيل</b>'
    '<small>مطاعم ومتاجر وخدمات يومية في مكان واحد</small>'
    '<button onClick={()=>setTab(\'search\')}>اكتشف المتاجر <span aria-hidden="true">←</span></button>',
    '<b>كل اللي تحتاجه يوصل لحد بابك</b>'
    '<small>مطاعم، بقالة، خضار، ومشاوير داخل ملوى</small>'
    '<div className="saree-promo-chips"><span>خدمة عند الاستلام</span><span>مندوبين محليين</span></div>',
    "hero copy")

# --- categories: reference heading plus "عرض كل", four tiles by default
sub('<div className="service-grid">',
    '<div className="section-title"><h2>التصنيفات</h2>'
    '<button className="link-more" onClick={()=>setAllCats(v=>!v)}>{allCats?\'أقل\':\'عرض كل\'}</button></div>'
    '<div className="service-grid">',
    "categories heading")
sub("] as {id:Service;label:string;icon:string}[]).map(x=>",
    "] as {id:Service;label:string;icon:string}[])"
    ".filter(x=>allCats||['restaurant','vegetables','grocery','errand'].includes(x.id))"
    ".sort((a,b)=>(['restaurant','vegetables','grocery','errand'].indexOf(a.id)+1||99)-"
    "(['restaurant','vegetables','grocery','errand'].indexOf(b.id)+1||99)).map(x=>",
    "categories filter")
sub("className={service===x.id?'service active':'service'}",
    "data-service={x.id} className={service===x.id?'service active':'service'}",
    "category data attribute")
sub("<div className=\"search\"><Search/><input placeholder=\"ابحث عن متجر أو خدمة في ملوى...\" value={query} "
    "onChange={e=>setQuery(e.target.value)}/><button onClick={()=>setQuery('')}><X size={18}/></button></div>",
    "<div className=\"search\"><Search/><input placeholder=\"ابحث عن مطعم أو منتج\" value={query} "
    "onChange={e=>setQuery(e.target.value)}/>{query&&<button onClick={()=>setQuery('')}><X size={18}/></button>}</div>",
    "search field")
sub("{service==='all'?'أماكن قريبة منك':STORE_TYPES[service]?.label||'كل المتاجر'}",
    "{service==='all'?'الأقرب إليك':STORE_TYPES[service]?.label||'كل المتاجر'}",
    "home store heading")
sub("<span className=\"muted\">{visibleStores.length} متجر</span></div><div className=\"store-grid\">"
    "{visibleStores.length===0?",
    "<button className=\"link-more\" onClick={()=>setTab('search')}>عرض كل</button></div>"
    "<div className=\"store-grid\">{visibleStores.length===0?",
    "home store count to عرض كل")

# --- legacy doctors directory entry out of the customer menu
sub("['doctors','دليل الأطباء',Stethoscope],", "", "customer doctors entry")

# --- store list heading
sub("المتاجر المطابقة</h2>", "الأقرب إليك</h2>", "store heading")

# --- bottom nav: four reference items, cart and search reachable elsewhere
sub('<button className={tab===\'search\'?\'active\':\'\'} aria-current={tab===\'search\'?\'page\':undefined} '
    'onClick={()=>{setTab(\'search\');setSelectedStore(null)}}><Search size={20}/><span>بحث</span></button>',
    '<button className={tab===\'errand\'?\'active\':\'\'} aria-current={tab===\'errand\'?\'page\':undefined} '
    'onClick={()=>{setTab(\'errand\');setSelectedStore(null)}}><Bike size={20}/><span>مشاوير</span></button>',
    "nav search to errand")
sub('<button className={tab===\'cart\'?\'active\':\'\'} aria-current={tab===\'cart\'?\'page\':undefined} '
    'onClick={()=>{setTab(\'cart\');setSelectedStore(null)}}><span className="nav-cart-icon"><ShoppingCart size={20}/>'
    '{count>0&&<i key={count} className="nav-cart-badge">{count>99?\'99+\':count}</i>}</span><span>السلة</span></button>',
    '',
    "nav cart removed")

app.write_text(text, encoding="utf-8")

# --- keep the source smoke test aligned with the reference hero copy
tests = Path("tests/source-smoke.test.cjs")
tt = tests.read_text(encoding="utf-8")
old_assert = "assert.ok(source.includes('طلبك أقرب مما تتخيل'));"
if old_assert in tt:
    tt = tt.replace(old_assert, "assert.ok(source.includes('كل اللي تحتاجه يوصل لحد بابك'));")
    tests.write_text(tt, encoding="utf-8")

theme = THEME_CSS

if "Sari3 agreed design" not in css.read_text(encoding="utf-8"):
    css.write_text(css.read_text(encoding="utf-8").rstrip() + "\n" + theme, encoding="utf-8")

print("Applied reference design: header, hero, categories, store rows, four-item nav.")

