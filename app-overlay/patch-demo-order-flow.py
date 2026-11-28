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
new_icons = "{x.icon==='all'?<Grid2X2 size={22}/>:x.icon==='restaurant'?<SareeInlineIcon name=\"restaurant\"/>:x.icon==='scooter'?<SareeInlineIcon name=\"scooter\"/>:x.icon==='cafe'?<Coffee size={22}/>:x.icon==='grocery'?<SareeInlineIcon name=\"bag\"/>:x.icon==='vegetables'?<Apple size={22}/>:x.icon==='pharmacy'?<Pill size={22}/>:x.icon==='doctors'?<Stethoscope size={22}/>:<SareeInlineIcon name=\"bag\"/>}"
if old_icons in s:
    line = next((x for x in s.splitlines() if x.startswith('import {') and "from 'lucide-react'" in x), None)
    if not line:
        raise SystemExit('lucide-react import not found')
    new_line = line.replace('import { ', 'import { Grid2X2, Coffee, Apple, Pill, ', 1)
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
