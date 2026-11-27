from pathlib import Path

app_path = Path("src/App.tsx")
css_path = Path("src/style.css")
if not app_path.exists() or not css_path.exists():
    raise SystemExit("App source or stylesheet is missing")

app = app_path.read_text()
marker = " <footer>© 2026 سريع"
if "mobile-bottom-nav" not in app:
    if marker not in app:
        raise SystemExit("Could not find footer insertion point for mobile navigation")
    nav = """ {role==='customer'&&<nav className="mobile-bottom-nav" aria-label="التنقل الرئيسي">
  <button className={tab==='home'?'active':''} onClick={()=>{setTab('home');setSelectedStore(null)}}><Home size={20}/><span>الرئيسية</span></button>
  <button onClick={()=>{setTab('home');setSelectedStore(null);setQuery('')}}><Search size={20}/><span>بحث</span></button>
  <button className={tab==='orders'?'active':''} onClick={()=>{setTab('orders');setSelectedStore(null)}}><ClipboardList size={20}/><span>طلباتي</span></button>
  <button className={tab==='cart'?'active':''} onClick={()=>{setTab('cart');setSelectedStore(null)}}><ShoppingCart size={20}/><span>السلة</span></button>
  <button className={tab==='profile'?'active':''} onClick={()=>{setTab('profile');setSelectedStore(null)}}><UserRound size={20}/><span>حسابي</span></button>
 </nav>}
"""
    app = app.replace(marker, nav + marker, 1)
    app_path.write_text(app)

css = css_path.read_text()
if ".mobile-bottom-nav{" not in css:
    css += """
/* Mobile customer navigation */
.mobile-bottom-nav{display:none}
@media(max-width:700px){
  .app{padding-bottom:calc(70px + env(safe-area-inset-bottom,0px))}
  .mobile-bottom-nav{position:fixed;z-index:50;left:0;right:0;bottom:0;display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:2px;padding:7px 5px calc(7px + env(safe-area-inset-bottom,0px));background:var(--surface);border-top:1px solid var(--line);box-shadow:0 -5px 20px #00000012}
  .mobile-bottom-nav button{min-width:0;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:3px;padding:5px 1px;background:transparent;color:var(--muted);font:inherit;font-size:9px;white-space:nowrap}
  .mobile-bottom-nav button svg{width:20px;height:20px}
  .mobile-bottom-nav button.active{color:var(--green);font-weight:800}
  .mobile-bottom-nav button:active{background:var(--soft);border-radius:9px}
  .layout{padding-bottom:12px}
}
"""
    css_path.write_text(css)
print("Added fixed mobile navigation for Home, Search, Orders, Cart and Account.")
