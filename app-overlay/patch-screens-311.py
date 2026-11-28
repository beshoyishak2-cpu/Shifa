#!/usr/bin/env python3
"""Build 311: restyle search, item detail and checkout screens to the agreed references.
Visual-only; keeps every function (add to cart, options, placeOrder, search filter) working."""
import re
from pathlib import Path

APP = Path('src/App.tsx')
CSS = Path('src/style.css')

def sub(text, old, new, anchor, count=1):
    if old not in text:
        raise SystemExit(f'missing anchor: {anchor}')
    return text.replace(old, new, count)

app = APP.read_text(encoding='utf-8')

# 1. demo option groups so the item sheet shows size chips + add-ons in demo mode
demo_groups_anchor = "const SAREE_DEMO_MERCHANT_ROWS=SAREE_DEMO_STORES.map(x=>({id:x.id,name:x.name,is_open:true,is_active:true,commission_percent:0,delivery_fee:x.fee,min_order:x.min,image_url:null}));"
demo_groups = demo_groups_anchor + """
const SAREE_DEMO_OPTION_GROUPS:Record<string,ProductOptionGroup[]>={'demo-r1':[{id:'dg-size',name:'الحجم',selection_type:'single',min_select:1,max_select:1,is_required:true,sort_order:1,product_option_values:[{id:'dgv-s',name:'صغير · ١٢٥ ج',price_delta:-20,is_available:true,sort_order:1},{id:'dgv-m',name:'وسط · ١٤٥ ج',price_delta:0,is_available:true,sort_order:2},{id:'dgv-l',name:'كبير · ١٧٥ ج',price_delta:30,is_available:true,sort_order:3}]},{id:'dg-add',name:'إضافات',selection_type:'multiple',min_select:0,max_select:5,is_required:false,sort_order:2,product_option_values:[{id:'dga-1',name:'شطة زيادة',price_delta:10,is_available:true,sort_order:1},{id:'dga-2',name:'دقة إضافية',price_delta:10,is_available:true,sort_order:2},{id:'dga-3',name:'عيش محمص',price_delta:0,is_available:true,sort_order:3}]}]};
"""
app = sub(app, demo_groups_anchor, demo_groups, 'demo option groups')

# 2. extra state for the item sheet and search recents
state_anchor = "const lineKey=(line:CartLine)=>"
state_add = """const [optionQty,setOptionQty]=useState(1),[itemNoteDraft,setItemNoteDraft]=useState(''),[favProducts,setFavProducts]=useState<string[]>(()=>load('fav-products',[])),[recentSearches,setRecentSearches]=useState<string[]>(()=>load('recent-searches',[]));
const rememberSearch=(term:string)=>{const t=term.trim();if(t.length<2)return;setRecentSearches(v=>{const n=[t,...v.filter(x=>x!==t)].slice(0,6);save('recent-searches',n);return n;})};
const toggleFavProduct=(id:string)=>setFavProducts(v=>{const n=v.includes(id)?v.filter(x=>x!==id):[...v,id];save('fav-products',n);return n;});
"""
app = sub(app, state_anchor, state_add + state_anchor, 'item sheet state')

# 3. CartLine gains an optional note; lineKey includes it
app = sub(app,
  "type CartLine = {productId:string;storeId:string;qty:number;productName?:string;unitPrice?:number;lineTotal?:number;options?:CartOptionGroup[]};",
  "type CartLine = {productId:string;storeId:string;qty:number;productName?:string;unitPrice?:number;lineTotal?:number;options?:CartOptionGroup[];note?:string};",
  'CartLine type')
app = sub(app,
  "const lineKey=(line:CartLine)=>line.productId+':'+(line.options||[]).map(g=>g.groupId+'='+[...g.valueIds].sort().join(',')).sort().join('|');",
  "const lineKey=(line:CartLine)=>line.productId+':'+(line.note||'')+':'+(line.options||[]).map(g=>g.groupId+'='+[...g.valueIds].sort().join(',')).sort().join('|');",
  'lineKey with note')

# 4. add() accepts qty and note
app = sub(app,
  "const add=(p:Product,options:CartOptionGroup[]=[] )=>{if(cartStore&&cartStore!==p.storeId){notify('السلة تقبل الطلب من متجر واحد. أفرغ السلة أو أكمل الطلب الحالي أولًا.');return;}const candidate:CartLine={productId:p.id,storeId:p.storeId,qty:1,options};const key=lineKey(candidate);setCart(c=>{const old=c.find(x=>lineKey(x)===key);return old?c.map(x=>lineKey(x)===key?{...x,qty:x.qty+1}:x):[...c,candidate]});notify('تمت الإضافة إلى السلة')};",
  "const add=(p:Product,options:CartOptionGroup[]=[],qty:number=1,note:string='')=>{if(cartStore&&cartStore!==p.storeId){notify('السلة تقبل الطلب من متجر واحد. أفرغ السلة أو أكمل الطلب الحالي أولًا.');return;}const candidate:CartLine={productId:p.id,storeId:p.storeId,qty,options,...(note?{note}:{})};const key=lineKey(candidate);setCart(c=>{const old=c.find(x=>lineKey(x)===key);return old?c.map(x=>lineKey(x)===key?{...x,qty:x.qty+qty}:x):[...c,candidate]});notify('تمت الإضافة إلى السلة')};",
  'add with qty and note')

# 5. tapping a product opens the item sheet (with demo groups in demo mode); add button quick-adds when no groups
app = sub(app,
  "const beginAddProduct=async(p:Product)=>{if(cartStore&&cartStore!==p.storeId){notify('السلة تقبل الطلب من متجر واحد. أفرغ السلة أو أكمل الطلب الحالي أولًا.');return;}if(!backendReady||!supabase||!isUuid(p.id)){add(p);return;}setOptionLoading(true);try{const groups=await loadProductOptions(p.id);if(!groups.length){add(p);return;}setOptionProduct(p);setOptionGroups(groups);setOptionSelections({});setModal('product-options')}catch(e){notify('تعذر تحميل اختيارات المنتج: '+(e instanceof Error?e.message:'خطأ غير معروف'))}finally{setOptionLoading(false)}};",
  "const openItemSheet=async(p:Product)=>{if(cartStore&&cartStore!==p.storeId){notify('السلة تقبل الطلب من متجر واحد. أفرغ السلة أو أكمل الطلب الحالي أولًا.');return;}setOptionLoading(true);try{const groups=(backendReady&&supabase&&isUuid(p.id))?await loadProductOptions(p.id):(SAREE_DEMO_OPTION_GROUPS[p.id]||[]);setOptionProduct(p);setOptionGroups(groups);setOptionSelections({});setOptionQty(1);setItemNoteDraft('');setModal('product-options')}catch(e){notify('تعذر تحميل اختيارات المنتج: '+(e instanceof Error?e.message:'خطأ غير معروف'))}finally{setOptionLoading(false)}};\n const beginAddProduct=async(p:Product)=>{if(cartStore&&cartStore!==p.storeId){notify('السلة تقبل الطلب من متجر واحد. أفرغ السلة أو أكمل الطلب الحالي أولًا.');return;}if(!backendReady||!supabase||!isUuid(p.id)){const groups=SAREE_DEMO_OPTION_GROUPS[p.id]||[];if(!groups.length){add(p);return;}void openItemSheet(p);return;}setOptionLoading(true);try{const groups=await loadProductOptions(p.id);if(!groups.length){add(p);return;}setOptionProduct(p);setOptionGroups(groups);setOptionSelections({});setOptionQty(1);setItemNoteDraft('');setModal('product-options')}catch(e){notify('تعذر تحميل اختيارات المنتج: '+(e instanceof Error?e.message:'خطأ غير معروف'))}finally{setOptionLoading(false)}};",
  'openItemSheet + beginAddProduct')

# 6. confirmProductOptions passes qty and note
app = sub(app,
  "add(optionProduct,selected);setModal('');setOptionProduct(null)};",
  "add(optionProduct,selected,optionQty,itemNoteDraft.trim());setModal('');setOptionProduct(null)};",
  'confirm with qty and note')

APP.write_text(app, encoding='utf-8')
print('build 311 part 1 applied: state, demo groups, add/beginAddProduct/confirm')

# ===================== part 2: JSX restyles =====================
app = APP.read_text(encoding='utf-8')

# unit price of the item sheet (base + selected deltas)
app = sub(app,
  "const confirmProductOptions=()=>",
  "const optionSheetUnit=optionProduct?optionProduct.price+optionGroups.reduce((sum,g)=>sum+g.product_option_values.filter(v=>(optionSelections[g.id]||[]).includes(v.id)).reduce((a,v)=>a+Number(v.price_delta),0),0):0;\n const confirmProductOptions=()=>",
  'optionSheetUnit')

# ---- item detail sheet (replaces the options dialog) ----
lines = app.split('\n')
for i, l in enumerate(lines):
    if "{modal==='product-options'" in l:
        lines[i] = ''' {modal==='product-options'&&optionProduct&&<div className="overlay saree-item-overlay" onClick={()=>{setModal('');setOptionProduct(null)}}><div className="dialog saree-item-sheet" onClick={e=>e.stopPropagation()}><div className="saree-item-hero">{optionProduct.imageUrl?<img src={optionProduct.imageUrl} alt={optionProduct.name}/>:<span className="saree-item-emoji">{optionProduct.emoji}</span>}<button className="saree-circle-btn saree-item-fav" onClick={()=>toggleFavProduct(optionProduct.id)} aria-label="مفضلة"><span className={favProducts.includes(optionProduct.id)?'on':''}>♥</span></button><button className="saree-circle-btn saree-item-back" onClick={()=>{setModal('');setOptionProduct(null)}} aria-label="رجوع"><ArrowLeft size={18}/></button></div><div className="saree-item-body"><div className="saree-item-head"><h2>{optionProduct.name}</h2><b>{money(optionSheetUnit)}</b></div><p className="saree-item-meta">★ {stores.find(s=>s.id===optionProduct.storeId)?.rating} · {stores.find(s=>s.id===optionProduct.storeId)?.eta} · من {stores.find(s=>s.id===optionProduct.storeId)?.name}</p><p className="saree-item-desc">{optionProduct.description}</p>{optionGroups.map(g=>g.selection_type==='single'?<section className="saree-item-sec" key={g.id}><h3>{g.name}</h3><div className="saree-chips">{g.product_option_values.map(v=>{const on=(optionSelections[g.id]||[]).includes(v.id);return <button type="button" key={v.id} className={on?'on':''} onClick={()=>toggleOptionValue(g,v.id)}>{v.name}</button>})}</div></section>:<section className="saree-item-sec" key={g.id}><h3>{g.name}</h3><div className="saree-addons">{g.product_option_values.map(v=>{const on=(optionSelections[g.id]||[]).includes(v.id);return <button type="button" key={v.id} className={on?'on':''} onClick={()=>toggleOptionValue(g,v.id)}><span className="saree-addon-txt"><b>{v.name}</b><small>{Number(v.price_delta)>0?'+ '+money(Number(v.price_delta)):'مجاناً'}</small></span><span className="saree-addon-plus">+</span></button>})}</div></section>)}<input className="saree-item-notes" value={itemNoteDraft} onChange={e=>setItemNoteDraft(e.target.value)} placeholder="ملاحظات للمطعم (اختياري)…"/><div className="saree-item-foot"><button className="saree-add-btn" onClick={confirmProductOptions}>أضف للسلة · {money(optionSheetUnit*optionQty)}</button><div className="saree-qty"><button onClick={()=>setOptionQty(q=>Math.max(1,q-1))} aria-label="أقل">−</button><b>{optionQty}</b><button className="up" onClick={()=>setOptionQty(q=>q+1)} aria-label="أكتر">+</button></div></div></div></div></div>}'''
        break
else:
    raise SystemExit('missing anchor: product-options modal line')

# ---- checkout sheet ----
for i, l in enumerate(lines):
    if "{modal==='checkout'" in l:
        lines[i] = ''' {modal==='checkout'&&<div className="overlay saree-item-overlay" onClick={()=>setModal('')}><div className="dialog saree-item-sheet saree-checkout-sheet" onClick={e=>e.stopPropagation()}><div className="saree-sheet-head"><h2>إتمام الطلب</h2><button className="saree-circle-btn" onClick={()=>setModal('')} aria-label="رجوع"><ArrowLeft size={18}/></button></div><div className="saree-item-body"><button className="saree-info-card" onClick={()=>window.dispatchEvent(new Event("saree3:open-address"))}><span className="saree-info-icon"><MapPin size={19}/></span><span className="saree-info-text"><b>التوصيل إلى: {address.name||'المنزل'}</b><small>{[address.area,address.street,address.landmark,address.unit||''].map(x=>String(x||'').trim()).filter(Boolean).concat(address.area==='وسط ملوى'&&!address.street&&!address.landmark&&!address.unit?['المنيا']:[]).join('، ')||'وسط ملوى، المنيا'}</small></span><span className="saree-info-link">تغيير</span></button><div className="saree-info-card"><span className="saree-info-icon"><Clock3 size={19}/></span><span className="saree-info-text"><b>التوصيل خلال {stores.find(s=>s.id===cartStore)?.eta||'٢٥ - ٣٥ دقيقة'}</b><small>أقرب مندوب متاح في منطقتك</small></span></div><h3 className="saree-pay-title">طريقة الدفع</h3><button className={'saree-pay-card'+(payment==='الدفع عند الاستلام'?' on':'')} onClick={()=>setPayment('الدفع عند الاستلام')}><span className="saree-info-icon"><Wallet size={18}/></span><span className="saree-info-text"><b>كاش عند الاستلام</b><small>ادفع للمندوب لما الطلب يوصلك</small></span>{payment==='الدفع عند الاستلام'&&<span className="saree-pay-check">✓</span>}</button><button className="saree-pay-card off" disabled><span className="saree-info-icon"><Wallet size={18}/></span><span className="saree-info-text"><b>محفظة سريع</b><small>قريباً</small></span></button>{!backendReady&&<div className="saree-checkout-fields"><label>اسم العميل<input value={customer.name} onChange={e=>setCustomer((v:any)=>({...v,name:e.target.value}))} placeholder="عميل تجريبي"/></label><label>رقم الهاتف<input type="tel" inputMode="tel" value={customer.phone} onChange={e=>setCustomer((v:any)=>({...v,phone:e.target.value}))} placeholder="01000000000"/></label></div>}<textarea className="saree-item-notes saree-checkout-notes" value={notes} onChange={e=>setNotes(e.target.value)} placeholder="ملاحظات للمتجر (اختياري)…"/><div className="saree-summary-card"><div className="saree-sum-row"><span>{count} أصناف من {stores.find(s=>s.id===cartStore)?.name||'المتجر'}</span><b>{money(subtotal)}</b></div><div className="saree-sum-row"><span>التوصيل</span><b>{money(delivery)}</b></div><div className="saree-sum-row total"><span>الإجمالي</span><b>{money(total)}</b></div></div><button className="saree-add-btn saree-confirm-btn" disabled={payment!=='الدفع عند الاستلام'} onClick={placeOrder}>تأكيد الطلب · {money(total)}</button></div></div></div>}'''
        break
else:
    raise SystemExit('missing anchor: checkout modal line')
app = '\n'.join(lines)

# ---- search screen ----
app = sub(app,
  '<div className="page-title"><div><h1>ابحث في سريع</h1><p className="muted">دور على متجر أو منتج داخل ملوى</p></div></div>',
  '<div className="saree-search-top"><button className="saree-circle-btn" onClick={()=>setTab(\'home\')} aria-label="رجوع"><ArrowLeft size={18}/></button>',
  'search page title')
app = sub(app,
  "{query&&<button aria-label=\"مسح البحث\" onClick={()=>setQuery('')}><X size={18}/></button>}</div>",
  "{query&&<button aria-label=\"مسح البحث\" onClick={()=>setQuery('')}><X size={18}/></button>}</div></div>",
  'close search-top wrap')
app = sub(app,
  "{!normalizedQuery?<div className=\"search-suggestions\"><span>ابدأ بكتابة اسم متجر أو منتج للبحث.</span><div>{['مطاعم','صيدليات','سوبر ماركت','خضار وفاكهة'].map((term,i)=><button key={term} onClick={()=>setQuery(term)}>{i===0?<SareeInlineIcon name=\"restaurant\" size={16}/>:<SareeInlineIcon name=\"bag\" size={16}/>} {term}</button>)}</div></div>:<>",
  "{!normalizedQuery?<div className=\"saree-search-idle\">{recentSearches.length>0&&<><p className=\"saree-search-label\">عمليات بحث سابقة</p><div className=\"saree-chips saree-recent\">{recentSearches.map(term=><button key={term} onClick={()=>setQuery(term)}><Clock3 size={14}/> {term}</button>)}</div></>}<h3 className=\"saree-search-h\">الأكثر بحثاً</h3><div className=\"saree-chips saree-hot\">{['كشري','شاورما','بيتزا','فراخ'].map(term=><button key={term} onClick={()=>setQuery(term)}>{term}</button>)}</div></div>:<>",
  'search idle block')
app = sub(app,
  '<div className="section-title"><h2>الأقرب إليك</h2><span className="muted">{visibleStores.length} متجر</span></div>',
  '<div className="section-title"><h2>نتائج قريبة منك</h2><span className="muted">{visibleStores.length} متجر</span></div>',
  'search results heading')
app = sub(app,
  "onClick={()=>{setSelectedStore(s.id);setProductCategory('all');setTab('home')}}",
  "onClick={()=>{rememberSearch(query);setSelectedStore(s.id);setProductCategory('all');setTab('home')}}",
  'remember search on store open')

APP.write_text(app, encoding='utf-8')
print('build 311 part 2 applied: item sheet, checkout sheet, search')

# ===================== part 3: CSS =====================
css = CSS.read_text(encoding='utf-8')
EXTRA = """
/* build 311 screens: item sheet, checkout sheet, search */
.saree-item-overlay{padding:0;place-items:stretch}
.saree-item-sheet{width:100%;max-width:480px;height:100dvh;max-height:100dvh;border-radius:0;padding:0;overflow-y:auto;margin:0 auto;background:#F3F4F1}
.saree-item-hero{position:relative;height:250px;background:#E4EECE;display:grid;place-items:center;overflow:hidden}
.saree-item-hero img{width:100%;height:100%;object-fit:cover}
.saree-item-emoji{font-size:88px}
.saree-circle-btn{position:absolute;top:14px;width:42px;height:42px;border-radius:50%;background:#fff;color:#141B0D;display:grid;place-items:center;box-shadow:0 4px 14px rgba(20,27,13,.12);border:0;cursor:pointer}
.saree-item-hero .saree-item-fav{inset-inline-start:14px;font-size:18px;color:#141B0D}
.saree-item-hero .saree-item-fav .on{color:#E2483D}
.saree-item-hero .saree-item-back{inset-inline-end:14px}
.saree-item-body{background:#F3F4F1;border-radius:24px 24px 0 0;margin-top:-22px;position:relative;padding:20px 16px 24px;display:flex;flex-direction:column;gap:12px;min-height:calc(100dvh - 228px)}
.saree-item-head{display:flex;justify-content:space-between;align-items:flex-start;gap:10px}
.saree-item-head h2{margin:0;font-size:19px;font-weight:900;color:#141B0D}
.saree-item-head b{font-size:14px;color:#141B0D;white-space:nowrap}
.saree-item-meta{margin:0;font-size:11px;color:#5C6650;display:flex;gap:6px}
.saree-item-desc{margin:0;font-size:11px;color:#5C6650;line-height:1.8}
.saree-item-sec h3{margin:0 0 8px;font-size:14px;font-weight:900;color:#141B0D}
.saree-item-sec .saree-chips{display:flex;gap:8px;flex-wrap:wrap}
.saree-item-sec .saree-chips button{padding:9px 16px;border-radius:999px;background:#fff;border:1px solid #E4E7DE;font:inherit;font-size:12px;font-weight:700;color:#141B0D;cursor:pointer}
.saree-item-sec .saree-chips button.on{background:#141B0D;color:#fff;border-color:#141B0D}
.saree-addons{display:flex;flex-direction:column;gap:8px}
.saree-addons button{display:flex;align-items:center;justify-content:space-between;gap:10px;background:#fff;border:1px solid #ECEEE7;border-radius:14px;padding:12px 14px;font:inherit;cursor:pointer}
.saree-addons button.on{border-color:#6FCB00}
.saree-addon-txt{display:flex;flex-direction:column;gap:2px;text-align:start}
.saree-addon-txt b{font-size:12px;color:#141B0D}
.saree-addon-txt small{font-size:10px;color:#8A8F86}
.saree-addon-plus{width:28px;height:28px;border-radius:50%;background:#6FCB00;color:#fff;display:grid;place-items:center;font-size:16px;font-weight:900;flex:none}
.saree-addons button.on .saree-addon-plus{background:#141B0D;content:"✓"}
.saree-item-notes{border:0;border-radius:14px;background:#fff;padding:13px 14px;font:inherit;font-size:12px;color:#141B0D;outline:0;width:100%}
.saree-item-foot{display:flex;gap:10px;align-items:center;margin-top:auto}
.saree-add-btn{flex:1;background:#6FCB00;color:#141B0D;border:0;border-radius:999px;padding:15px;font:inherit;font-size:14px;font-weight:900;cursor:pointer}
.saree-qty{display:flex;align-items:center;gap:12px;background:#fff;border-radius:999px;padding:8px 12px}
.saree-qty button{width:30px;height:30px;border-radius:50%;border:0;background:#F3F4F1;color:#141B0D;font-size:16px;font-weight:900;cursor:pointer}
.saree-qty button.up{background:#6FCB00}
.saree-qty b{font-size:14px;color:#141B0D;min-width:14px;text-align:center}
/* checkout */
.saree-sheet-head{position:relative;display:flex;align-items:center;justify-content:center;padding:16px;background:#F3F4F1}
.saree-sheet-head h2{margin:0;font-size:17px;font-weight:900;color:#141B0D}
.saree-sheet-head .saree-circle-btn{inset-inline-end:14px;top:10px}
.saree-checkout-sheet .saree-item-body{min-height:calc(100dvh - 66px);margin-top:0;border-radius:0}
.saree-info-card{display:flex;align-items:center;gap:12px;background:#fff;border-radius:18px;padding:14px;border:1px solid #ECEEE7;width:100%;font:inherit;cursor:pointer;text-align:start}
div.saree-info-card{cursor:default}
.saree-info-icon{width:42px;height:42px;border-radius:50%;background:#F1FAD3;color:#4E9A00;display:grid;place-items:center;flex:none}
.saree-info-text{display:flex;flex-direction:column;gap:3px;flex:1;min-width:0}
.saree-info-text b{font-size:13px;color:#141B0D}
.saree-info-text small{font-size:10px;color:#8A8F86}
.saree-info-link{font-size:11px;color:#4E9A00;font-weight:800}
.saree-pay-title{margin:6px 0 0;font-size:14px;font-weight:900;color:#141B0D}
.saree-pay-card{display:flex;align-items:center;gap:12px;background:#fff;border-radius:18px;padding:14px;border:1.5px solid #ECEEE7;width:100%;font:inherit;cursor:pointer;text-align:start;position:relative}
.saree-pay-card.on{border-color:#6FCB00;box-shadow:0 0 0 2px #6FCB0033}
.saree-pay-card.off{opacity:.5}
.saree-pay-check{width:26px;height:26px;border-radius:50%;background:#6FCB00;color:#fff;display:grid;place-items:center;font-size:13px;font-weight:900;flex:none}
.saree-summary-card{background:#fff;border-radius:18px;padding:6px 16px;border:1px solid #ECEEE7}
.saree-sum-row{display:flex;justify-content:space-between;padding:11px 0;font-size:12px;color:#5C6650;border-bottom:1px solid #F0F1EC}
.saree-sum-row b{color:#141B0D}
.saree-sum-row.total{border-bottom:0;font-size:15px;font-weight:900;color:#141B0D}
.saree-sum-row.total b{color:#141B0D}
.saree-confirm-btn{margin-top:6px}
.saree-checkout-fields label{display:flex;flex-direction:column;gap:5px;font-size:11px;font-weight:700;color:#141B0D}
.saree-checkout-fields input{border:1px solid #ECEEE7;border-radius:12px;padding:11px;background:#fff;font:inherit;font-size:12px;outline:0}
/* search */
.saree-search-top{display:flex;align-items:center;gap:10px;margin-top:4px}
.saree-search-top .saree-circle-btn{position:static;flex:none}
.saree-search-top .search{flex:1;min-width:0;margin:0;border-radius:999px;border:1px solid #E4E7DE}
.saree-search-label{font-size:11px;color:#8A8F86;margin:16px 0 8px;font-weight:700}
.saree-search-h{font-size:15px;font-weight:900;color:#141B0D;margin:18px 0 10px}
.saree-search-idle .saree-chips{display:flex;gap:8px;flex-wrap:wrap}
.saree-search-idle .saree-recent button{display:flex;align-items:center;gap:6px;padding:9px 16px;border-radius:999px;background:#fff;border:1px solid #E4E7DE;font:inherit;font-size:12px;font-weight:700;color:#141B0D;cursor:pointer}
.saree-search-idle .saree-hot button{padding:9px 18px;border-radius:999px;background:#F1FAD3;border:0;font:inherit;font-size:12px;font-weight:800;color:#3E7A00;cursor:pointer}
.customer-search-page{position:relative}
"""
if 'build 311 screens' not in css:
    css = css.rstrip() + '\n' + EXTRA
CSS.write_text(css, encoding='utf-8')
print('build 311 part 3 applied: CSS')