from pathlib import Path

p = Path('src/App.tsx')
s = p.read_text()

def replace_once(old: str, new: str, label: str):
    global s
    if old in s:
        s = s.replace(old, new, 1)
    elif new not in s:
        raise SystemExit(f'customer catalog patch anchor missing: {label}')

replace_once(
    "type Product = {id:string;storeId:string;name:string;description:string;price:number;unit:string;emoji:string;category:string;available:boolean};",
    "type Product = {id:string;storeId:string;name:string;description:string;price:number;unit:string;emoji:string;category:string;imageUrl?:string;available:boolean};",
    'product image type'
)
replace_once(
    "[service,setService]=useState<Service>('all'),[query,setQuery]=useState(''),[selectedStore,setSelectedStore]=useState<string|null>(null),",
    "[service,setService]=useState<Service>('all'),[query,setQuery]=useState(''),[selectedStore,setSelectedStore]=useState<string|null>(null),[productCategory,setProductCategory]=useState('all'),",
    'product category state'
)
old_load = """ useEffect(()=>{if(!supabase||!signedInPhone)return;let alive=true;(async()=>{const {data:merchantRows,error}=await supabase!.from('merchants').select('id,name,service_type,area_name,description,delivery_fee,min_order,is_open,eta,pharmacist_verified').order('name');if(error){notify('تعذر تحميل المتاجر من الخادم: '+error.message);return;}if(!alive)return;const rows=merchantRows||[];const ids=rows.map((m:any)=>m.id);setStores(rows.map((m:any)=>({id:m.id,name:m.name,type:m.service_type||'restaurant',area:m.area_name||'ملوي',rating:0,eta:m.eta||'20–30 دقيقة',fee:Number(m.delivery_fee||0),min:Number(m.min_order||0),open:Boolean(m.is_open),desc:m.description||'',icon:STORE_TYPES[m.service_type]?.icon||'🏪',pharmacistVerified:Boolean(m.pharmacist_verified)})));if(!ids.length){setProducts([]);return;}const {data:productRows,error:productError}=await supabase!.from('products').select('id,merchant_id,name,description,price,unit,emoji,category_id,image_url,is_available').in('merchant_id',ids).order('name');if(productError){notify('تعذر تحميل المنتجات: '+productError.message);return;}if(!alive)return;setProducts((productRows||[]).map((p:any)=>({id:p.id,storeId:p.merchant_id,name:p.name,description:p.description||'',price:Number(p.price||0),unit:p.unit||'قطعة',emoji:p.emoji||'📦',category:p.category_id||'عام',available:Boolean(p.is_available)})));})();return()=>{alive=false}},[signedInPhone]);"""
new_load = """ useEffect(()=>{if(!supabase||!signedInPhone)return;let alive=true;(async()=>{const [{data:merchantRows,error},{data:categoryRows}]=await Promise.all([supabase!.from('merchants').select('id,name,service_type,area_name,description,delivery_fee,min_order,is_open,eta,pharmacist_verified').eq('is_active',true).order('name'),supabase!.from('categories').select('id,name_ar').eq('is_active',true).order('sort_order')]);if(error){notify('تعذر تحميل المتاجر من الخادم: '+error.message);return;}if(!alive)return;const categoryMap=new Map((categoryRows||[]).map((c:any)=>[c.id,c.name_ar]));const rows=merchantRows||[];const ids=rows.map((m:any)=>m.id);setStores(rows.map((m:any)=>({id:m.id,name:m.name,type:m.service_type||'restaurant',area:m.area_name||'ملوي',rating:0,eta:m.eta||'20–30 دقيقة',fee:Number(m.delivery_fee||0),min:Number(m.min_order||0),open:Boolean(m.is_open),desc:m.description||'',icon:STORE_TYPES[m.service_type]?.icon||'🏪',pharmacistVerified:Boolean(m.pharmacist_verified)})));if(!ids.length){setProducts([]);return;}const {data:productRows,error:productError}=await supabase!.from('products').select('id,merchant_id,name,description,price,unit,emoji,category_id,image_url,is_available').in('merchant_id',ids).order('name');if(productError){notify('تعذر تحميل المنتجات: '+productError.message);return;}if(!alive)return;const mapped=(productRows||[]).map((p:any)=>({id:p.id,storeId:p.merchant_id,name:p.name,description:p.description||'',price:Number(p.price||0),unit:p.unit||'قطعة',emoji:p.emoji||'📦',category:categoryMap.get(p.category_id)||'عام',imageUrl:p.image_url||undefined,available:Boolean(p.is_available)}));setProducts(mapped);setStores(v=>v.map(store=>({...store,image:mapped.find(product=>product.storeId===store.id&&product.imageUrl)?.imageUrl||store.image})));})();return()=>{alive=false}},[signedInPhone]);"""
replace_once(old_load, new_load, 'catalog data loader')
replace_once(
    " const visibleStores=useMemo(()=>stores.filter(s=>(service==='all'||s.type===service)&&(!query||`${s.name} ${s.area} ${s.desc}`.includes(query))),[stores,service,query]);\n const visibleProducts=useMemo(()=>products.filter(p=>p.storeId===selectedStore&&p.available&&(!query||`${p.name} ${p.description} ${p.category}`.includes(query))),[products,selectedStore,query]);",
    " const normalizedQuery=query.trim().toLocaleLowerCase();\n const visibleStores=useMemo(()=>stores.filter(s=>(service==='all'||s.type===service)&&(!normalizedQuery||`${s.name} ${s.area} ${s.desc}`.toLocaleLowerCase().includes(normalizedQuery)||products.some(p=>p.storeId===s.id&&`${p.name} ${p.description} ${p.category}`.toLocaleLowerCase().includes(normalizedQuery)))),[stores,service,normalizedQuery,products]);\n const productCategories=useMemo(()=>Array.from(new Set(products.filter(p=>p.storeId===selectedStore&&p.category&&p.category!=='عام').map(p=>p.category))),[products,selectedStore]);\n const visibleProducts=useMemo(()=>products.filter(p=>p.storeId===selectedStore&&p.available&&(productCategory==='all'||p.category===productCategory)&&(!normalizedQuery||`${p.name} ${p.description} ${p.category}`.toLocaleLowerCase().includes(normalizedQuery))),[products,selectedStore,productCategory,normalizedQuery]);",
    'global product search and category filtering'
)
replace_once(
    "<div className=\"section-title\"><div><h2>{stores.find(s=>s.id===selectedStore)?.name}</h2><small>{stores.find(s=>s.id===selectedStore)?.desc} · {stores.find(s=>s.id===selectedStore)?.eta}</small></div><span className=\"rating\">★ {stores.find(s=>s.id===selectedStore)?.rating}</span></div><div className=\"product-grid\">{visibleProducts.map(p=><article className=\"product\" key={p.id}><div className=\"product-art\">{p.emoji}</div><h3>{p.name}</h3><p>{p.description}</p><div className=\"product-foot\"><b>{money(p.price)}</b><button className=\"add\" onClick={()=>add(p)}><Plus size={16}/> أضف</button></div></article>)}</div>",
    "<div className=\"section-title\"><div><h2>{stores.find(s=>s.id===selectedStore)?.name}</h2><small>{stores.find(s=>s.id===selectedStore)?.desc} · {stores.find(s=>s.id===selectedStore)?.eta} · {stores.find(s=>s.id===selectedStore)?.open?'مفتوح':'مغلق'}</small></div><span className=\"rating\">★ {stores.find(s=>s.id===selectedStore)?.rating}</span></div><div className=\"category-filters\"><button className={productCategory==='all'?'active':''} onClick={()=>setProductCategory('all')}>كل الأصناف</button>{productCategories.map(c=><button key={c} className={productCategory===c?'active':''} onClick={()=>setProductCategory(c)}>{c}</button>)}</div><div className=\"product-grid\">{visibleProducts.map(p=><article className=\"product\" key={p.id}><div className=\"product-art\">{p.imageUrl?<img src={p.imageUrl} alt={p.name} loading=\"lazy\"/>:p.emoji}</div><small className=\"product-category\">{p.category}</small><h3>{p.name}</h3><p>{p.description}</p><div className=\"product-foot\"><b>{money(p.price)}</b><button className=\"add\" onClick={()=>add(p)}><Plus size={16}/> أضف</button></div></article>)}</div>",
    'vendor product presentation'
)
replace_once("onClick={()=>setSelectedStore(s.id)}", "onClick={()=>{setProductCategory('all');setSelectedStore(s.id)}}", 'reset category when opening vendor')
p.write_text(s)

css = Path('src/style.css')
if css.exists():
    c = css.read_text()
    additions = "\n.category-filters{display:flex;gap:7px;overflow-x:auto;padding:5px 0 12px}.category-filters button{flex:0 0 auto;border:1px solid var(--line);border-radius:20px;background:var(--surface);color:var(--ink);padding:7px 13px;font:inherit;font-size:10px}.category-filters button.active{background:var(--green);border-color:var(--green);color:#fff}.product-category{display:inline-block;color:var(--green);font-size:9px;margin-top:5px}.product-art img{width:100%;height:100%;object-fit:cover;border-radius:10px}\n"
    if '.category-filters{' not in c:
        css.write_text(c + additions)

tests = Path('tests/source-smoke.test.cjs')
if tests.exists():
    t = tests.read_text()
    extra = """
test('customer catalog searches products globally and filters active vendors', () => {
  assert.ok(app().includes(\".eq('is_active',true)\"));
  assert.ok(app().includes('products.some(p=>p.storeId===s.id'));
});
test('customer vendor menu displays product photos and database category labels', () => {
  assert.ok(app().includes('imageUrl:p.image_url||undefined'));
  assert.ok(app().includes(\"from('categories').select('id,name_ar')\"));
  assert.ok(app().includes('productCategories.map'));
});
"""
    if 'customer catalog searches products globally' not in t:
        tests.write_text(t + extra)
print('Customer catalog patch applied.')
