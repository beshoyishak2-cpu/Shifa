"""Build 312: restyle orders, tracking, profile and ride screens to the references.

Applied after patch-screens-311.py. Covers:
  * customer orders page: back circle + title, جارية/سابقة toggle, reference
    order cards (thumb, status chip, items summary, lime تتبع الطلب or outline
    إعادة الطلب) with reorder + invoice kept working
  * tracking sheet: ETA chip, live steps (تم تأكيد الطلب / المطعم جهّزه /
    في الطريق / تم التوصيل), captain card with call/chat
  * profile: avatar + name/phone, stats row (طلبات، مشاوير، خصم), grouped
    menu cards with lime icon chips, red تسجيل الخروج; address form, favorites
    and about move into modals so nothing is lost
  * ride (مشاوير): reference heading, vehicle chips row, lime confirm button
  * all new CSS appended under 'build 312 screens'
"""
from pathlib import Path

app = Path("src/App.tsx")
trip = Path("src/PrivateTripMap.tsx")
css = Path("src/style.css")

text = app.read_text(encoding="utf-8")


def sub(old, new, label):
    global text
    if old not in text:
        raise SystemExit(f"missing anchor: {label}")
    text = text.replace(old, new, 1)


# --- icons
sub("import { Grid2X2, Coffee, Apple, Pill, Activity, ArrowLeft, Bike, Building2, CheckCircle2, Clock3, FileImage, Home, MapPin, Menu, Package, Plus, Search, ShieldCheck, ShoppingCart, Store, Truck, UserRound, Users, Wallet, X, Bell, Settings, ClipboardList, Navigation, Phone, Stethoscope, Moon, Sun, MessageCircle } from 'lucide-react';",
    "import { Grid2X2, Coffee, Apple, Pill, Activity, ArrowLeft, Bike, Building2, CheckCircle2, Clock3, FileImage, Home, MapPin, Menu, Package, Plus, Search, ShieldCheck, ShoppingCart, Store, Truck, UserRound, Users, Wallet, X, Bell, Settings, ClipboardList, Navigation, Phone, Stethoscope, Moon, Sun, MessageCircle, Heart, Globe, Info, LogOut, ChevronLeft, Star } from 'lucide-react';",
    "lucide imports")

# --- state: orders filter + tracking order
sub("const [searchKeyboardOpen,setSearchKeyboardOpen]=useState(false);const [allCats,setAllCats]=useState(false);",
    "const [searchKeyboardOpen,setSearchKeyboardOpen]=useState(false);const [allCats,setAllCats]=useState(false);const [orderFilter,setOrderFilter]=useState<'active'|'past'>('active');const [trackingOrder,setTrackingOrder]=useState<Order|null>(null);",
    "orders filter state")

# --- helpers + renderCustomerOrders, inserted before renderOrders
sub("const renderOrders=(filter:",
    """const arNum=(n:number|string)=>Number(n).toLocaleString('ar-EG');
const orderStep=(s:OrderStatus):number=>({'جديد':0,'تم القبول':1,'قيد التجهيز':2,'جاهز للاستلام':2,'تم تعيين مندوب':3,'في الطريق':3,'تم التسليم':4,'ملغي':0} as Record<string,number>)[s]??0;
const reorder=(o:Order)=>{if(!o.lines.length){notify('لا يمكن إعادة هذا الطلب تلقائيًا');return;}if(cartStore&&cartStore!==o.lines[0].storeId){notify('السلة تقبل الطلب من متجر واحد. أفرغ السلة أولًا.');return;}setCart(o.lines.map(l=>({productId:l.productId,storeId:l.storeId,qty:l.qty,options:l.options||[],...(l.note?{note:l.note}:{})})));setTab('cart');notify('تمت إعادة أصناف الطلب إلى السلة')};
const openTracking=(o:Order)=>{setTrackingOrder(o);setModal('tracking')};
const renderCustomerOrders=()=>{const active=(o:Order)=>o.status!=='تم التسليم'&&o.status!=='ملغي';const rows=orders.filter(o=>orderFilter==='active'?active(o):!active(o));return <section className="saree-orders-page"><div className="saree-orders-top"><button className="saree-circle-btn" onClick={()=>setTab('home')} aria-label="رجوع"><ArrowLeft size={18}/></button><h1>طلباتي</h1></div><div className="saree-orders-toggle"><button className={orderFilter==='active'?'on':''} onClick={()=>setOrderFilter('active')}>جارية</button><button className={orderFilter==='past'?'on':''} onClick={()=>setOrderFilter('past')}>سابقة</button></div>{rows.length===0?<Empty title={orderFilter==='active'?'لا توجد طلبات جارية':'لا توجد طلبات سابقة'} hint="اطلب من أي متجر وسيظهر طلبك هنا."/>:rows.map(o=>{const st=stores.find(s=>s.id===o.storeId);const items=o.lines.length?o.lines.map(l=>l.qty+' × '+(l.productName||'صنف')).join(' · '):o.kind;const live=active(o);return <article className="saree-order-card" key={o.id}><div className="saree-order-top"><div className="saree-order-info"><b>{o.storeName}</b><small>#{o.number} · {new Date(o.createdAt).toLocaleString('ar-EG',{day:'numeric',month:'long',hour:'numeric',minute:'2-digit'})}</small></div><span className={'saree-order-chip'+(live?' live':'')}>{o.status}</span><span className="saree-order-thumb">{st?.image?<img src={st.image} alt={st.name}/>:<span>{st?.icon||'🛍'}</span>}</span></div><p className="saree-order-lines"><span>{items}</span><b>{money(o.total+o.delivery)}</b></p>{live?<button className="saree-add-btn saree-order-cta" onClick={()=>openTracking(o)}>تتبع الطلب</button>:<button className="saree-order-reorder" onClick={()=>reorder(o)}>إعادة الطلب</button>}<div className="saree-order-sub"><button className="saree-order-invoice" onClick={()=>openInvoice(o)}>فاتورة</button></div></article>})}</section>};
const renderOrders=(filter:""",
    "renderCustomerOrders")

# --- customer orders tab uses the new renderer
sub("{role==='customer'&&tab==='orders'&&renderOrders('customer')}",
    "{role==='customer'&&tab==='orders'&&renderCustomerOrders()}",
    "customer orders tab")

# --- profile screen (replace the whole old profile block)
old_profile_start = "{role==='customer'&&tab==='profile'&&<><button className=\"outline full saree-issue-shortcut\""
i = text.index(old_profile_start)
j = text.index("{role==='customer'&&tab==='wallet'")
old_block = text[i:j].rstrip() + ""
new_profile = """{role==='customer'&&tab==='profile'&&<div className="saree-profile"><div className="saree-profile-head"><span className="saree-avatar">{(customer.name||'ضيف').trim().slice(0,1)||'ض'}</span><div className="saree-profile-id"><h1>{customer.name||'ضيف سريع'}</h1><p>{customer.phone||'بدون رقم'} · ملوى</p></div></div><div className="saree-profile-stats"><div className="saree-stat"><b>{arNum(orders.filter(o=>o.kind!=='مشوار خاص').length)}</b><small>طلب</small></div><div className="saree-stat"><b>{arNum(orders.filter(o=>o.kind==='مشوار خاص').length)}</b><small>مشاوير</small></div><div className="saree-stat"><b className="lime">١٠٪</b><small>خصم الشهر</small></div></div><div className="saree-profile-card"><button className="saree-menu-row" onClick={()=>setTab('orders')}><span className="saree-menu-ico"><ClipboardList size={18}/></span><b>طلباتي</b><ChevronLeft size={17} className="saree-menu-chev"/></button><button className="saree-menu-row" onClick={()=>setModal('profile-address')}><span className="saree-menu-ico"><MapPin size={18}/></span><b>عناويني</b><small>{address.name||'المنزل'}</small><ChevronLeft size={17} className="saree-menu-chev"/></button><button className="saree-menu-row" onClick={()=>setModal('profile-fav')}><span className="saree-menu-ico"><Heart size={18}/></span><b>المفضلة</b><small>{arNum(favProducts.length)} منتج</small><ChevronLeft size={17} className="saree-menu-chev"/></button></div><div className="saree-profile-card"><button className="saree-menu-row" onClick={()=>setTab('support')}><span className="saree-menu-ico"><MessageCircle size={18}/></span><b>الدعم والمساعدة</b><ChevronLeft size={17} className="saree-menu-chev"/></button><button className="saree-menu-row"><span className="saree-menu-ico"><Globe size={18}/></span><b>اللغة</b><small>العربية</small><ChevronLeft size={17} className="saree-menu-chev"/></button><button className="saree-menu-row" onClick={()=>setModal('about')}><span className="saree-menu-ico"><Info size={18}/></span><b>عن سريع</b><ChevronLeft size={17} className="saree-menu-chev"/></button></div><button className="saree-profile-card saree-menu-row saree-logout" onClick={async()=>{if(backendReady)await supabase?.auth.signOut();setSignedInPhone(null);notify('تم تسجيل الخروج')}}><span className="saree-menu-ico out"><LogOut size={18}/></span><b>تسجيل الخروج</b><ChevronLeft size={17} className="saree-menu-chev"/></button><button className="saree-issue-link" onClick={()=>setTab('issue-log')}>سجل المشاكل</button></div>}"""
text = text[:i] + new_profile + "\n " + text[j:]

# --- tracking + profile modals, inserted before the invoice modal
sub(" {modal==='invoice'&&invoiceOrder&&",
    """ {modal==='tracking'&&trackingOrder&&<div className="overlay saree-item-overlay" onClick={()=>setModal('')}><div className="dialog saree-item-sheet saree-tracking-sheet" onClick={e=>e.stopPropagation()}><div className="saree-track-map"><svg viewBox="0 0 390 240" className="saree-track-svg" aria-hidden="true"><rect width="390" height="240" fill="#EDF2E4"/><g fill="#DFE8D2"><rect x="20" y="18" width="70" height="46" rx="8"/><rect x="110" y="18" width="90" height="46" rx="8"/><rect x="220" y="18" width="70" height="46" rx="8"/><rect x="310" y="18" width="60" height="46" rx="8"/><rect x="20" y="84" width="70" height="60" rx="8"/><rect x="220" y="84" width="70" height="60" rx="8"/><rect x="20" y="164" width="90" height="56" rx="8"/><rect x="130" y="164" width="70" height="56" rx="8"/><rect x="310" y="84" width="60" height="60" rx="8"/><rect x="220" y="164" width="150" height="56" rx="8"/></g><rect x="126" y="84" width="78" height="60" rx="10" fill="#CBE79B"/><path d="M60 210 C 90 150, 130 160, 170 120 S 260 60, 320 40" stroke="#141B0D" strokeWidth="7" fill="none" strokeLinecap="round"/><path d="M60 210 C 90 150, 130 160, 170 120 S 260 60, 320 40" stroke="#6FCB00" strokeWidth="3" fill="none" strokeLinecap="round" strokeDasharray="2 10"/><circle cx="60" cy="210" r="10" fill="#6FCB00"/><circle cx="60" cy="210" r="4" fill="#fff"/><circle cx="320" cy="40" r="10" fill="#141B0D"/><circle cx="320" cy="40" r="4" fill="#fff"/><circle cx="205" cy="103" r="17" fill="#fff" stroke="#6FCB00" strokeWidth="3"/></svg><span className="saree-track-rider"><Bike size={17}/></span><span className="saree-track-eta"><Clock3 size={14}/> يوصل خلال {stores.find(s=>s.id===trackingOrder.storeId)?.eta||'٢٥ - ٣٥ دقيقة'}</span><button className="saree-circle-btn saree-track-back" onClick={()=>setModal('')} aria-label="رجوع"><ArrowLeft size={18}/></button></div><div className="saree-item-body saree-track-body"><div className="saree-track-head">{trackingOrder.status!=='تم التسليم'&&trackingOrder.status!=='ملغي'&&<span className="saree-live-chip">مباشر</span>}<div><h2>{trackingOrder.status==='تم التسليم'?'تم التوصيل':trackingOrder.status==='ملغي'?'طلب ملغي':trackingOrder.status==='في الطريق'?'في الطريق إليك':'طلبك قيد التنفيذ'}</h2><p className="muted">طلب #{trackingOrder.number} · {trackingOrder.storeName}</p></div></div><div className="saree-track-steps">{(['تم تأكيد الطلب','المطعم جهّزه','في الطريق','تم التوصيل'] as const).map((label,idx)=>{const rank=orderStep(trackingOrder.status);const done=idx<rank;const current=idx===rank&&trackingOrder.status!=='تم التسليم';return <div className={'saree-step'+(done?' done':'')+(current?' current':'')} key={label}><span className="saree-step-dot">{done?'✓':''}</span><small>{label}</small></div>})}<span className="saree-step-line"/><span className="saree-step-line fill" style={{width:Math.min(100,orderStep(trackingOrder.status)/4*100)+'%'}}/></div><div className="saree-captain"><span className="saree-captain-avatar">{(trackingOrder.driver||'ك').trim().slice(0,1)}</span><div className="saree-captain-info"><b>{trackingOrder.driver||'كابتن سريع'}</b><small><Star size={12} className="saree-star"/> ٤٫٩ · دراجة نارية</small></div><button className="saree-captain-btn" onClick={()=>notify('الاتصال بالكابتن يتاح بعد تعيينه رسميًا')} aria-label="اتصال"><Phone size={17}/></button><button className="saree-captain-btn chat" onClick={()=>{setModal('');setTab('support')}} aria-label="محادثة"><MessageCircle size={17}/></button></div></div></div></div>}
 {modal==='profile-address'&&<div className="overlay saree-item-overlay" onClick={()=>setModal('')}><div className="dialog saree-item-sheet" onClick={e=>e.stopPropagation()}><div className="saree-sheet-head"><h2>بياناتي وعناويني</h2><button className="saree-circle-btn" onClick={()=>setModal('')} aria-label="رجوع"><ArrowLeft size={18}/></button></div><div className="saree-item-body"><section className="panel form-panel saree-plain-form"><label>الاسم<input value={customer.name} onChange={e=>setCustomer({...customer,name:e.target.value})}/></label><label>رقم الهاتف<input inputMode="tel" value={customer.phone} onChange={e=>setCustomer({...customer,phone:e.target.value})} placeholder="01xxxxxxxxx"/></label><label>اسم العنوان<input value={address.name} onChange={e=>setAddress({...address,name:e.target.value})}/></label><label>المنطقة / القرية<input value={address.area} onChange={e=>setAddress({...address,area:e.target.value})}/></label><label>الشارع ورقم المنزل<input value={address.street} onChange={e=>setAddress({...address,street:e.target.value})} placeholder="اسم الشارع أو أقرب وصف"/></label><label>علامة مميزة<input value={address.landmark} onChange={e=>setAddress({...address,landmark:e.target.value})} placeholder="بجوار مسجد / مدرسة / محل معروف"/></label><button className="outline" onClick={locate}><Navigation size={16}/> تحديد موقعي GPS</button>{address.lat&&<small className="hint">{address.lat.toFixed(5)}, {address.lng?.toFixed(5)}</small>}<button className="saree-add-btn" onClick={()=>{notify('تم حفظ العنوان على هذا الجهاز');setModal('')}}>حفظ البيانات والعنوان</button></section></div></div></div>}
 {modal==='profile-fav'&&<div className="overlay saree-item-overlay" onClick={()=>setModal('')}><div className="dialog saree-item-sheet" onClick={e=>e.stopPropagation()}><div className="saree-sheet-head"><h2>المفضلة</h2><button className="saree-circle-btn" onClick={()=>setModal('')} aria-label="رجوع"><ArrowLeft size={18}/></button></div><div className="saree-item-body">{favProducts.length===0?<Empty title="لا توجد منتجات مفضلة" hint="اضغط على القلب في صفحة أي منتج لحفظه هنا."/>:favProducts.map(pid=>{const p=products.find(x=>x.id===pid);if(!p)return null;const st=stores.find(s=>s.id===p.storeId);return <div className="saree-fav-row" key={pid}><span className="saree-order-thumb">{p.imageUrl?<img src={p.imageUrl} alt={p.name}/>:<span>{p.emoji}</span>}</span><div className="saree-order-info"><b>{p.name}</b><small>{st?.name||''} · {money(p.price)}</small></div><button className="saree-fav-remove" onClick={()=>toggleFavProduct(pid)} aria-label="إزالة من المفضلة"><Heart size={17}/></button></div>})}</div></div></div>}
 {modal==='about'&&<div className="overlay saree-item-overlay" onClick={()=>setModal('')}><div className="dialog saree-item-sheet" onClick={e=>e.stopPropagation()}><div className="saree-sheet-head"><h2>عن سريع</h2><button className="saree-circle-btn" onClick={()=>setModal('')} aria-label="رجوع"><ArrowLeft size={18}/></button></div><div className="saree-item-body"><p className="saree-about">سريع — توصيل محلي داخل ملوى: مطاعم، بقالة، خضار، صيدليات ومشاوير. الدفع عند الاستلام ومندوبون من أهالي المنطقة.</p><p className="saree-about muted">الإصدار التجريبي ٣١٢ · © 2026 سريع</p></div></div></div>}
 {modal==='invoice'&&invoiceOrder&&""",
    "tracking + profile modals")

app.write_text(text, encoding="utf-8")
print("build 312 part 1 applied: orders, tracking, profile")

# --- ride screen (PrivateTripMap): reference heading + vehicle chips + lime button
t2 = trip.read_text(encoding="utf-8")


def sub2(old, new, label):
    global t2
    if old not in t2:
        raise SystemExit(f"missing anchor (trip): {label}")
    t2 = t2.replace(old, new, 1)


sub2("import {Crosshair,MapPin,Search,Navigation,Clock3,Route,Wallet,AlertCircle,Loader2,LocateFixed} from 'lucide-react';",
     "import {Crosshair,MapPin,Search,Navigation,Clock3,Route,Wallet,AlertCircle,Loader2,LocateFixed,Bike,Truck,Package} from 'lucide-react';",
     "trip lucide imports")


sub2('<div className="s3-trip-heading"><div><span className="s3-trip-kicker">خدمة المشاوير داخل ملوى</span><h1>مشوار خاص</h1><p>حدد الانطلاق والوجهة وسنحسب الطريق والوقت تلقائيًا</p></div><span className="s3-trip-heading-icon"><Navigation size={22}/></span></div>',
     '<div className="s3-trip-heading"><div><span className="s3-trip-kicker">خدمة المشاوير داخل ملوى</span><h1>اطلب مشوار</h1></div><span className="s3-trip-heading-icon"><Navigation size={22}/></span></div>',
     "trip heading")

sub2('<div className="s3-trip-metrics">',
     '''<div className="s3-trip-vehicles"><button type="button" className="on"><Bike size={20}/><b>دراجة</b><small>٥ د</small><span>{fare!==null?money(fare):'١٥ ج'}</span></button><button type="button" disabled><Truck size={20}/><b>عربية</b><small>قريباً</small><span>—</span></button><button type="button" disabled><Package size={20}/><b>توصيل حاجة</b><small>قريباً</small><span>—</span></button></div><div className="s3-trip-metrics">''',
     "vehicle chips")

trip.write_text(t2, encoding="utf-8")
print("build 312 part 2 applied: ride screen")

# --- CSS
css_text = css.read_text(encoding="utf-8")
css_text += """

/* build 312 screens: orders, tracking, profile, ride */
.saree-orders-page{display:flex;flex-direction:column;gap:14px}
.saree-orders-top{display:flex;align-items:center;justify-content:center;position:relative;padding:4px 0}
.saree-orders-top h1{font-size:20px;font-weight:800;margin:0}
.saree-orders-top .saree-circle-btn{position:absolute;inset-inline-end:0}
.saree-orders-toggle{display:flex;gap:8px;justify-content:center}
.saree-orders-toggle button{border:0;border-radius:999px;padding:10px 34px;font:inherit;font-size:13px;font-weight:700;background:#fff;color:#141B0D;box-shadow:0 2px 10px #0f1a0512}
.saree-orders-toggle button.on{background:#141B0D;color:#fff}
.saree-order-card{background:#fff;border-radius:20px;padding:16px;box-shadow:0 4px 18px #0f1a050f;display:flex;flex-direction:column;gap:10px}
.saree-order-top{display:flex;align-items:center;gap:12px}
.saree-order-info{flex:1;min-width:0;display:flex;flex-direction:column;gap:3px}
.saree-order-info b{font-size:15px;font-weight:800}
.saree-order-info small{font-size:11px;color:#8A9184}
.saree-order-thumb{width:56px;height:56px;flex:none;border-radius:16px;background:#F1FAD3;display:flex;align-items:center;justify-content:center;font-size:26px;overflow:hidden}
.saree-order-thumb img{width:100%;height:100%;object-fit:cover}
.saree-order-chip{flex:none;border-radius:999px;padding:7px 13px;font-size:11px;font-weight:700;background:#F3F4F1;color:#6B7264}
.saree-order-chip.live{background:#F1FAD3;color:#4A8F00}
.saree-order-lines{display:flex;align-items:center;justify-content:space-between;gap:10px;border-top:1px solid #F0F2EC;padding-top:12px;margin:0;font-size:12px;color:#6B7264}
.saree-order-lines b{color:#141B0D;font-size:14px}
.saree-order-cta{border-radius:999px}
.saree-order-reorder{border:1.5px solid #E4E7DE;background:#fff;border-radius:999px;padding:13px;font:inherit;font-size:14px;font-weight:800;color:#141B0D}
.saree-order-sub{display:flex;justify-content:flex-start}
.saree-order-invoice{background:none;border:0;color:#8A9184;font:inherit;font-size:11px;text-decoration:underline;padding:0}
.saree-tracking-sheet{padding:0;overflow:hidden}
.saree-track-map{position:relative}
.saree-track-rider{position:absolute;left:52.56%;top:42.9%;transform:translate(-50%,-50%);width:20px;height:20px;display:flex;align-items:center;justify-content:center;color:#141B0D;pointer-events:none}
.saree-order-thumb>span{font-size:15px;font-weight:700;white-space:nowrap;overflow:hidden;max-width:100%;padding:0 4px}
.saree-track-svg{display:block;width:100%;height:auto}
.saree-track-eta{position:absolute;top:14px;inset-inline-start:14px;display:inline-flex;align-items:center;gap:6px;background:#F1FAD3;color:#4A8F00;border-radius:999px;padding:8px 14px;font-size:12px;font-weight:800;box-shadow:0 4px 14px #0f1a0518}
.saree-track-back{position:absolute;top:14px;inset-inline-end:14px}
.saree-track-body{padding-top:18px}
.saree-track-head{display:flex;align-items:flex-start;gap:10px;flex-direction:row-reverse;justify-content:flex-end}
.saree-track-head h2{font-size:20px;font-weight:800;margin:0 0 4px}
.saree-track-head p{margin:0;font-size:12px}
.saree-live-chip{flex:none;background:#141B0D;color:#fff;border-radius:999px;padding:7px 14px;font-size:11px;font-weight:800}
.saree-track-steps{position:relative;display:flex;justify-content:space-between;margin:22px 0 6px;padding:0 4px}
.saree-step{position:relative;z-index:1;display:flex;flex-direction:column;align-items:center;gap:7px;width:64px}
.saree-step-dot{width:26px;height:26px;border-radius:50%;background:#EEF0EA;color:#fff;display:flex;align-items:center;justify-content:center;font-size:13px;font-weight:800;border:3px solid #EEF0EA}
.saree-step small{font-size:10px;color:#8A9184;text-align:center;font-weight:700}
.saree-step.done .saree-step-dot{background:#6FCB00;border-color:#6FCB00}
.saree-step.done small{color:#141B0D}
.saree-step.current .saree-step-dot{background:#fff;border-color:#6FCB00;box-shadow:0 0 0 4px #F1FAD3}
.saree-step.current small{color:#4A8F00;font-weight:800}
.saree-step-line{position:absolute;top:16px;inset-inline:32px;height:3px;border-radius:3px;background:#EEF0EA;z-index:0}
.saree-step-line.fill{background:#6FCB00;transition:width .4s}
.saree-captain{display:flex;align-items:center;gap:12px;background:#F7F8F4;border-radius:18px;padding:14px;margin-top:18px}
.saree-captain-avatar{width:46px;height:46px;flex:none;border-radius:50%;background:#F1FAD3;color:#4A8F00;display:flex;align-items:center;justify-content:center;font-size:20px;font-weight:800}
.saree-captain-info{flex:1;min-width:0;display:flex;flex-direction:column;gap:3px}
.saree-captain-info b{font-size:14px;font-weight:800}
.saree-captain-info small{font-size:11px;color:#8A9184;display:flex;align-items:center;gap:4px}
.saree-star{color:#F5B800}
.saree-captain-btn{width:42px;height:42px;flex:none;border-radius:50%;border:1px solid #E4E7DE;background:#fff;color:#141B0D;display:flex;align-items:center;justify-content:center}
.saree-captain-btn.chat{border:0;background:#6FCB00;color:#fff}
.saree-profile{display:flex;flex-direction:column;gap:14px}
.saree-profile-head{display:flex;align-items:center;gap:14px;padding:6px 2px}
.saree-avatar{width:64px;height:64px;flex:none;border-radius:50%;background:#6FCB00;color:#fff;display:flex;align-items:center;justify-content:center;font-size:26px;font-weight:800}
.saree-profile-id h1{font-size:19px;font-weight:800;margin:0 0 3px}
.saree-profile-id p{margin:0;font-size:12px;color:#8A9184}
.saree-profile-stats{display:grid;grid-template-columns:repeat(3,1fr);gap:10px}
.saree-stat{background:#fff;border-radius:16px;padding:14px 8px;text-align:center;box-shadow:0 2px 10px #0f1a050c;display:flex;flex-direction:column;gap:4px}
.saree-stat b{font-size:17px;font-weight:800}
.saree-stat b.lime{color:#4A8F00}
.saree-stat small{font-size:11px;color:#8A9184}
.saree-profile-card{background:#fff;border-radius:18px;box-shadow:0 2px 12px #0f1a050c;overflow:hidden;display:flex;flex-direction:column}
.saree-menu-row{display:flex;align-items:center;gap:12px;padding:14px 16px;background:none;border:0;font:inherit;text-align:start;color:#141B0D}
.saree-menu-row+.saree-menu-row{border-top:1px solid #F0F2EC}
.saree-menu-ico{width:38px;height:38px;flex:none;border-radius:12px;background:#F1FAD3;color:#4A8F00;display:flex;align-items:center;justify-content:center}
.saree-menu-ico.out{background:#FDECEA;color:#D24A43}
.saree-menu-row b{flex:1;font-size:14px;font-weight:800}
.saree-menu-row small{font-size:11px;color:#8A9184}
.saree-menu-chev{color:#B9BFB2;flex:none}
.saree-logout b{color:#D24A43}
.saree-issue-link{align-self:center;background:none;border:0;color:#8A9184;font:inherit;font-size:11px;text-decoration:underline}
.saree-plain-form{border:0;box-shadow:none;padding:0;background:transparent}
.saree-fav-row{display:flex;align-items:center;gap:12px;padding:10px 0;border-bottom:1px solid #F0F2EC}
.saree-fav-row:last-child{border-bottom:0}
.saree-fav-remove{width:38px;height:38px;flex:none;border-radius:50%;border:0;background:#FDECEA;color:#D24A43;display:flex;align-items:center;justify-content:center}
.saree-about{font-size:13px;line-height:1.9;margin:0 0 10px}
.s3-trip-vehicles{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin:12px 0}
.s3-trip-vehicles button{border:1.5px solid #E4E7DE;background:#fff;border-radius:16px;padding:12px 8px;display:flex;flex-direction:column;align-items:center;gap:4px;font:inherit;color:#141B0D}
.s3-trip-vehicles button b{font-size:12px;font-weight:800}
.s3-trip-vehicles button small{font-size:10px;color:#8A9184}
.s3-trip-vehicles button span{font-size:13px;font-weight:800;color:#4A8F00}
.s3-trip-vehicles button.on{border-color:#6FCB00;background:#F9FEEE;box-shadow:0 4px 14px #6fcb0022}
.s3-trip-vehicles button:disabled{opacity:.55}
.s3-trip-confirm{background:#6FCB00!important;border-radius:999px!important;font-weight:800!important}
.s3-trip-map-wrap{border-radius:20px;overflow:hidden}
"""
css.write_text(css_text, encoding="utf-8")
print("build 312 part 3 applied: CSS")
