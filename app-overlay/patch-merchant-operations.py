from pathlib import Path

app = Path('src/App.tsx')
s = app.read_text()

def replace_once(old: str, new: str, label: str):
    global s
    count = s.count(old)
    if count != 1:
        raise SystemExit(f'{label}: expected exactly one match, found {count}')
    s = s.replace(old, new, 1)

replace_once(
"type StoreItem = {image?:string;id:string;name:string;type:Exclude<Service,'all'|'doctors'|'errand'>;area:string;rating:number;eta:string;fee:number;min:number;open:boolean;desc:string;icon:string;featured?:boolean;pharmacistVerified?:boolean};",
"type StoreItem = {image?:string;id:string;name:string;type:Exclude<Service,'all'|'doctors'|'errand'>;area:string;rating:number;eta:string;fee:number;min:number;open:boolean;desc:string;icon:string;featured?:boolean;pharmacistVerified?:boolean;commissionPercent?:number};",
"store type"
)
replace_once(
"[stores,setStores]=useState<StoreItem[]>([]),[products,setProducts]=useState<Product[]>([]),",
"[stores,setStores]=useState<StoreItem[]>([]),[merchantStoreRows,setMerchantStoreRows]=useState<any[]>([]),[products,setProducts]=useState<Product[]>([]),",
"merchant store state"
)
replace_once(
".select('id,name,service_type,area_name,description,delivery_fee,min_order,is_open,eta,pharmacist_verified')",
".select('id,name,service_type,area_name,description,delivery_fee,min_order,is_open,eta,pharmacist_verified,commission_percent')",
"merchant public select"
)
replace_once(
"pharmacistVerified:Boolean(m.pharmacist_verified)})))",
"pharmacistVerified:Boolean(m.pharmacist_verified),commissionPercent:Number(m.commission_percent||0)})))",
"merchant commission mapping"
)
anchor = " useEffect(()=>{if(!supabase||!signedInPhone)return;let alive=true;(async()=>{const [{data:merchantRows,error},{data:categoryRows}]=await Promise.all(["
insert = " useEffect(()=>{if(!supabase||!signedInPhone||!merchantIds.length){setMerchantStoreRows([]);return;}let live=true;supabase.from('merchants').select('id,name,is_open,is_active,commission_percent,delivery_fee,min_order').in('id',merchantIds).order('name').then(({data,error}:any)=>{if(!live)return;if(error){notify('تعذر تحميل إعدادات متاجرك: '+error.message);return;}setMerchantStoreRows(data||[])});return()=>{live=false}},[signedInPhone,merchantIds]);\n"
if s.count(anchor) != 1:
    raise SystemExit('merchant store load anchor not unique')
s = s.replace(anchor, insert + anchor, 1)
anchor = " const renderOrders=(filter:'customer'|'merchant'|'driver'|'admin')=>"
method = " const toggleMerchantStoreOpen=async(store:any)=>{if(!supabase||!merchantIds.includes(store.id)){notify('لا تملك صلاحية إدارة هذا المتجر');return;}const next=!store.is_open;const {data,error}=await supabase.rpc('set_merchant_open_status',{p_merchant_id:store.id,p_is_open:next});if(error||data===null){notify('تعذر تحديث حالة المتجر: '+(error?.message||'لم يتم تحديث أي متجر'));return;}setMerchantStoreRows(rows=>rows.map(x=>x.id===store.id?{...x,is_open:Boolean(data)}:x));setStores(rows=>rows.map(x=>x.id===store.id?{...x,open:Boolean(data)}:x));notify(next?'تم فتح المتجر لاستقبال الطلبات':'تم إغلاق المتجر مؤقتًا')};\n const merchantToday=(storeId:string)=>orders.filter(o=>o.storeId===storeId&&o.status==='تم التسليم'&&new Date(o.createdAt).toDateString()===new Date().toDateString());\n"
if s.count(anchor) != 1:
    raise SystemExit('order renderer anchor not unique')
s = s.replace(anchor, method + anchor, 1)
old = " {role==='merchant'&&tab==='overview'&&<><h1>لوحة التاجر</h1><div className=\"stats\"><Stat label=\"الطلبات الجديدة\" value={orders.filter(o=>merchantIds.includes(o.storeId||'')&&o.status==='جديد').length.toString()}/><Stat label=\"إجمالي الطلبات\" value={orders.filter(o=>merchantIds.includes(o.storeId||'')).length.toString()}/><Stat label=\"المنتجات\" value={products.filter(p=>merchantIds.includes(p.storeId)).length.toString()}/><Stat label=\"حالة المتجر\" value=\"مفتوح\"/></div>{renderOrders('merchant')}</>}"
new = " {role==='merchant'&&tab==='overview'&&<><h1>لوحة التاجر</h1><div className=\"stats\"><Stat label=\"الطلبات الجديدة\" value={orders.filter(o=>merchantIds.includes(o.storeId||'')&&o.status==='جديد').length.toString()}/><Stat label=\"إجمالي الطلبات\" value={orders.filter(o=>merchantIds.includes(o.storeId||'')).length.toString()}/><Stat label=\"المنتجات\" value={products.filter(p=>merchantIds.includes(p.storeId)).length.toString()}/><Stat label=\"المتاجر المرتبطة\" value={merchantStoreRows.length.toString()}/></div><section className=\"panel\"><h2>حالة استقبال الطلبات</h2>{merchantStoreRows.length===0?<Empty title=\"لا توجد متاجر مرتبطة\" hint=\"اطلب من الإدارة ربط حسابك بالمنشأة المعتمدة.\"/>:merchantStoreRows.map(m=><article className=\"cart-line\" key={m.id}><span><b>{m.name}</b><small className=\"muted\">{m.is_active?'منشأة نشطة':'المنشأة موقوفة من الإدارة'}</small></span><span className={m.is_open?'status success':'status'}>{m.is_open?'مفتوح':'مغلق'}</span><button className=\"outline\" disabled={!m.is_active} onClick={()=>void toggleMerchantStoreOpen(m)}>{m.is_open?'إغلاق مؤقت':'فتح لاستقبال الطلبات'}</button></article>)}</section><section className=\"panel\"><h2>ملخص مبيعات اليوم</h2>{merchantStoreRows.map(m=>{const completed=merchantToday(m.id);const gross=completed.reduce((sum,o)=>sum+o.total,0);const rate=Number(m.commission_percent||0);return <article className=\"order-card\" key={m.id}><b>{m.name}</b><p>{completed.length} طلب تم تسليمه اليوم</p><div className=\"summary-row\"><span>إجمالي قيمة المنتجات</span><b>{money(gross)}</b></div><div className=\"summary-row\"><span>عمولة المنصة التقديرية ({rate}%)</span><b>{money(gross*rate/100)}</b></div><div className=\"summary-row total\"><span>صافي مستحق المتجر التقديري</span><b>{money(gross*(1-rate/100))}</b></div><small className=\"muted\">تقدير للطلبات المسلّمة اليوم، وليس كشف تسوية مالية نهائيًا.</small></article>})}{!merchantStoreRows.length&&<Empty title=\"لا توجد بيانات مبيعات\" hint=\"ستظهر المبيعات بعد ربط المتجر بحسابك.\"/>}</section>{renderOrders('merchant')}</>}"
replace_once(old, new, "merchant dashboard")
replace_once(
" {role==='merchant'&&tab==='profile'&&<section className=\"panel\"><h2>بيانات المتجر</h2><p>اسم تجريبي: صيدلية الشفاء – ملوي</p><p className=\"warning\">يجب رفع الترخيص والتحقق من الصيدلي المسؤول قبل استقبال أي وصفات أو طلبات أدوية.</p></section>}",
" {role==='merchant'&&tab==='profile'&&<section className=\"panel\"><h2>بيانات المتجر</h2>{merchantStoreRows.length?merchantStoreRows.map(m=><article className=\"order-card\" key={m.id}><b>{m.name}</b><p>رسوم التوصيل: {money(Number(m.delivery_fee||0))}</p><p>الحد الأدنى للطلب: {money(Number(m.min_order||0))}</p><p>عمولة المنصة: {Number(m.commission_percent||0)}%</p><span className={m.is_active?'status success':'status'}>{m.is_active?'نشط من الإدارة':'موقوف من الإدارة'}</span></article>):<Empty title=\"لا توجد منشأة مرتبطة\" hint=\"سيتم عرض بيانات المتجر بعد ربط حسابك من الإدارة.\"/>}<p className=\"muted\">مواعيد العمل الأسبوعية غير مهيأة في قاعدة البيانات الحالية؛ لذلك لا نعرض جدول ساعات غير محفوظ.</p></section>}",
"merchant profile placeholder"
)
app.write_text(s)

tests = Path('tests/source-smoke.test.cjs')
if tests.exists():
    t = tests.read_text()
    marker = "test('merchant dashboard supports store availability and daily sales', () => {"
    if marker not in t:
        t += '''\n\ntest('merchant dashboard supports store availability and daily sales', () => {\n  const source = app();\n  assert.ok(source.includes('toggleMerchantStoreOpen'));\n  assert.ok(source.includes("rpc('set_merchant_open_status'"));\n  assert.ok(source.includes('merchantToday'));\n  assert.ok(source.includes('commission_percent'));\n  assert.ok(source.includes('صافي مستحق المتجر التقديري'));\n});\n'''
        tests.write_text(t)
print('Applied vendor store availability and daily sales module.')
