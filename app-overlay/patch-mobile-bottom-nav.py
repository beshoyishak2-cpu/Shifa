from pathlib import Path

app_path = Path("src/App.tsx")
css_path = Path("src/style.css")
if not app_path.exists() or not css_path.exists():
    raise SystemExit("App source or stylesheet is missing")
app = app_path.read_text()
css = css_path.read_text()

state = " const [role,setRole]=useState<Role>('customer'),[tab,setTabState]=useState('home')"
if "const [searchKeyboardOpen,setSearchKeyboardOpen]" not in app:
    if state not in app:
        raise SystemExit("Could not locate App state declaration")
    app = app.replace(state, " const [searchKeyboardOpen,setSearchKeyboardOpen]=useState(false);\n" + state, 1)

if "const onFocus=(e:FocusEvent)" not in app:
    anchor = " useEffect(()=>{if(!isNativeApp())return;let active=true;"
    effect = " useEffect(()=>{const onFocus=(e:FocusEvent)=>{const target=e.target as HTMLElement|null;if(target?.closest('.customer-search-page'))setSearchKeyboardOpen(true)};const onBlur=(e:FocusEvent)=>{const target=e.target as HTMLElement|null;if(target?.closest('.customer-search-page'))setSearchKeyboardOpen(false)};window.addEventListener('focusin',onFocus);window.addEventListener('focusout',onBlur);return()=>{window.removeEventListener('focusin',onFocus);window.removeEventListener('focusout',onBlur)}},[]);\n"
    if anchor not in app:
        raise SystemExit("Could not locate effect insertion point")
    app = app.replace(anchor, effect + anchor, 1)

old_nav_items = "[['home','الرئيسية',Home],['orders','طلباتي',ClipboardList],['errand','ابعتلي مشوار',Bike]"
new_nav_items = "[['home','الرئيسية',Home],['search','بحث',Search],['cart','السلة',ShoppingCart],['orders','طلباتي',ClipboardList],['errand','ابعتلي مشوار',Bike]"
if new_nav_items not in app:
    if old_nav_items not in app:
        raise SystemExit("Could not locate customer desktop navigation")
    app = app.replace(old_nav_items, new_nav_items, 1)

old_header_cart = '<div className="head-actions"><button className="icon-btn" aria-label="الإشعارات" onClick={()=>notify(\'الإشعارات الفعلية تحتاج ربط FCM وخادم الإرسال\')}><Bell/></button>{role===\'customer\'&&<button className="cart-btn" aria-label="السلة" onClick={()=>setTab(\'cart\')}><ShoppingCart/><span>السلة ({count})</span></button>}</div>'
new_header_actions = '<div className="head-actions"><button className="icon-btn" aria-label="الإشعارات" onClick={()=>notify(\'الإشعارات الفعلية تحتاج ربط FCM وخادم الإرسال\')}><Bell/></button></div>'
if old_header_cart in app:
    app = app.replace(old_header_cart, new_header_actions, 1)

search_page = """ {role==='customer'&&tab==='search'&&<section className="customer-search-page">
  <div className="page-title"><div><h1>ابحث في سريع</h1><p className="muted">دور على متجر أو منتج داخل ملوي</p></div></div>
  <div className="search customer-search-box"><Search/><input autoComplete="off" aria-label="البحث عن متجر أو منتج" placeholder="مثلاً: بيتزا، صيدلية، خضار..." value={query} onChange={e=>setQuery(e.target.value)}/>{query&&<button aria-label="مسح البحث" onClick={()=>setQuery('')}><X size={18}/></button>}</div>
  {!normalizedQuery?<div className="search-suggestions"><span>ابدأ بكتابة اسم متجر أو منتج للبحث.</span><div>{['مطاعم','صيدليات','سوبر ماركت','خضار وفاكهة'].map((term,i)=><button key={term} onClick={()=>setQuery(term)}>{['🍽️','💊','🛒','🥬'][i]} {term}</button>)}</div></div>:<>
   <div className="section-title"><h2>المتاجر المطابقة</h2><span className="muted">{visibleStores.length} متجر</span></div>
   {visibleStores.length?<div className="store-grid">{visibleStores.map(s=><button className="store-card" key={s.id} onClick={()=>{setSelectedStore(s.id);setProductCategory('all');setTab('home')}}><div className="store-icon">{s.image?<img src={s.image} alt={s.name}/>:<span>{s.icon}</span>}</div><div className="store-main"><b>{s.name}</b><small>{s.desc}</small><small><MapPin size={12}/> {s.area}</small><div className="store-meta"><span>★ {s.rating}</span><span>◷ {s.eta}</span><span>{money(s.fee)} توصيل</span></div></div><span className="store-open">{s.open?'مفتوح':'مغلق'}</span></button>)}</div>:<Empty title="لا توجد متاجر مطابقة" hint="جرّب كلمة بحث مختلفة أو اسم منطقة أو خدمة."/>}
   <div className="section-title search-products-title"><h2>المنتجات المطابقة</h2><span className="muted">{products.filter(p=>p.available&&`${p.name} ${p.description} ${p.category}`.toLocaleLowerCase().includes(normalizedQuery)).length} منتج</span></div>
   <div className="product-grid">{products.filter(p=>p.available&&`${p.name} ${p.description} ${p.category}`.toLocaleLowerCase().includes(normalizedQuery)).map(p=><article className="product" key={p.id}><div className="product-art">{p.imageUrl?<img src={p.imageUrl} alt={p.name} loading="lazy"/>:p.emoji}</div><small className="product-category">{stores.find(s=>s.id===p.storeId)?.name||'متجر'} · {p.category}</small><h3>{p.name}</h3><p>{p.description}</p><div className="product-foot"><b>{money(p.price)}</b><button className="add" disabled={optionLoading} onClick={()=>void beginAddProduct(p)}><Plus size={16}/> أضف</button></div></article>)}</div>
  </>}
 </section>}
"""
cart_marker = " {role==='customer'&&tab==='cart'&&<>"
if "tab==='search'&&" not in app:
    if cart_marker not in app:
        raise SystemExit("Could not locate cart page insertion point")
    app = app.replace(cart_marker, search_page + cart_marker, 1)

# Replace the legacy nav if present; otherwise insert the new one before the footer.
nav = """ {role==='customer'&&<nav className={`mobile-bottom-nav${searchKeyboardOpen?' keyboard-open':''}`} aria-label="التنقل الرئيسي">
  <button className={tab==='home'?'active':''} aria-current={tab==='home'?'page':undefined} onClick={()=>{setTab('home');setSelectedStore(null)}}><Home size={20}/><span>الرئيسية</span></button>
  <button className={tab==='search'?'active':''} aria-current={tab==='search'?'page':undefined} onClick={()=>{setTab('search');setSelectedStore(null)}}><Search size={20}/><span>بحث</span></button>
  <button className={tab==='cart'?'active':''} aria-current={tab==='cart'?'page':undefined} onClick={()=>{setTab('cart');setSelectedStore(null)}}><span className="nav-cart-icon"><ShoppingCart size={20}/>{count>0&&<i className="nav-cart-badge">{count>99?'99+':count}</i>}</span><span>السلة</span></button>
  <button className={tab==='orders'?'active':''} aria-current={tab==='orders'?'page':undefined} onClick={()=>{setTab('orders');setSelectedStore(null)}}><ClipboardList size={20}/><span>طلباتي</span></button>
  <button className={tab==='profile'?'active':''} aria-current={tab==='profile'?'page':undefined} onClick={()=>{setTab('profile');setSelectedStore(null)}}><UserRound size={20}/><span>حسابي</span></button>
 </nav>}
"""
footer = " <footer>© 2026 سريع"
if "nav-cart-badge" not in app:
    if 'mobile-bottom-nav' in app:
        start = app.index(" {role==='customer'&&<nav className=\"mobile-bottom-nav\"")
        end = app.index(" </nav>}", start) + len(" </nav>}")
        app = app[:start] + nav.rstrip() + app[end:]
    elif footer in app:
        app = app.replace(footer, nav + footer, 1)
    else:
        raise SystemExit("Could not locate mobile nav/footer insertion point")

if "/* Customer navigation/search refinement" not in css:
    css += """
/* Customer navigation/search refinement — scoped to the customer shell */
@media(max-width:700px){
 .app{padding-bottom:calc(76px + env(safe-area-inset-bottom,0px))}
 .mobile-bottom-nav{grid-template-columns:repeat(5,minmax(0,1fr));min-height:62px;padding:7px 5px calc(7px + env(safe-area-inset-bottom,0px));gap:0}
 .mobile-bottom-nav button{position:relative;gap:4px;font-size:10px;font-weight:600;color:var(--muted);border:0;border-radius:10px}
 .mobile-bottom-nav button.active{color:var(--green)}
 .mobile-bottom-nav button.active:after{content:"";position:absolute;top:-7px;left:30%;right:30%;height:3px;border-radius:0 0 4px 4px;background:var(--green)}
 .nav-cart-icon{position:relative;display:inline-flex;align-items:center;justify-content:center}
 .nav-cart-badge{position:absolute;top:-7px;right:-10px;min-width:15px;height:15px;padding:0 3px;border-radius:9px;background:#e34d4d;color:#fff;font-size:9px;font-style:normal;font-weight:800;line-height:15px;text-align:center;border:1.5px solid var(--surface)}
 .mobile-bottom-nav.keyboard-open{display:none}
 .customer-search-page .customer-search-box{position:sticky;top:calc(66px + env(safe-area-inset-top,0px));z-index:5;box-shadow:0 5px 16px #0000000a}
 .search-suggestions{padding:16px 4px;color:var(--muted);font-size:11px}
 .search-suggestions>div{display:flex;flex-wrap:wrap;gap:7px;margin-top:12px}
 .search-suggestions button{background:var(--surface);border:1px solid var(--line);border-radius:20px;padding:9px 12px;color:var(--ink);font:inherit;font-size:10px}
 .search-products-title{margin-top:22px}
}
"""
app_path.write_text(app)
css_path.write_text(css)
print("Added customer bottom navigation, search page, cart badge and keyboard-aware nav.")
