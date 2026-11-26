from pathlib import Path

ROOT = Path(".")
app_path = ROOT / "src/App.tsx"
css_path = ROOT / "src/style.css"
html_path = ROOT / "index.html"
mobile_path = ROOT / "src/lib/mobile.ts"
test_path = ROOT / "tests/source-smoke.test.cjs"

def replace_once(text, old, new, label):
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"UI patch stopped: expected one {label}, found {count}")
    return text.replace(old, new, 1)

app = app_path.read_text()
app = replace_once(app,
"type StoreItem = {id:string;name:string;type:Exclude<Service,'all'|'doctors'|'errand'>;area:string;rating:number;eta:string;fee:number;min:number;open:boolean;desc:string;icon:string;featured?:boolean};",
"type StoreItem = {id:string;name:string;type:Exclude<Service,'all'|'doctors'|'errand'>;area:string;rating:number;eta:string;fee:number;min:number;open:boolean;desc:string;icon:string;image?:string;featured?:boolean};",
"store image field")
app = app.replace("'عميل شفاء'", "'عميل جَيّلك'")
app = app.replace("'كل طلبات شفاء'", "'كل طلبات جَيّلك'")
app = app.replace("'لوحة إدارة شفاء'", "'لوحة إدارة جَيّلك'")
app = app.replace("لوحة إدارة شفاء", "لوحة إدارة جَيّلك")
app = app.replace("مشروع شفاء المرتبط", "مشروع جَيّلك المرتبط")
demo = """ <div className="demo"><span>● نسخة تشغيل تجريبية · ملوي، المنيا</span><div><span className="backend">{backendReady?'مفاتيح Supabase موجودة – يلزم استكمال ربط البيانات':'وضع تجريبي – البيانات محفوظة على هذا الجهاز'}</span>{!backendReady&&<label>تجربة الدور: <select value={role} onChange={e=>chooseRole(e.target.value as Role)}><option value="customer">العميل</option><option value="merchant">التاجر / الصيدلية</option><option value="driver">الكابتن</option><option value="admin">الإدارة</option></select></label>}</div></div>
"""
app = replace_once(app, demo, "", "temporary top strip")
old_header = """ <header><button className="icon-btn" onClick={()=>setModal('menu')}><Menu/></button><div className="brand"><b>✚ شفاء</b><small>SHIFA · خدمات ملوي في مكان واحد</small></div><span className="place"><MapPin size={16}/> ملوي، المنيا</span><div className="head-actions">{backendReady&&!signedInPhone&&<button className="login-btn" onClick={()=>setModal('login')}>دخول برقم الهاتف</button>}{signedInPhone&&<span className="signed-phone">{signedInPhone}</span>}<button className="icon-btn" onClick={()=>setDark(!dark)}>{dark?<Sun/>:<Moon/>}</button><button className="icon-btn" onClick={()=>notify('الإشعارات الفعلية تحتاج ربط FCM وخادم الإرسال')}><Bell/></button>{role==='customer'&&<button className="cart-btn" onClick={()=>setTab('cart')}><ShoppingCart/> السلة ({count})</button>}</div></header>"""
new_header = """ <header><button className="icon-btn" aria-label="فتح القائمة" onClick={()=>setModal('menu')}><Menu/></button><div className="brand"><b>جَيّلك</b><small>كل خدمات ملوي في مكان واحد</small></div><div className="head-actions"><button className="icon-btn" aria-label="الإشعارات" onClick={()=>notify('الإشعارات الفعلية تحتاج ربط FCM وخادم الإرسال')}><Bell/></button>{role==='customer'&&<button className="cart-btn" aria-label="السلة" onClick={()=>setTab('cart')}><ShoppingCart/><span>السلة ({count})</span></button>}</div></header>"""
app = replace_once(app, old_header, new_header, "top header")
app = app.replace("أهلاً بك في شفاء", "أهلاً بك في جَيّلك")
app = app.replace("<small>متاجر تجريبية – استبدلها ببيانات التجار بعد التعاقد</small>", "")
app = replace_once(app, '<div className="store-icon">{s.icon}</div>', '<div className="store-icon">{s.image?<img src={s.image} alt={s.name} loading="lazy"/>:<span>{s.icon}</span>}</div>', "store image renderer")
old_menu = """{modal==='menu'&&<div className="overlay" onClick={()=>setModal('')}><div className="dialog" onClick={e=>e.stopPropagation()}><button className="close" onClick={()=>setModal('')}><X/></button><h2>القائمة</h2>{navItems.map(([id,label,Icon])=><button className="menu-link" key={id} onClick={()=>{setTab(id);setModal('')}}><Icon size={18}/>{label}</button>)}</div></div>}"""
new_menu = """{modal==='menu'&&<div className="overlay" onClick={()=>setModal('')}><div className="dialog" onClick={e=>e.stopPropagation()}><button className="close" onClick={()=>setModal('')}><X/></button><h2>القائمة</h2><section className="drawer-tools"><div className="drawer-account"><b>{signedInPhone?'مرحبًا '+signedInPhone:'حسابك على جَيّلك'}</b>{backendReady&&!signedInPhone&&<button className="login-btn" onClick={()=>setModal('login')}>دخول برقم الهاتف</button>}{signedInPhone&&<button className="outline" onClick={async()=>{await supabase?.auth.signOut();setSignedInPhone(null);}}>تسجيل الخروج</button>}</div><label className="drawer-role">تبديل نوع الحساب<select value={role} onChange={e=>chooseRole(e.target.value as Role)}><option value="customer">العميل</option><option value="merchant">التاجر / الصيدلية</option><option value="driver">الكابتن</option><option value="admin">الإدارة</option></select></label><button className="menu-link" onClick={()=>setDark(!dark)}>{dark?<Sun size={18}/>:<Moon size={18}/>} {dark?'الوضع الفاتح':'الوضع الليلي'}</button></section>{navItems.map(([id,label,Icon])=><button className="menu-link" key={id} onClick={()=>{setTab(id);setModal('')}}><Icon size={18}/>{label}</button>)}</div></div>}"""
app = replace_once(app, old_menu, new_menu, "drawer menu")
app = app.replace("© 2026 شفاء Shifa", "© 2026 جَيّلك")
app_path.write_text(app)

css = css_path.read_text()
css = css.replace("body{margin:0;min-width:320px}", "body{margin:0;min-width:320px;min-height:100%;}")
css = css.replace(".app{min-height:100vh;", ".app{min-height:100vh;min-height:100dvh;padding-top:env(safe-area-inset-top,0px);")
demo_css = ".demo{background:#103f35;color:#dff7ec;padding:8px max(16px,calc((100vw - 1240px)/2));display:flex;align-items:center;justify-content:space-between;gap:15px;font-size:11px}.demo>div{display:flex;align-items:center;gap:12px}.demo label{display:flex;align-items:center;gap:6px}.demo select{background:#1c594b;color:#fff;border:1px solid #4c8271;border-radius:8px;padding:4px 8px;font-size:11px}.backend{color:#b5e8d3}"
css = css.replace(demo_css, "")
css = css.replace("position:sticky;top:0;z-index:5}", "position:sticky;top:env(safe-area-inset-top,0px);z-index:5;flex:none}")
css = css.replace(".layout{max-width:1280px;margin:auto;padding:22px 18px;", ".layout{max-width:1280px;margin:auto;padding:30px 18px 22px;")
css = css.replace(".store-icon{width:52px;height:52px;border-radius:13px;background:var(--soft);display:grid;place-items:center;font-size:28px;flex:none}", ".store-icon{width:76px;height:76px;aspect-ratio:1/1;border-radius:16px;background:var(--soft);display:grid;place-items:center;font-size:28px;flex:none;overflow:hidden}.store-icon img{display:block;width:100%;height:100%;object-fit:cover;border-radius:inherit}.store-icon span{display:grid;place-items:center;width:100%;height:100%}")
css = css.replace(".dialog h2{margin-bottom:18px}", ".dialog h2{margin-bottom:18px}.drawer-tools{padding:4px 0 12px;border-bottom:1px solid var(--line);margin-bottom:8px}.drawer-account{display:flex;align-items:center;justify-content:space-between;gap:8px;flex-wrap:wrap;margin-bottom:12px;font-size:11px}.drawer-role{display:flex;flex-direction:column;gap:6px;font-size:10px;color:var(--muted);margin:8px 0}.drawer-role select{width:100%;padding:10px;border:1px solid var(--line);border-radius:9px;background:var(--surface);color:var(--ink);font:inherit}")
css = css.replace("@media(max-width:650px){.demo{align-items:flex-start;flex-direction:column;padding:8px 12px;gap:6px}.demo>div{width:100%;justify-content:space-between}.demo label{font-size:9px}", "@media(max-width:650px){")
css = css.replace(".layout{display:block;padding:13px 11px}", ".layout{display:block;padding:22px 11px 18px}")
css = css.replace("header{height:62px;padding:0 11px;gap:9px}", "header{height:66px;padding:0 12px;gap:10px;top:env(safe-area-inset-top,0px)}")
css = css.replace(".brand b{font-size:19px}.brand small{font-size:8px}", ".brand b{font-size:21px;line-height:1.2}.brand small{font-size:9px;line-height:1.5}.head-actions{gap:5px}.head-actions .icon-btn{padding:9px}.cart-btn{white-space:nowrap}")
css = css.replace(".store-card{padding:11px}", ".store-card{padding:12px;gap:11px;align-items:center}.store-icon{width:68px;height:68px;border-radius:14px}")
css_path.write_text(css)

html = html_path.read_text()
html = html.replace('content="#087f68"', 'content="#ffffff"')
html = html.replace('content="شفاء - خدمات وتوصيل محلي في ملوي، المنيا. مطاعم وبقالة وصيدليات ومشاوير خاصة."', 'content="جَيّلك - خدمات وتوصيل محلي في ملوي، المنيا."')
html = html.replace("<title>شفاء | Shifa - ملوي</title>", "<title>جَيّلك - كل خدمات ملوي</title>")
html_path.write_text(html)

mobile = mobile_path.read_text().replace("طلب من شفاء", "طلب من جَيّلك")
mobile_path.write_text(mobile)

tests = test_path.read_text()
tests = tests.replace("  assert.ok(app.includes('البيانات محفوظة على هذا الجهاز'));", "  assert.ok(app.includes(\"localStorage.getItem('shifa:' + key)\") || app.includes(\"localStorage.getItem('shifa:'\"));")
if "branded mobile UI has safe area" not in tests:
    tests += """
test('branded mobile UI has safe area, clean header, and image-ready store cards', () => {
  const app = fs.readFileSync(path.join(root, 'src/App.tsx'), 'utf8');
  const css = fs.readFileSync(path.join(root, 'src/style.css'), 'utf8');
  const html = fs.readFileSync(path.join(root, 'index.html'), 'utf8');
  assert.ok(app.includes('أهلاً بك في جَيّلك'));
  assert.ok(app.includes('s.image?<img'));
  assert.ok(!app.includes('متاجر تجريبية – استبدلها ببيانات التجار بعد التعاقد'));
  assert.ok(!app.includes('className="demo"'));
  assert.ok(css.includes('env(safe-area-inset-top'));
  assert.ok(css.includes('object-fit:cover'));
  assert.ok(html.includes('<title>جَيّلك - كل خدمات ملوي</title>'));
});
"""
test_path.write_text(tests)
print("Applied Jeylak UI patch.")
