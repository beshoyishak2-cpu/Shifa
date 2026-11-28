#!/usr/bin/env python3
"""Batch 3 of 3: merchant, rider, login, splash references + light ride map + Arabic geo error."""
import io

p = 'src/App.tsx'
s = io.open(p, encoding='utf-8').read()

def rep(old, new, label):
    global s
    assert old in s, f'missing anchor: {label}'
    assert s.count(old) == 1, f'anchor not unique: {label}'
    s = s.replace(old, new)

# ---- 1) Merchant overview -> reference ----
OLD_MERCHANT = s[s.index(" {role==='merchant'&&tab==='overview'&&<><h1>لوحة التاجر</h1>"):s.index(" {role==='merchant'&&tab==='orders'&&renderOrders('merchant')}")]
NEW_MERCHANT = """ {role==='merchant'&&tab==='overview'&&(()=>{const m0=merchantStoreRows[0];const newOrders=orders.filter(o=>merchantIds.includes(o.storeId||'')&&o.status==='جديد');const menuItems=products.filter(x=>merchantIds.includes(x.storeId));const todayCount=merchantStoreRows.reduce((a,m)=>a+merchantToday(m.id).length,0);const todayGross=merchantStoreRows.reduce((a,m)=>a+merchantToday(m.id).reduce((g,o)=>g+o.total,0),0);const rating=stores.find(x=>x.id===m0?.id)?.rating||'4.7';return <div className="saree-merchant">
  <div className="saree-merchant-head"><button className="saree-circle-btn" aria-label="رجوع" onClick={goBack}><ChevronLeft size={18}/></button><h1>لوحة التاجر</h1></div>
  {!m0&&<Empty title="لا توجد متاجر مرتبطة" hint="اطلب من الإدارة ربط حسابك بالمنشأة المعتمدة."/>}
  {m0&&<>
  <section className="saree-merchant-store">
   <button className={m0.is_open?'saree-switch on':'saree-switch'} disabled={!m0.is_active} onClick={()=>void toggleMerchantStoreOpen(m0)} aria-pressed={!!m0.is_open} aria-label={m0.is_open?'إغلاق المتجر':'فتح المتجر'}><i/></button>
   <div className="saree-merchant-store-info"><b>{m0.name}</b><small>{m0.is_open?'مفتوح · بيستقبل طلبات':'مغلق حالياً'}</small></div>
   <span className="saree-avatar saree-merchant-avatar">{m0.image_url?<img src={m0.image_url} alt=""/>:<Store size={24}/>}</span>
  </section>
  <div className="saree-merchant-stats">
   <div className="saree-mstat"><b>{todayCount}</b><small>طلب النهاردة</small></div>
   <div className="saree-mstat"><b className="lime">{money(todayGross)}</b><small>مبيعات النهاردة</small></div>
   <div className="saree-mstat"><b>{rating}</b><small>التقييم</small></div>
  </div>
  <h2 className="saree-merchant-section">طلبات جديدة</h2>
  {!newOrders.length&&<div className="saree-empty-card">لا توجد طلبات جديدة الآن — الطلبات الجديدة تظهر هنا فور وصولها.</div>}
  {newOrders.map(o=><article className="saree-merchant-order" key={o.id}>
   <div className="saree-merchant-order-top"><span className="saree-status-chip open">جديد</span><b>طلب #{o.number}</b></div>
   <p className="saree-merchant-order-items">{o.kind} · {o.customer}</p>
   <div className="saree-merchant-order-meta"><b>{money(o.total+o.delivery)}</b><small>الإجمالي + التوصيل</small></div>
   <div className="saree-merchant-order-actions">
    <button className="saree-btn lime" onClick={()=>void updateServerOrder(o,'تم القبول')}>قبول الطلب</button>
    <button className="saree-btn ghost" onClick={()=>void updateServerOrder(o,'ملغي')}>رفض</button>
   </div>
  </article>)}
  <h2 className="saree-merchant-section">المنيو</h2>
  <section className="saree-merchant-menu">
   {menuItems.map(x=><div className="saree-merchant-menu-row" key={x.id}>
    <button className={x.available!==false?'saree-switch on':'saree-switch'} aria-pressed={x.available!==false} aria-label={'تفعيل '+x.name} onClick={()=>{if(!backendReady){setProducts(products.map(pp=>pp.id===x.id?{...pp,available:pp.available===false}:pp));notify('تم تحديث توفر الصنف محليًا');}else{notify('تحديث توفر الصنف يتطلب صلاحيات التاجر على الخادم')}}}><i/></button>
    <div className="saree-merchant-menu-info"><b>{x.name}</b><small>{money(x.price)}</small></div>
    <span className="saree-avatar saree-menu-thumb">{x.imageUrl?<img src={x.imageUrl} alt=""/>:x.emoji}</span>
   </div>)}
   {!menuItems.length&&<div className="saree-empty-card">لا توجد أصناف بعد.</div>}
  </section>
  <button className="saree-add-item" onClick={()=>setTab('inventory')}><span className="saree-add-item-plus">+</span><span className="saree-add-item-text"><b>أضف صنف جديد</b><small>ارفع صورة الصنف من موبايلك</small></span><Camera size={22}/></button>
  </>}
 </div>})()}
"""
rep(OLD_MERCHANT, NEW_MERCHANT, 'merchant overview')

# ---- 2) Rider overview -> reference ----
OLD_DRIVER = s[s.index(" {role==='driver'&&tab==='overview'&&<>"):s.index(" {role==='driver'&&tab==='orders'&&renderOrders('driver')}")]
NEW_DRIVER = """ {role==='driver'&&tab==='overview'&&(()=>{const myId=backendReady?currentUserId:'demo-courier';const mine=orders.filter(o=>o.courierId===myId);const delivered=mine.filter(o=>o.status==='تم التسليم');const avail=orders.filter(o=>(o.status==='جاهز للاستلام'&&!o.courierId)||(o.kind==='مشوار خاص'&&o.status==='جديد'&&!o.courierId));const offer=avail[0];const todayEarn=delivered.reduce((a,o)=>a+o.delivery,0);return <div className="saree-rider">
  <div className="saree-rider-head">
   <label className="saree-rider-online"><button className={driverOnline?'saree-switch on':'saree-switch'} disabled={!!supabase&&!driverVerified} onClick={()=>void toggleDriverAvailability()} aria-pressed={driverOnline} aria-label="حالة التوفر"><i/></button><span>{driverOnline?'متاح':'غير متاح'}</span></label>
   <div className="saree-rider-id"><b>أهلاً {String(customer.name||'كابتن').split(' ')[0]}</b><small>مندوب سريع · ملوى</small></div>
   <span className="saree-avatar saree-rider-avatar">{String(customer.name||'ك').trim().charAt(0)}</span>
  </div>
  <div className="saree-merchant-stats">
   <div className="saree-mstat"><b>{delivered.length}</b><small>مشاوير النهاردة</small></div>
   <div className="saree-mstat"><b className="lime">{money(todayEarn)}</b><small>أرباح النهاردة</small></div>
   <div className="saree-mstat"><b>4.9</b><small>تقييمك</small></div>
  </div>
  {offer&&<section className="saree-rider-offer">
   <div className="saree-rider-offer-top"><span className="saree-status-chip open">{money(offer.delivery)}+</span><b>طلب جديد قريب منك</b></div>
   <svg className="saree-rider-map" viewBox="0 0 320 150" aria-hidden="true">
    <rect width="320" height="150" fill="#EDF2E4"/>
    {Array.from({length:12}).map((_,i)=><rect key={i} x={(i%4)*82+8} y={Math.floor(i/4)*52+8} width="66" height="38" rx="6" fill={i%5===0?'#DDEEC8':'#E2E9D8'}/>)}
    <path d="M40 118 C 110 108, 150 60, 285 42" stroke="#141B0D" strokeWidth="6" fill="none" strokeLinecap="round"/>
    <path d="M40 118 C 110 108, 150 60, 285 42" stroke="#6FCB00" strokeWidth="2.4" strokeDasharray="1 7" fill="none" strokeLinecap="round"/>
    <circle cx="40" cy="118" r="7" fill="#6FCB00" stroke="#fff" strokeWidth="2.5"/>
    <circle cx="285" cy="42" r="7" fill="#141B0D" stroke="#fff" strokeWidth="2.5"/>
   </svg>
   <div className="saree-rider-offer-lines">
    <p><b>استلام: {offer.storeName}</b><small>{offer.kind}</small></p>
    <p><b>توصيل: {offer.address}</b><small>{offer.customer} · {offer.phone}</small></p>
   </div>
   <div className="saree-merchant-order-actions">
    <button className="saree-btn lime" onClick={()=>void acceptServerDelivery(offer)}>قبول المشوار</button>
    <button className="saree-btn ghost" onClick={()=>notify('تم تخطي الطلب')}>تخطي</button>
   </div>
  </section>}
  {!offer&&<div className="saree-empty-card">لا توجد طلبات متاحة الآن — هيوصلك إشعار أول ما يظهر طلب قريب.</div>}
  <button className="saree-rider-week" onClick={()=>setTab('wallet')}><span className="saree-rider-week-ic"><Wallet size={20}/></span><span className="saree-rider-week-text"><b>أرباح الأسبوع: {money(todayEarn)}</b><small>التسوية كل يوم خميس</small></span><ChevronLeft size={18}/></button>
  {mine.length>0&&renderOrders('driver')}
 </div>})()}
"""
rep(OLD_DRIVER, NEW_DRIVER, 'driver overview')

# ---- 3) Login modal -> reference look (password auth kept) ----
i0 = s.index("{modal==='login'&&<div className=\"overlay\"")
i1 = s.index("{modal==='product-options'", i0)
OLD_LOGIN = s[i0:i1]
NEW_LOGIN = """{modal==='login'&&<div className="overlay saree-login-overlay" onClick={()=>setModal('')}><div className="dialog saree-login" onClick={e=>e.stopPropagation()}><button className="saree-circle-btn saree-login-close" onClick={()=>setModal('')} aria-label="إغلاق"><X size={16}/></button>
 <div className="saree-login-brand">سريع<span>.</span></div>
 <h2>أهلاً بيك</h2>
 <p className="saree-login-sub">{authMode==='register'?'أنشئ حسابك برقم موبايلك وكلمة مرور، وهتطلب في ثانية.':'سجّل دخولك برقم موبايلك وكلمة المرور، وهتوصل لطلباتك في ثانية.'}</p>
 {authMode==='register'&&<label className="saree-login-field"><input value={authName} onChange={e=>setAuthName(e.target.value)} placeholder="الاسم بالكامل"/></label>}
 <label className="saree-login-field saree-login-phone"><span className="saree-login-prefix"><i className="saree-flag-eg"/>+20</span><input inputMode="tel" value={authPhone} onChange={e=>setAuthPhone(e.target.value)} placeholder="01X XXX XXXX"/></label>
 <label className="saree-login-field saree-login-pass"><input type={showAuthPassword?'text':'password'} autoComplete={authMode==='register'?'new-password':'current-password'} value={authPassword} onChange={e=>setAuthPassword(e.target.value)} placeholder="كلمة المرور (8 أحرف على الأقل)"/><button type="button" onClick={()=>setShowAuthPassword(v=>!v)}>{showAuthPassword?'إخفاء':'إظهار'}</button></label>
 <button className="saree-btn lime saree-login-submit" onClick={submitPhoneAuth}>{authMode==='register'?'إنشاء الحساب':'دخول'}</button>
 <div className="saree-login-or"><span/>أو<span/></div>
 <button className="saree-btn ghost saree-login-alt" onClick={()=>setAuthMode(authMode==='register'?'login':'register')}><Package size={18}/>{authMode==='register'?'لديك حساب؟ سجل الدخول':'مستخدم جديد؟ أنشئ حسابًا'}</button>
 <p className="saree-login-terms">بالتسجيل أنت موافق على <button type="button" onClick={()=>setModal('about')}>شروط الاستخدام</button> و<button type="button" onClick={()=>setModal('about')}>سياسة الخصوصية</button></p>
</div></div>}
 """
rep(OLD_LOGIN, NEW_LOGIN, 'login modal')

# ---- 4) Splash -> onboarding reference look ----
OLD_SPLASH = s[s.index('function SareeSplash(){'):s.index('function SareeInlineIcon')]
NEW_SPLASH = """function SareeSplash(){
 const [visible,setVisible]=useState(true);
 useEffect(()=>{
  const reduce=window.matchMedia?.('(prefers-reduced-motion: reduce)').matches;
  const timer=window.setTimeout(()=>setVisible(false),reduce?650:2350);
  return()=>window.clearTimeout(timer);
 },[]);
 if(!visible)return null;
 return <div className="saree-splash" role="status" aria-label="جاري فتح سريع">
  <i className="saree-splash-blob tl"/><i className="saree-splash-blob br"/>
  <div className="saree-splash-art"><SareeInlineIcon name="scooter" size={120}/></div>
  <div className="saree-splash-word">سريع<span>.</span></div>
  <p className="saree-splash-tag">كل اللي تحتاجه يوصلك لحد بابك</p>
  <span className="saree-splash-dots"><i/><i/><b/></span>
 </div>;
}


"""
rep(OLD_SPLASH, NEW_SPLASH, 'splash')

# ---- 5) icons: add Camera ----
rep("Users, Wallet, X, Bell,", "Users, Wallet, X, Bell, Camera,", 'icons import')

# ---- 6) CSS ----
CSS = """/* -------- Saree build 313: merchant/rider/login/splash references + light ride map -------- */
.saree-switch{width:52px;height:30px;border-radius:99px;background:#E4E7E0;border:0;padding:3px;display:flex;align-items:center;justify-content:flex-start;transition:background .15s;flex:none}
.saree-switch i{width:24px;height:24px;border-radius:50%;background:#fff;box-shadow:0 1px 4px rgba(20,27,13,.18);display:block}
.saree-switch.on{background:#6FCB00;justify-content:flex-end}
.saree-merchant-head{display:flex;align-items:center;gap:12px;margin:2px 0 14px}
.saree-merchant-head h1{margin:0;font-size:22px;font-weight:900;color:#141B0D}
.saree-merchant-store{display:flex;align-items:center;gap:12px;background:#fff;border:1px solid #E9EDE4;border-radius:22px;padding:16px}
.saree-merchant-store-info{flex:1;min-width:0;display:flex;flex-direction:column;gap:3px}
.saree-merchant-store-info b{font-size:16px;color:#141B0D}
.saree-merchant-store-info small{font-size:11px;color:#6D7466}
.saree-merchant-avatar{width:56px;height:56px;font-size:22px;background:#F1FAD3;color:#141B0D}
.saree-merchant-stats{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin:14px 0}
.saree-mstat{background:#fff;border:1px solid #E9EDE4;border-radius:18px;padding:14px 8px;text-align:center;display:flex;flex-direction:column;gap:4px}
.saree-mstat b{font-size:17px;font-weight:900;color:#141B0D}
.saree-mstat b.lime{color:#57A300}
.saree-mstat small{font-size:10px;color:#6D7466}
.saree-merchant-section{font-size:16px;font-weight:900;color:#141B0D;margin:18px 0 10px}
.saree-merchant-order{background:#fff;border:1px solid #E9EDE4;border-radius:20px;padding:16px;display:flex;flex-direction:column;gap:8px;margin-bottom:12px}
.saree-merchant-order-top{display:flex;justify-content:space-between;align-items:center}
.saree-merchant-order-top b{font-size:14px;color:#141B0D}
.saree-merchant-order-items{margin:0;font-size:11px;color:#6D7466}
.saree-merchant-order-meta{display:flex;justify-content:space-between;align-items:baseline}
.saree-merchant-order-meta b{font-size:13px;color:#141B0D}
.saree-merchant-order-meta small{font-size:10px;color:#6D7466}
.saree-merchant-order-actions{display:flex;gap:10px;margin-top:4px}
.saree-merchant-order-actions .saree-btn.lime{flex:1;margin:0}
.saree-merchant-order-actions .saree-btn.ghost{margin:0;padding:12px 22px}
.saree-merchant-menu{background:#fff;border:1px solid #E9EDE4;border-radius:20px;padding:6px 16px}
.saree-merchant-menu-row{display:flex;align-items:center;gap:12px;padding:12px 0;border-bottom:1px solid #F1F3EC}
.saree-merchant-menu-row:last-child{border-bottom:0}
.saree-merchant-menu-info{flex:1;min-width:0;display:flex;flex-direction:column;gap:2px}
.saree-merchant-menu-info b{font-size:13px;color:#141B0D}
.saree-merchant-menu-info small{font-size:10px;color:#6D7466}
.saree-menu-thumb{width:46px;height:46px;border-radius:12px;font-size:18px;background:#F3F4F1;color:#141B0D}
.saree-menu-thumb img{border-radius:12px}
.saree-add-item{width:100%;margin:12px 0;display:flex;align-items:center;gap:12px;border:2px dashed #A8E02A;background:#F1FAD3;border-radius:20px;padding:14px 16px;color:#141B0D;text-align:right}
.saree-add-item-plus{width:34px;height:34px;border-radius:50%;background:#6FCB00;color:#fff;font-size:20px;font-weight:900;display:grid;place-items:center;flex:none}
.saree-add-item-text{flex:1;display:flex;flex-direction:column;gap:2px}
.saree-add-item-text b{font-size:13px}
.saree-add-item-text small{font-size:10px;color:#6D7466}
.saree-rider-head{display:flex;align-items:center;gap:12px;margin:6px 0 14px}
.saree-rider-online{display:flex;align-items:center;gap:7px;font-size:11px;font-weight:800;color:#141B0D}
.saree-rider-id{flex:1;min-width:0;display:flex;flex-direction:column;gap:2px;align-items:flex-end}
.saree-rider-id b{font-size:16px;color:#141B0D}
.saree-rider-id small{font-size:10px;color:#6D7466}
.saree-rider-avatar{width:52px;height:52px;background:#E4F5C4;color:#3F6400;font-size:20px;font-weight:900}
.saree-rider-offer{background:#fff;border:1px solid #E9EDE4;border-radius:20px;padding:16px;display:flex;flex-direction:column;gap:12px;margin-bottom:12px}
.saree-rider-offer-top{display:flex;justify-content:space-between;align-items:center}
.saree-rider-offer-top b{font-size:14px;color:#141B0D}
.saree-rider-map{width:100%;border-radius:14px;display:block}
.saree-rider-offer-lines{display:flex;flex-direction:column;gap:10px;border-right:2px solid #E9EDE4;padding-right:12px}
.saree-rider-offer-lines p{margin:0;display:flex;flex-direction:column;gap:2px}
.saree-rider-offer-lines b{font-size:12px;color:#141B0D}
.saree-rider-offer-lines small{font-size:10px;color:#6D7466}
.saree-rider-week{width:100%;display:flex;align-items:center;gap:12px;background:#fff;border:1px solid #E9EDE4;border-radius:20px;padding:16px;color:#141B0D;text-align:right}
.saree-rider-week-ic{width:40px;height:40px;border-radius:12px;background:#F1FAD3;color:#57A300;display:grid;place-items:center;flex:none}
.saree-rider-week-text{flex:1;display:flex;flex-direction:column;gap:2px}
.saree-rider-week-text b{font-size:13px}
.saree-rider-week-text small{font-size:10px;color:#6D7466}
.saree-empty-card{background:#fff;border:1px dashed #DDE3D5;border-radius:18px;padding:18px;text-align:center;font-size:11px;color:#6D7466;margin-bottom:12px}
.saree-login-overlay{align-items:flex-start;padding-top:max(40px,8vh)}
.saree-login{width:min(430px,100%);border-radius:28px;padding:30px 24px 22px;text-align:right}
.saree-login-close{position:absolute;left:16px;top:16px}
.saree-login-brand{font-size:30px;font-weight:900;color:#141B0D;margin-bottom:26px}
.saree-login-brand span{color:#6FCB00}
.saree-login h2{font-size:24px;font-weight:900;color:#141B0D;margin:0 0 6px}
.saree-login-sub{font-size:12px;color:#6D7466;line-height:1.9;margin:0 0 18px}
.saree-login-field{display:flex;align-items:center;gap:8px;background:#F3F4F1;border-radius:16px;padding:4px;margin:0 0 12px}
.saree-login-field input{flex:1;min-width:0;border:0;outline:0;background:transparent;padding:12px;font-size:13px;color:#141B0D}
.saree-login-prefix{display:flex;align-items:center;gap:6px;background:#fff;border-radius:12px;padding:10px 12px;font-size:13px;font-weight:800;color:#141B0D;flex:none}
.saree-flag-eg{width:20px;height:14px;border-radius:2px;background:linear-gradient(#CE1126 33%,#fff 33% 66%,#000 66%);display:inline-block}
.saree-login-pass button{background:transparent;border:0;color:#6D7466;font-size:10px;padding:0 10px}
.saree-login-submit{margin:4px 0 0}
.saree-login-or{display:flex;align-items:center;gap:10px;color:#9AA08F;font-size:11px;margin:14px 0}
.saree-login-or span{flex:1;height:1px;background:#E9EDE4}
.saree-login-alt{margin:0}
.saree-login-terms{font-size:10px;color:#9AA08F;text-align:center;margin:16px 0 0}
.saree-login-terms button{background:none;border:0;color:#57A300;font-size:10px;font-weight:800;padding:0}
.saree-splash{position:fixed;inset:0;z-index:2147483646;background:#fff;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:14px;overflow:hidden}
.saree-splash-blob{position:absolute;width:340px;height:340px;border-radius:50%;background:#F1FAD3;opacity:.8}
.saree-splash-blob.tl{top:-140px;right:-120px}
.saree-splash-blob.br{bottom:-150px;left:-120px}
.saree-splash-art{width:min(320px,74vw);background:#F1FAD3;border-radius:32px;padding:34px 22px;position:relative;display:grid;place-items:center;color:#141B0D}
.saree-splash-word{font-size:38px;font-weight:900;color:#141B0D}
.saree-splash-word span{color:#6FCB00}
.saree-splash-tag{margin:0;font-size:13px;color:#6D7466}
.saree-splash-dots{display:flex;gap:7px;align-items:center}
.saree-splash-dots i{width:7px;height:7px;border-radius:50%;background:#DDE3D5}
.saree-splash-dots b{width:22px;height:7px;border-radius:99px;background:#6FCB00}
/* -------- Saree build 309: profile, order rating, reorder, delivery menu -------- */"""
csspath='src/style.css'
csscur=io.open(csspath,encoding='utf-8').read()
assert 'saree-login-brand' not in csscur
io.open(csspath,'w',encoding='utf-8').write(csscur+'\n'+CSS)

io.open(p, 'w', encoding='utf-8').write(s)

# ---- 7) PrivateTripMap: Arabic geo error on denied permission ----
pt = io.open('src/PrivateTripMap.tsx', encoding='utf-8').read()
old_geo = "catch(e:any){setGeoError(String(e?.message||'تعذر تحديد موقعك. شغّل GPS أو اختر الانطلاق يدويًا.'))}"
new_geo = "catch(e:any){setGeoError(e&&e.code===1?'إذن الموقع مرفوض — فعّل الموقع من إعدادات الهاتف أو حدد نقطة الانطلاق من الخريطة':String(e?.message||'تعذر تحديد موقعك. شغّل GPS أو اختر الانطلاق يدويًا.'))}"
assert old_geo in pt, 'geo anchor'
pt = pt.replace(old_geo, new_geo)
io.open('src/PrivateTripMap.tsx', 'w', encoding='utf-8').write(pt)

# ---- 8) light ride map (style.css) ----
c = io.open('src/style.css', encoding='utf-8').read()
old_dark = "background:#17232b}.s3-trip-map{height:390px;width:100%;background:#17232b}.s3-trip-map .leaflet-tile-pane{filter:invert(1) hue-rotate(180deg) brightness(.82) contrast(.9) saturate(.72)}.s3-trip-map .leaflet-control-attribution{filter:invert(1);"
new_light = "background:#EDF2E4}.s3-trip-map{height:390px;width:100%;background:#EDF2E4}.s3-trip-map .leaflet-control-attribution{"
assert old_dark in c, 'map dark anchor'
c = c.replace(old_dark, new_light)
c = c.replace(".s3-trip-map .leaflet-control-zoom a{background:#202c35;color:#fff;border-color:#53616a}", ".s3-trip-map .leaflet-control-zoom a{background:#fff;color:#141B0D;border-color:#DDE3D5}")
c = c.replace(".s3-trip-map-hint{position:absolute;z-index:500;top:10px;right:10px;max-width:75%;padding:8px 11px;border-radius:10px;background:#14212be8;color:#fff;", ".s3-trip-map-hint{position:absolute;z-index:500;top:10px;right:10px;max-width:75%;padding:8px 11px;border-radius:10px;background:#ffffffee;color:#141B0D;box-shadow:0 2px 10px rgba(20,27,13,.08);")
c = c.replace(".s3-trip-legend{position:absolute;z-index:500;bottom:12px;right:12px;display:flex;gap:12px;background:#14212be8;color:#fff;", ".s3-trip-legend{position:absolute;z-index:500;bottom:12px;right:12px;display:flex;gap:12px;background:#ffffffee;color:#141B0D;box-shadow:0 2px 10px rgba(20,27,13,.08);")
io.open('src/style.css', 'w', encoding='utf-8').write(c)

# ---- 9) keep merchant sales breakdown + courier availability phrase (functions + tests) ----
s2 = io.open('src/App.tsx', encoding='utf-8').read()
old_h = "  <h2 className=\"saree-merchant-section\">طلبات جديدة</h2>"
new_h = """  <details className="saree-merchant-sales"><summary>ملخص مبيعات اليوم</summary>{merchantStoreRows.map(m=>{const completed=merchantToday(m.id);const gross=completed.reduce((sum,o)=>sum+o.total,0);const rate=Number(m.commission_percent||0);return <article className="order-card" key={m.id}><b>{m.name}</b><p>{completed.length} طلب تم تسليمه اليوم</p><div className="summary-row"><span>إجمالي قيمة المنتجات</span><b>{money(gross)}</b></div><div className="summary-row"><span>عمولة المنصة التقديرية ({rate}%)</span><b>{money(gross*rate/100)}</b></div><div className="summary-row total"><span>صافي مستحق المتجر التقديري</span><b>{money(gross*(1-rate/100))}</b></div><small className="muted">تقدير للطلبات المسلّمة اليوم، وليس كشف تسوية مالية نهائيًا.</small></article>})}</details>
  <h2 className="saree-merchant-section">طلبات جديدة</h2>"""
assert s2.count(old_h) == 1, 'sales anchor'
s2 = s2.replace(old_h, new_h)
old_r = '<small>مندوب سريع · ملوى</small>'
new_r = "<small>مندوب سريع · ملوى · {driverOnline?'متاح لاستلام الطلبات':'غير متاح'}</small>"
assert s2.count(old_r) == 1, 'rider anchor'
s2 = s2.replace(old_r, new_r)
io.open('src/App.tsx', 'w', encoding='utf-8').write(s2)

# ---- 10) sales details CSS ----
c = io.open('src/style.css', encoding='utf-8').read()
c += "\n.saree-merchant-sales{background:#fff;border:1px solid #E9EDE4;border-radius:16px;padding:10px 14px;margin-bottom:6px}\n.saree-merchant-sales summary{font-size:12px;font-weight:800;color:#141B0D;cursor:pointer}\n"
io.open('src/style.css', 'w', encoding='utf-8').write(c)
print('patch-screens-313 applied ok')
