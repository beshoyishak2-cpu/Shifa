"""Build 310 fixes: ops panel width, hidden pull-to-refresh, category empty state,
safe area, partner label, new home hero copy and illustration."""
from pathlib import Path
import re

APP = Path('src/App.tsx')
CSS = Path('src/style.css')
OPS = Path('src/SareeOperationsPanel.tsx')
SVG = Path('public/brand/saree-hero-illustration.svg')


def need(text, old, label):
    if old not in text:
        raise SystemExit('missing anchor: ' + label)
    return text.replace(old, new=None) if False else text.replace(old, old, 1)


def sub(text, old, new, label):
    if old not in text:
        raise SystemExit('missing anchor: ' + label)
    return text.replace(old, new, 1)


# ---------------------------------------------------------------- App.tsx
app = APP.read_text(encoding='utf-8')

# 1. pull-to-refresh indicator must not render unless the user is pulling
ptr_pat = re.compile(r"return <div className=\{'saree-ptr'.*?</div>;", re.S)
if not ptr_pat.search(app):
    raise SystemExit('missing anchor: ptr return')
app = ptr_pat.sub(
    "if(!shown)return null;\n"
    "  return <div className={'saree-ptr'+(busy?' busy':'')} style={{height:busy?52:Math.max(0,pull)}} aria-hidden=\"true\"><span>{busy?'↻':'↓'}</span></div>;",
    app, count=1)

# 2. hero copy: eyebrow, two-line title with lime accent, check chips
old_hero = ('<div className="saree-promo-copy"><b>كل اللي تحتاجه يوصل لحد بابك</b>'
            '<small>مطاعم، بقالة، خضار، ومشاوير داخل ملوى</small>'
            '<div className="saree-promo-chips"><span>خدمة عند الاستلام</span><span>مندوبين محليين</span></div></div>')
check = ('<svg viewBox="0 0 24 24" aria-hidden="true" fill="none" stroke="currentColor" strokeWidth="3.2" '
         'strokeLinecap="round" strokeLinejoin="round"><path d="M5 12.5l4.5 4.5L19 7.5"/></svg>')
new_hero = ('<div className="saree-promo-copy"><span className="saree-promo-eyebrow">أهلاً بك في سريع</span>'
            '<b>كل اللي تحتاجه<br/><em>يوصلك لحد بابك</em></b>'
            '<small>مطاعم، بقالة، خضار، ومشاوير داخل ملوى</small>'
            '<div className="saree-promo-chips"><span>' + check + 'دفع عند الاستلام</span>'
            '<span>' + check + 'مندوبين محليين</span></div></div>')
app = sub(app, old_hero, new_hero, 'hero copy')

# 3. category section: visible, actionable empty state
old_empty = ('<Empty title="لا توجد متاجر أو منتجات منشورة بعد" '
             'hint="لسه الإدارة ما أضافتش متاجر ومنتجات لملوى. تقدر تستخدم خدمة المشوار، وسيظهر التسوق هنا بعد إضافة أول متجر."/>')
new_empty = ('<div className="saree-empty-cat"><Package size={28}/>'
             '<b>لا توجد متاجر في {service===\'all\'?\'ملوى\':(STORE_TYPES[service]?.label||\'هذا القسم\')} بعد</b>'
             '<small>جرّب قسم تاني، أو شوف كل المتاجر المتاحة دلوقتي في ملوى.</small>'
             '{service!==\'all\'&&<button onClick={()=>setService(\'all\')}>عرض كل المتاجر</button>}</div>')
app = sub(app, old_empty, new_empty, 'category empty state')

# 4. partner label: no pharmacies in Sari3
app = app.replace('التجار والصيدليات', 'التجار والمتاجر')

# 5. demo data: a vegetables store with products so the category is not empty
veg_store = ("{id:'demo-veg',name:'خيرات ملوى',type:'vegetables',area:'السوق القديم – ملوى',rating:4.6,"
             "eta:'20–35 دقيقة',fee:18,min:30,open:true,desc:'خضار وفاكهة طازجة',icon:'خضار'},")
m = re.search(r"const SAREE_DEMO_STORES:StoreItem\[\]=\[\n(.*?)\];", app, re.S)
if not m:
    raise SystemExit('missing anchor: demo stores array')
if 'demo-veg' not in m.group(1):
    app = app[:m.end(1)] + ',\n' + veg_store + app[m.end(1):]

veg_products = [
    "{id:'demo-v1',storeId:'demo-veg',name:'طماطم بلدي',description:'كيلو طماطم طازجة',price:14,unit:'كيلو',emoji:'خضار',category:'خضار',available:true}",
    "{id:'demo-v2',storeId:'demo-veg',name:'بطاطس',description:'كيلو بطاطس',price:12,unit:'كيلو',emoji:'خضار',category:'خضار',available:true}",
    "{id:'demo-v3',storeId:'demo-veg',name:'موز',description:'كيلو موز',price:24,unit:'كيلو',emoji:'فاكهة',category:'فاكهة',available:true}",
    "{id:'demo-v4',storeId:'demo-veg',name:'برتقال',description:'كيلو برتقال عصير',price:18,unit:'كيلو',emoji:'فاكهة',category:'فاكهة',available:true}",
]
m = re.search(r"const SAREE_DEMO_PRODUCTS:Product\[\]=\[\n(.*?)\];", app, re.S)
if not m:
    raise SystemExit('missing anchor: demo products array')
if 'demo-v1' not in m.group(1):
    app = app[:m.end(1)] + ',\n' + ',\n'.join(veg_products) + ',' + app[m.end(1):]

APP.write_text(app, encoding='utf-8')

# --------------------------------------------------- tests stay in sync
TEST = Path('tests/source-smoke.test.cjs')
t = TEST.read_text(encoding='utf-8')
t = sub(t, "assert.ok(app().includes('لا توجد متاجر أو منتجات منشورة بعد'));",
        "assert.ok(app().includes('لا توجد متاجر في'));", 'test: empty marketplace')
t = sub(t, "assert.ok(source.includes('كل اللي تحتاجه يوصل لحد بابك'));",
        "assert.ok(source.includes('كل اللي تحتاجه'));\n  assert.ok(source.includes('يوصلك لحد بابك'));", 'test: hero title')
t = sub(t, "assert.ok(!source.includes('أهلاً بك في سريع'));",
        "assert.ok(source.includes('أهلاً بك في سريع'));", 'test: hero eyebrow')
TEST.write_text(t, encoding='utf-8')

# ------------------------------------------------- SareeOperationsPanel.tsx
ops = OPS.read_text(encoding='utf-8')
old_shell = ("    shell: { position: 'fixed', zIndex: 2147482901, left: 10, bottom: "
             "'max(88px, calc(env(safe-area-inset-bottom) + 84px))', direction: 'rtl', fontFamily: 'inherit', "
             "color: '#141B0D', maxWidth: '46vw' },")
new_shell = ("    shell: { position: 'fixed', zIndex: 2147482901, left: 10, right: 'auto', bottom: "
             "'max(88px, calc(env(safe-area-inset-bottom) + 84px))', direction: 'rtl', fontFamily: 'inherit', "
             "color: '#141B0D', display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: 8, "
             "maxWidth: 'calc(100vw - 20px)' },")
ops = sub(ops, old_shell, new_shell, 'ops shell style')

old_panel = "    panel: { width: 'min(470px, calc(100vw - 20px))',"
new_panel = "    panel: { width: 'min(470px, calc(100vw - 20px))', maxWidth: '100%', boxSizing: 'border-box',"
ops = sub(ops, old_panel, new_panel, 'ops panel style')
ops = ops.replace('التجار والصيدليات', 'التجار والمتاجر')
OPS.write_text(ops, encoding='utf-8')

# ---------------------------------------------------------------- style.css
css = CSS.read_text(encoding='utf-8')
EXTRA = """
/* ---- build 310 fixes ---- */
.app{padding-top:0!important}
header{top:0!important;padding-top:calc(10px + env(safe-area-inset-top,0px))!important}
.saree-ptr{background:transparent;border:0;box-shadow:none}
.saree-ptr span{background:#F1FAD3;color:#4E9A00;box-shadow:0 2px 8px #141B0D14}
.saree-promo-copy{gap:5px;max-width:min(62%,240px)}
.saree-promo-eyebrow{display:block;font-size:10px;font-weight:800;color:#4E9A00;opacity:1}
.saree-promo-copy>b{font-size:19px;line-height:1.32;font-weight:900}
.saree-promo-copy>b em{display:block;font-style:normal;color:#4E9A00}
.saree-promo-copy>small{font-size:10.5px;line-height:1.75;color:#4C5A2E;max-width:none}
.saree-promo-chips{gap:5px}
.saree-promo-chips span{background:#fff;color:#3E5A12;font-weight:700;padding:5px 10px;font-size:10px}
.saree-promo-chips span:before{display:none}
.saree-promo-chips span svg{width:13px;height:13px;flex:none;color:#fff;background:#6FCB00;border-radius:999px;padding:2px;box-sizing:content-box}
.saree-promo-art{background:transparent;width:118px;height:118px;border-radius:0}
.saree-promo-art img{width:100%;height:100%;object-fit:contain}
.saree-empty-cat{grid-column:1/-1;display:flex;flex-direction:column;align-items:center;gap:7px;text-align:center;padding:22px 14px;background:#fff;border:1px solid #EDEFE8;border-radius:16px;color:#8A8F86}
.saree-empty-cat b{font-size:12.5px;color:#141B0D}
.saree-empty-cat small{font-size:10.5px;line-height:1.75;max-width:260px}
.saree-empty-cat button{margin-top:4px;background:#F1FAD3;color:#3E7A00;border:0;border-radius:999px;padding:8px 14px;font:inherit;font-size:11px;font-weight:800;cursor:pointer}
@media(max-width:420px){.saree-promo-art{width:104px;height:104px}.saree-promo-copy>b{font-size:18px}}
"""
if 'build 310 fixes' not in css:
    css = css.rstrip() + '\n' + EXTRA
CSS.write_text(css, encoding='utf-8')

# --------------------------------------------------------------- hero SVG
NEW_SVG = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 460" role="img" aria-labelledby="title">
<title id="title">بيت ومندوب سريع على سكوتر بيوصل طلب</title>
<g fill="none" stroke="#141B0D" stroke-linecap="round" stroke-linejoin="round">
<path d="M286 100c0-20 16-34 36-34 6-14 22-24 40-20 16 4 27 18 25 34 11 4 18 12 18 21 0 6-4 9-10 9h-99c-6 0-10-4-10-10z" fill="#EAF7C9" stroke="none" opacity=".85"/>
<rect x="70" y="250" width="210" height="155" fill="#fff" stroke-width="16"/>
<path d="M52 252 175 142l123 110" fill="#A8E02A" stroke-width="16"/>
<path d="M245 205v-45h32v70" fill="#fff" stroke-width="14"/>
<circle cx="122" cy="302" r="24" fill="#F1FAD3" stroke-width="12"/>
<path d="M122 278v48M98 302h48" stroke-width="9"/>
<rect x="198" y="308" width="60" height="97" rx="8" fill="#6FCB00" stroke-width="12"/>
<circle cx="246" cy="356" r="5" fill="#141B0D" stroke="none"/>
<path d="M52 405v-26h42v26z" fill="#6FCB00" stroke-width="10"/>
<path d="M73 379c0-22-12-32-26-34 0 19 9 30 26 34z" fill="#A8E02A" stroke-width="8"/>
<path d="M73 379c0-22 12-32 26-34 0 19-9 30-26 34z" fill="#A8E02A" stroke-width="8"/>
<path d="M420 60h120a16 16 0 0 1 16 16v48a16 16 0 0 1-16 16h-56l-24 20v-20h-40a16 16 0 0 1-16-16V76a16 16 0 0 1 16-16z" fill="#fff" stroke-width="12"/>
<rect x="452" y="84" width="44" height="38" rx="6" fill="#F1FAD3" stroke-width="8"/>
<path d="M474 84v38M452 100h44" stroke-width="7"/>
<ellipse cx="335" cy="422" rx="40" ry="6" fill="#EAF7C9" stroke="none"/>
<ellipse cx="480" cy="422" rx="40" ry="6" fill="#EAF7C9" stroke="none"/>
<rect x="486" y="238" width="76" height="70" rx="10" fill="#D6F08A" stroke-width="14"/>
<path d="M486 266h76M524 238v70" stroke-width="10"/>
<circle cx="335" cy="388" r="30" fill="#fff" stroke-width="14"/>
<circle cx="335" cy="388" r="7" fill="#141B0D" stroke="none"/>
<circle cx="480" cy="388" r="30" fill="#fff" stroke-width="14"/>
<circle cx="480" cy="388" r="7" fill="#141B0D" stroke="none"/>
<rect x="350" y="350" width="100" height="16" rx="8" fill="#6FCB00" stroke-width="10"/>
<path d="M452 306C470 330 480 356 480 386" stroke-width="22"/>
<path d="M452 306C470 330 480 356 480 386" stroke="#6FCB00" stroke-width="12"/>
<path d="M352 356C344 330 346 304 356 282" stroke-width="22"/>
<path d="M352 356C344 330 346 304 356 282" stroke="#6FCB00" stroke-width="12"/>
<rect x="443" y="288" width="72" height="18" rx="9" fill="#141B0D" stroke="none"/>
<path d="M336 268 376 282" stroke-width="12"/>
<circle cx="346" cy="300" r="9" fill="#F1FAD3" stroke-width="8"/>
<path d="M450 294 424 208" stroke-width="34"/>
<path d="M450 294 424 208" stroke="#6FCB00" stroke-width="24"/>
<path d="M448 296C425 306 408 314 400 324L412 356" stroke-width="20"/>
<path d="M448 296C425 306 408 314 400 324L412 356" stroke="#6FCB00" stroke-width="11"/>
<path d="M404 356h20" stroke-width="10"/>
<path d="M424 220C402 236 380 254 358 272" stroke-width="18"/>
<path d="M424 220C402 236 380 254 358 272" stroke="#6FCB00" stroke-width="10"/>
<circle cx="416" cy="182" r="24" fill="#fff" stroke-width="12"/>
<path d="M392 181a24 24 0 0 1 48 0z" fill="#6FCB00" stroke-width="10"/>
<circle cx="407" cy="187" r="3.5" fill="#141B0D" stroke="none"/>
</g>
</svg>

"""
SVG.write_text(NEW_SVG, encoding='utf-8')

print('Applied build 310 fixes: ops panel width, hidden pull-to-refresh, category empty state, safe area, partner label, hero copy and illustration.')
