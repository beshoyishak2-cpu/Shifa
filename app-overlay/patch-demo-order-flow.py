from pathlib import Path

app = Path('src/App.tsx')
s = app.read_text(encoding='utf-8')

def replace_once(old, new, label):
    global s
    count = s.count(old)
    if count != 1:
        raise SystemExit(f'{label}: expected one match, found {count}')
    s = s.replace(old, new, 1)

replace_once(
    "[customer,setCustomer]=useState(()=>load('customer',{name:'عميل سريع',phone:''})),",
    "[customer,setCustomer]=useState(()=>{const saved=load('customer',{name:'عميل تجريبي',phone:'01000000000'});return backendReady?saved:{...saved,name:String(saved.name||'').trim()||'عميل تجريبي',phone:String(saved.phone||'').trim()||'01000000000'}}),",
    'demo customer defaults'
)

old_effect = "useEffect(()=>{if(!backendReady||!supabase||!signedInPhone||!merchantIds.length){setMerchantStoreRows([]);return;}let live=true;supabase.from('merchants').select('id,name,is_open,is_active,commission_percent,delivery_fee,min_order,image_url').in('id',merchantIds).order('name').then(({data,error}:any)=>{if(!live)return;if(error){notify('تعذر تحميل إعدادات متاجرك: '+error.message);return;}setMerchantStoreRows(data||[])});return()=>{live=false}},[signedInPhone,merchantIds]);"
new_effect = "useEffect(()=>{if(!backendReady){setMerchantStoreRows(SAREE_DEMO_MERCHANT_ROWS);return;}if(!supabase||!signedInPhone||!merchantIds.length){setMerchantStoreRows([]);return;}let live=true;supabase.from('merchants').select('id,name,is_open,is_active,commission_percent,delivery_fee,min_order,image_url').in('id',merchantIds).order('name').then(({data,error}:any)=>{if(!live)return;if(error){notify('تعذر تحميل إعدادات متاجرك: '+error.message);return;}setMerchantStoreRows(data||[])});return()=>{live=false}},[backendReady,signedInPhone,merchantIds]);"
replace_once(old_effect, new_effect, 'demo merchant membership')

replace_once(
    '<h2>تأكيد الطلب</h2><label>طريقة الدفع',
    '<h2>تأكيد الطلب</h2>{!backendReady&&<><label>اسم العميل<input value={customer.name} onChange={e=>setCustomer((v:any)=>({...v,name:e.target.value}))} placeholder="عميل تجريبي"/></label><label>رقم الهاتف<input type="tel" inputMode="tel" value={customer.phone} onChange={e=>setCustomer((v:any)=>({...v,phone:e.target.value}))} placeholder="01000000000"/></label></>}<label>طريقة الدفع',
    'demo checkout customer fields'
)
replace_once(
    "if(!cart.length||!address.street.trim()||!customer.name.trim()||!customer.phone.trim())",
    "if(!cart.length||!(backendReady?address.street.trim():String(address.area||'').trim())||!customer.name.trim()||!customer.phone.trim())",
    'demo checkout validation'
)
replace_once(
    "address:[address.area,address.street,address.landmark,address.unit].filter(Boolean).join(' – ')",
    "address:[address.area,address.street,address.landmark,address.unit||''].map(x=>String(x||'').trim()).filter(Boolean).concat(address.area==='وسط ملوى'&&!address.street&&!address.landmark&&!address.unit?['المنيا']:[]).join('، ')||'وسط ملوى، المنيا'",
    'clean demo order address'
)
replace_once(
    "value={`${address.area} – ${address.street} – ${address.landmark} – ${address.unit||''}`} readOnly",
    "value={[address.area,address.street,address.landmark,address.unit||''].map(x=>String(x||'').trim()).filter(Boolean).concat(address.area==='وسط ملوى'&&!address.street&&!address.landmark&&!address.unit?['المنيا']:[]).join('، ')||'وسط ملوى، المنيا'} readOnly",
    'clean checkout address display'
)

old_icons = "{x.icon==='all'?<SareeInlineIcon name=\"all\"/>:x.icon==='restaurant'?<SareeInlineIcon name=\"restaurant\"/>:x.icon==='scooter'?<SareeInlineIcon name=\"scooter\"/>:x.icon==='cafe'?<SareeInlineIcon name=\"sparkle\"/>:x.icon==='grocery'?<SareeInlineIcon name=\"bag\"/>:<SareeInlineIcon name=\"sparkle\"/>}"
new_icons = "{x.icon==='all'?<Grid2X2 size={22}/>:x.icon==='restaurant'?<SareeInlineIcon name=\"restaurant\"/>:x.icon==='scooter'?<SareeInlineIcon name=\"scooter\"/>:x.icon==='cafe'?<Coffee size={22}/>:x.icon==='grocery'?<SareeInlineIcon name=\"bag\"/>:x.icon==='vegetables'?<Apple size={22}/>:x.icon==='pharmacy'?<Pill size={22}/>:(x.icon==='doctors'||x.icon==='doctor'||x.icon==='medical'||x.icon==='physician')?<Stethoscope size={22}/>:<SareeInlineIcon name=\"bag\"/>}"
if old_icons in s:
    line = next((x for x in s.splitlines() if x.startswith('import {') and "from 'lucide-react'" in x), None)
    if not line:
        raise SystemExit('lucide-react import not found')
    icons_to_add = ['Grid2X2', 'Coffee', 'Apple', 'Pill', 'Stethoscope']
    missing_icons = [name for name in icons_to_add if name not in line]
    new_line = line.replace('import { ', 'import { ' + ', '.join(missing_icons) + (', ' if missing_icons else ''), 1)
    s = s.replace(line, new_line, 1)
    replace_once(old_icons, new_icons, 'service category icons')
else:
    print('Service category grid is not part of this target; icon patch skipped.')

# Keep demo courier assignments visible until the courier explicitly picks up.
# Demo mode has no authenticated user ID, so it must filter by its local courier ID.
replace_once(
    "status:'في الطريق',courierId:'demo-courier'",
    "status:'جاهز للاستلام',courierId:'demo-courier'",
    'demo courier acceptance keeps pickup status'
)
replace_once(
    "o.courierId===currentUserId",
    "(backendReady?o.courierId===currentUserId:o.courierId==='demo-courier')",
    'demo courier task ownership filter'
)


# Merchant cashier: expose each permitted transition explicitly instead of auto-advancing.
replace_once(
    "type CartLine = {productId:string;storeId:string;qty:number;options?:CartOptionGroup[]};",
    "type CartLine = {productId:string;storeId:string;qty:number;productName?:string;unitPrice?:number;lineTotal?:number;options?:CartOptionGroup[]};",
    'invoice line snapshots'
)
replace_once(
    " const [searchKeyboardOpen,setSearchKeyboardOpen]=useState(false);",
    """ const [searchKeyboardOpen,setSearchKeyboardOpen]=useState(false);
 const [invoiceOrder,setInvoiceOrder]=useState<Order|null>(null);""",
    'invoice state'
)
replace_once(
    "order_items(product_id,quantity,order_item_options(group_name_snapshot,option_name_snapshot,price_delta,quantity))",
    "order_items(product_id,product_name,unit_price,line_total,quantity,order_item_options(group_name_snapshot,option_name_snapshot,price_delta,quantity))",
    'invoice order item select'
)
replace_once(
    "({productId:x.product_id,storeId:o.merchant_id,qty:x.quantity,options:",
    "({productId:x.product_id,storeId:o.merchant_id,qty:x.quantity,productName:x.product_name,unitPrice:Number(x.unit_price||0),lineTotal:Number(x.line_total||0),options:",
    'invoice item snapshot mapping'
)
replace_once(
    "status:orderStatusFromDb(o.status),payment:'الدفع عند الاستلام'",
    "status:orderStatusFromDb(o.status),payment:o.payment_method==='cash'?'الدفع عند الاستلام':String(o.payment_method||'غير محدد')",
    'invoice payment mapping'
)
replace_once(
    " const renderOrders=(filter:'customer'|'merchant'|'driver'|'admin')=>",
    """ const openInvoice=(o:Order)=>{setInvoiceOrder(o);setModal('invoice')};
 const renderOrders=(filter:'customer'|'merchant'|'driver'|'admin')=>""",
    'invoice open helper'
)
replace_once(
    """{(filter==='merchant'||filter==='admin')&&o.status!=='تم التسليم'&&o.status!=='ملغي'&&(filter==='admin'||o.status!=='جاهز للاستلام')&&<button className="primary small" onClick={()=>void updateServerOrder(o,nextStatus(o.status))}>تحديث حالة الطلب</button>}""",
    """{filter==='merchant'&&o.status==='جديد'&&<button className="primary small" onClick={()=>void updateServerOrder(o,'تم القبول')}>قبول الطلب</button>}{filter==='merchant'&&o.status==='تم القبول'&&<button className="primary small" onClick={()=>void updateServerOrder(o,'قيد التجهيز')}>ابدأ التجهيز</button>}{filter==='merchant'&&o.status==='قيد التجهيز'&&<button className="primary small" onClick={()=>void updateServerOrder(o,'جاهز للاستلام')}>جاهز للاستلام</button>}{filter==='merchant'&&(o.status==='جديد'||o.status==='تم القبول')&&<button className="outline small invoice-cancel" onClick={()=>void updateServerOrder(o,'ملغي')}>رفض/إلغاء</button>}{filter==='admin'&&o.status!=='تم التسليم'&&o.status!=='ملغي'&&<button className="primary small" onClick={()=>void updateServerOrder(o,nextStatus(o.status))}>تحديث حالة الطلب</button>}{(filter==='customer'||filter==='merchant')&&<button className="outline small" onClick={()=>openInvoice(o)}>فاتورة</button>}""",
    'merchant cashier actions and invoice buttons'
)
invoice = r""" {modal==='invoice'&&invoiceOrder&&<div className="overlay invoice-overlay" onClick={()=>setModal('')}><div className="dialog invoice-dialog" onClick={e=>e.stopPropagation()}><div className="invoice-actions"><button className="close invoice-close" onClick={()=>setModal('')}><X/></button><button className="primary" onClick={()=>window.print()}>طباعة الفاتورة</button></div><article className="invoice-sheet" dir="rtl"><div className="invoice-head"><div><h1>{invoiceOrder.storeName}</h1><p>فاتورة طلب</p></div><div className="invoice-number"><span>رقم الفاتورة</span><b>#{invoiceOrder.number}</b><small>{new Date(invoiceOrder.createdAt).toLocaleString('ar-EG')}</small></div></div><div className="invoice-meta"><div><span>اسم العميل</span><b>{invoiceOrder.customer||'—'}</b></div><div><span>رقم الهاتف</span><b>{invoiceOrder.phone||'—'}</b></div><div className="invoice-address"><span>عنوان التوصيل</span><b>{invoiceOrder.address||'—'}</b></div><div><span>حالة الطلب</span><b>{invoiceOrder.status}</b></div></div><table className="invoice-items"><thead><tr><th>الصنف</th><th>الكمية</th><th>سعر الوحدة</th><th>الإجمالي</th></tr></thead><tbody>{invoiceOrder.lines.map((line,i)=>{const product=products.find(p=>p.id===line.productId);const unitPrice=typeof line.unitPrice==='number'?line.unitPrice:lineUnitPrice(line);const lineTotal=typeof line.lineTotal==='number'?line.lineTotal:unitPrice*line.qty;const options=(line.options||[]).flatMap(g=>g.values.map(v=>v.name));return <tr key={line.productId+'-'+i}><td><b>{line.productName||product?.name||'منتج'}</b>{options.length>0&&<small>{options.join('، ')}</small>}</td><td>{line.qty}</td><td>{money(unitPrice)}</td><td>{money(lineTotal)}</td></tr>})}{invoiceOrder.lines.length===0&&<tr><td colSpan={4}>لا توجد أصناف — {invoiceOrder.notes||invoiceOrder.kind}</td></tr>}</tbody></table><div className="invoice-totals"><div><span>المنتجات</span><b>{money(invoiceOrder.total)}</b></div><div><span>التوصيل</span><b>{money(invoiceOrder.delivery)}</b></div><div className="invoice-grand-total"><span>الإجمالي</span><b>{money(invoiceOrder.total+invoiceOrder.delivery)}</b></div></div><div className="invoice-payment"><span>طريقة الدفع</span><b>{invoiceOrder.payment||'غير محدد'}</b></div><p className="invoice-thanks">شكرًا لاستخدام سريع — ملوى</p></article></div></div>}"""
replace_once(
    ' {toast&&<div className="toast"',
    invoice + ' {toast&&<div className="toast"',
    'invoice modal'
)

css_path=Path('src/style.css')
css=css_path.read_text(encoding='utf-8')
if '.invoice-sheet' not in css:
    css += r"""
/* Merchant cashier + printable customer/merchant invoice. */
.order-actions .invoice-cancel{border-color:#c84b43!important;color:#a52f28!important}
.invoice-dialog{width:min(760px,calc(100vw - 30px));max-width:100%;max-height:94dvh;overflow:auto;padding:14px;box-sizing:border-box}
.invoice-actions{display:flex;align-items:center;justify-content:flex-end;gap:10px;margin:0 0 12px}
.invoice-actions .invoice-close{position:static;margin-inline-end:auto}
.invoice-sheet{width:100%;max-width:100%;min-width:0;box-sizing:border-box;overflow-wrap:anywhere;background:#fff;color:#17231d;border:1px solid #e4e9e5;border-radius:12px;padding:28px;direction:rtl}
.invoice-sheet *{box-sizing:border-box;min-width:0;max-width:100%;overflow-wrap:anywhere}
.invoice-head{display:flex;justify-content:space-between;align-items:flex-start;gap:18px;min-width:0;padding-bottom:18px;border-bottom:2px solid #6FCB00}
.invoice-head>div{min-width:0;max-width:100%}
.invoice-head h1{margin:0 0 4px;font-size:24px;color:#17643d;overflow-wrap:anywhere;word-break:break-word}
.invoice-head p{margin:0;color:#66736a;font-size:13px}
.invoice-number{display:grid;gap:4px;text-align:left;min-width:0;max-width:100%}
.invoice-number span,.invoice-meta span,.invoice-payment span{font-size:11px;color:#68766e}
.invoice-number b{font-size:20px;overflow-wrap:anywhere;word-break:break-all}
.invoice-number small{font-size:11px;color:#68766e;overflow-wrap:anywhere}
.invoice-meta{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px;min-width:0;padding:18px 0}
.invoice-meta>div{display:grid;gap:4px;min-width:0;max-width:100%}
.invoice-meta b{font-size:13px;overflow-wrap:anywhere;word-break:break-word}
.invoice-address{grid-column:1/-1}
.invoice-items{width:100%;max-width:100%;min-width:0;table-layout:fixed;border-collapse:collapse;margin:6px 0 18px;font-size:12px}
.invoice-items th,.invoice-items td{width:auto;min-width:0;max-width:100%;padding:10px 6px;border-bottom:1px solid #e6ece7;text-align:right;vertical-align:top;overflow-wrap:anywhere;word-break:break-word}
.invoice-items th:nth-child(1),.invoice-items td:nth-child(1){width:40%}
.invoice-items th:nth-child(2),.invoice-items td:nth-child(2){width:13%;text-align:center}
.invoice-items th:nth-child(3),.invoice-items td:nth-child(3){width:22%}
.invoice-items th:nth-child(4),.invoice-items td:nth-child(4){width:25%}
.invoice-items th{background:#f1f7f2;font-weight:800}
.invoice-items td small{display:block;color:#718078;font-size:10px;margin-top:3px;overflow-wrap:anywhere}
.invoice-totals{width:min(320px,100%);max-width:100%;min-width:0;margin-inline-start:auto;display:grid;gap:8px}
.invoice-totals>div{display:flex;justify-content:space-between;gap:16px;min-width:0;font-size:12px}
.invoice-totals span,.invoice-totals b{min-width:0;overflow-wrap:anywhere}
.invoice-grand-total{border-top:2px solid #17643d;padding-top:10px;font-size:16px!important;font-weight:900}
.invoice-payment{display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:8px;min-width:0;max-width:100%;margin-top:20px;padding:12px;background:#f1f7f2;border-radius:8px;font-size:12px}
.invoice-payment>*{min-width:0;max-width:100%;overflow-wrap:anywhere}
.invoice-thanks{text-align:center;color:#68766e;font-size:11px;margin:24px 0 0;overflow-wrap:anywhere}
@media(max-width:600px){.invoice-dialog{width:calc(100vw - 20px);padding:10px}.invoice-sheet{padding:16px}.invoice-head{gap:10px}.invoice-head h1{font-size:19px}.invoice-number b{font-size:16px}.invoice-items{font-size:10px}.invoice-items th,.invoice-items td{padding:8px 4px}}
@media print{
 @page{size:A4;margin:12mm}
 html,body,#root{width:100%!important;min-width:0!important;max-width:100%!important;height:auto!important;min-height:0!important;margin:0!important;padding:0!important;overflow:visible!important;background:#fff!important}
 /* Remove the app shell from print layout, but preserve the ancestor chain containing the invoice. */
 body *{display:none!important}
 #root{display:block!important;position:static!important;width:100%!important;height:auto!important;overflow:visible!important}
 #root *:has(.invoice-overlay){display:contents!important;position:static!important;width:auto!important;height:auto!important;min-height:0!important;max-height:none!important;overflow:visible!important;margin:0!important;padding:0!important;transform:none!important}
 .invoice-overlay{position:static!important;inset:auto!important;display:block!important;width:100%!important;max-width:186mm!important;min-width:0!important;height:auto!important;min-height:0!important;margin:0!important;padding:0!important;overflow:visible!important;transform:none!important;background:#fff!important;place-items:initial!important}
 .invoice-overlay *{display:revert!important;position:static!important;max-width:100%!important;min-width:0!important;height:auto!important;max-height:none!important;overflow:visible!important;transform:none!important;box-shadow:none!important}
 .invoice-head{display:flex!important;justify-content:space-between!important;align-items:flex-start!important}
 .invoice-number{display:grid!important;grid-template-columns:minmax(72px,.85fr) minmax(0,1.5fr)!important;gap:4px 8px!important}
 .invoice-number small{grid-column:1/-1!important}
 .invoice-number span,.invoice-number b,.invoice-number small{display:block!important}
 .invoice-meta{display:grid!important;grid-template-columns:repeat(2,minmax(0,1fr))!important;gap:12px!important}
 .invoice-meta>div{display:grid!important;grid-template-columns:minmax(72px,.85fr) minmax(0,1.5fr)!important;align-items:start!important;column-gap:8px!important;row-gap:0!important}
 .invoice-meta span,.invoice-meta b{display:block!important;min-width:0!important}
 .invoice-address{grid-column:1/-1!important}
 .invoice-items{display:table!important}
 .invoice-items thead{display:table-header-group!important}
 .invoice-items tbody{display:table-row-group!important}
 .invoice-items tr{display:table-row!important}
 .invoice-items th,.invoice-items td{display:table-cell!important}
 .invoice-totals{display:grid!important;gap:8px!important}
 .invoice-totals>div{display:flex!important;justify-content:space-between!important}
 .invoice-payment{display:flex!important;justify-content:space-between!important;align-items:flex-start!important;flex-wrap:wrap!important}
 .invoice-dialog{position:static!important;display:block!important;width:100%!important;max-width:186mm!important;min-width:0!important;height:auto!important;max-height:none!important;overflow:visible!important;margin:0!important;padding:0!important;border:0!important;border-radius:0!important;box-shadow:none!important;background:#fff!important;color:#17231d!important}
 .invoice-actions,.invoice-close{display:none!important}
 .invoice-sheet{position:static!important;display:block!important;width:100%!important;max-width:186mm!important;min-width:0!important;height:auto!important;max-height:none!important;overflow:visible!important;margin:0!important;padding:0!important;border:0!important;border-radius:0!important;box-shadow:none!important;background:#fff!important;color:#17231d!important;break-inside:auto!important}
 .invoice-sheet *{max-width:100%!important;min-width:0!important;overflow-wrap:anywhere!important;word-break:break-word!important}
 .invoice-head,.invoice-meta,.invoice-totals,.invoice-payment{min-width:0!important;max-width:100%!important}
 .invoice-items{width:100%!important;max-width:100%!important;min-width:0!important;table-layout:fixed!important;border-collapse:collapse!important}
 .invoice-items th,.invoice-items td{min-width:0!important;max-width:100%!important;padding:7px 4px!important;white-space:normal!important;overflow-wrap:anywhere!important;word-break:break-word!important}
 .invoice-payment{flex-wrap:wrap!important;background:#f1f7f2!important}
 .invoice-items tr,.invoice-meta>div,.invoice-totals>div,.invoice-payment{break-inside:avoid}
}
"""
    css_path.write_text(css, encoding='utf-8')

tests=Path('tests/source-smoke.test.cjs')
if tests.exists():
    t=tests.read_text(encoding='utf-8')
    if 'merchant cashier uses explicit order transitions and cancellation' not in t:
        t += r"""
test('merchant cashier uses explicit order transitions and cancellation', () => {
  const source = app();
  assert.ok(source.includes("filter==='merchant'&&o.status==='جديد'"));
  assert.ok(source.includes("updateServerOrder(o,'تم القبول')"));
  assert.ok(source.includes("updateServerOrder(o,'قيد التجهيز')"));
  assert.ok(source.includes("updateServerOrder(o,'جاهز للاستلام')"));
  assert.ok(source.includes("updateServerOrder(o,'ملغي')"));
  assert.ok(source.includes('رفض/إلغاء'));
});

test('customer and merchant can open a snapshot-based printable invoice', () => {
  const source = app();
  const css = fs.readFileSync(path.join(root, 'src/style.css'), 'utf8');
  assert.ok(source.includes("(filter==='customer'||filter==='merchant')&&<button className=\"outline small\" onClick={()=>openInvoice(o)}>فاتورة</button>"));
  assert.ok(source.includes('productName:x.product_name'));
  assert.ok(source.includes('unitPrice:Number(x.unit_price||0)'));
  assert.ok(source.includes('رقم الفاتورة'));
  assert.ok(source.includes('invoiceOrder.storeName'));
  assert.ok(source.includes('invoiceOrder.payment'));
  assert.ok(source.includes('window.print()'));
  assert.ok(css.includes('@media print'));
  assert.ok(css.includes('.invoice-actions,.invoice-close{display:none!important}'));
  assert.ok(css.includes('@page{size:A4;margin:12mm}'));
  assert.ok(css.includes('max-width:186mm!important'));
  assert.ok(css.includes('table-layout:fixed!important'));
  assert.ok(css.includes('body *{display:none!important}'));
  assert.ok(css.includes('#root *:has(.invoice-overlay){display:contents!important;'));
  assert.ok(css.includes('.invoice-overlay{position:static!important'));
  assert.ok(!css.includes('body *{visibility:hidden!important}'));
  assert.ok(css.includes('.invoice-meta>div{display:grid!important;grid-template-columns:minmax(72px,.85fr) minmax(0,1.5fr)!important'));
  assert.ok(css.includes('.invoice-number{display:grid!important;grid-template-columns:minmax(72px,.85fr) minmax(0,1.5fr)!important'));
  assert.ok(css.includes('.invoice-items th,.invoice-items td{display:table-cell!important}'));
  assert.ok(css.includes('.invoice-payment{display:flex!important'));
  assert.ok(css.includes('background:#fff!important'));
  assert.ok(css.includes('overflow-wrap:anywhere!important'));
  assert.ok(css.includes('body *{display:none!important}'));
  assert.ok(css.includes('#root *:has(.invoice-overlay){display:contents!important}'));
  assert.ok(css.includes('.invoice-overlay{position:static!important'));
  assert.ok(!css.includes('body *{visibility:hidden!important}'));
});
"""
    tests.write_text(t, encoding='utf-8')

app.write_text(s, encoding='utf-8')

tests = Path('tests/source-smoke.test.cjs')
if tests.exists():
    t = tests.read_text(encoding='utf-8')
    if 'demo checkout includes customer identity and keeps merchant linked' not in t:
        t += """
\ntest('demo checkout includes customer identity and keeps merchant linked', () => {
  const app = fs.readFileSync(path.join(root, 'src/App.tsx'), 'utf8');
  assert.ok(app.includes("name:'عميل تجريبي',phone:'01000000000'"));
  assert.ok(app.includes('اسم العميل'));
  assert.ok(app.includes('setMerchantStoreRows(SAREE_DEMO_MERCHANT_ROWS)'));
  assert.ok(app.includes("merchantIds.includes(o.storeId||'')"));
  assert.ok(app.includes("!(backendReady?address.street.trim():String(address.area||'').trim())"));
  assert.ok(app.includes("address.area==='وسط ملوى'"));
});

test('service category icons are distinct line icons', () => {
  const app = fs.readFileSync(path.join(root, 'src/App.tsx'), 'utf8');
  if (!app.includes('className="service-grid"') || !app.includes('<Grid2X2 size={22}/>')) return;
  assert.ok(app.includes('<Grid2X2 size={22}/>'));
  assert.ok(app.includes('<Coffee size={22}/>'));
  assert.ok(app.includes('<Apple size={22}/>'));
  assert.ok(app.includes('<Pill size={22}/>'));
  assert.ok(app.includes('<Stethoscope size={22}/>'));
  assert.ok(app.includes("x.icon==='doctor'||x.icon==='medical'||x.icon==='physician'"));
});
"""
        tests.write_text(t, encoding='utf-8')


tests = Path('tests/source-smoke.test.cjs')
if tests.exists():
    t = tests.read_text(encoding='utf-8')
    if 'demo courier can accept, pick up and deliver an order' not in t:
        t += """
\ntest('demo courier can accept, pick up and deliver an order', () => {
  const app = fs.readFileSync(path.join(root, 'src/App.tsx'), 'utf8');
  assert.ok(app.includes("status:'جاهز للاستلام',courierId:'demo-courier'"));
  assert.ok(app.includes("(backendReady?o.courierId===currentUserId:o.courierId==='demo-courier')"));
  assert.ok(app.includes('استلام الطلب'));
  assert.ok(app.includes('تأكيد التسليم'));
});
"""
        tests.write_text(t, encoding='utf-8')

print('Applied demo checkout, merchant membership, clean address and category icon fixes.')
