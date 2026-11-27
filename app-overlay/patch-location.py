from pathlib import Path
p=Path("src/App.tsx")
s=p.read_text()

def replace_once(old: str, new: str, label: str):
    global s
    if old in s:
        s=s.replace(old,new,1)
    elif new not in s:
        raise SystemExit("Cannot find "+label)

if "import LocationSystem from './LocationSystem';" not in s:
    s="import LocationSystem from './LocationSystem';\n"+s
if '<LocationSystem/>' not in s:
    if "</header>" not in s: raise SystemExit("Cannot find app header insertion point")
    s=s.replace("</header>","</header><LocationSystem/>",1)

# The archive's original source may format or infer this type differently.
import re
if __import__("os").environ.get("SAREE_FINAL_PATCH") == "1":
    s=re.sub(r"(type\s+AddressDraft\s*=\s*\{[^}]*landmark:string;)([^}]*\};)",r"\1unit?:string;\2",s,count=1)
s=s.replace("landmark:selected.landmark||'',lat:selected.lat??null", "landmark:selected.landmark||'',unit:selected.unit||'',lat:selected.lat??null",1)
s=s.replace("delivery_area,delivery_street,delivery_landmark,delivery_latitude", "delivery_area,delivery_street,delivery_landmark,delivery_unit_details,delivery_latitude",1)
s=s.replace("[o.delivery_area,o.delivery_street,o.delivery_landmark].filter(Boolean)", "[o.delivery_area,o.delivery_street,o.delivery_landmark,o.delivery_unit_details].filter(Boolean)",1)
s=s.replace("o.delivery_map_url||((o.delivery_latitude!=null&&o.delivery_longitude!=null)?`https://www.google.com/maps?q=${o.delivery_latitude},${o.delivery_longitude}`:undefined)", "(o.delivery_latitude!=null&&o.delivery_longitude!=null)?`https://www.openstreetmap.org/?mlat=${o.delivery_latitude}&mlon=${o.delivery_longitude}#map=18/${o.delivery_latitude}/${o.delivery_longitude}`:undefined",1)
s=s.replace("${address.area} – ${address.street} – ${address.landmark}", "${address.area} – ${address.street} – ${address.landmark} – ${address.unit||''}",1)

if "saree3:address-selected" not in s:
    listener=" useEffect(()=>{const syncAddress=(event?:Event)=>{let selected=(event as CustomEvent|undefined)?.detail;try{if(!selected){const raw=localStorage.getItem('saree3:selected-address');if(raw)selected=JSON.parse(raw)}}catch{}if(!selected)return;setAddress({name:selected.label||'المنزل',area:selected.area||'',street:selected.street||'',landmark:selected.landmark||'',unit:selected.unit||'',lat:selected.lat??null,lng:selected.lng??null});};syncAddress();window.addEventListener('saree3:address-selected',syncAddress);return()=>window.removeEventListener('saree3:address-selected',syncAddress);},[]);\n"
    anchor=" useEffect(()=>save('cart',cart),[cart]);"
    if anchor not in s: raise SystemExit("Cannot find state persistence anchor")
    s=s.replace(anchor,listener+anchor,1)

if "deliveryMapUrl?:string" not in s:
    s=s.replace("notes:string;driver?:string;prescriptionName?:string;pickup?:string;dropoff?:string};","notes:string;driver?:string;prescriptionName?:string;pickup?:string;dropoff?:string;deliveryMapUrl?:string};",1)

if "saree3:open-address" not in s:
    old='<label>عنوان التوصيل<input value={`${address.area} – ${address.street} – ${address.landmark}`} readOnly/></label>'
    new=old+'<button className="outline full" onClick={()=>window.dispatchEvent(new Event("saree3:open-address"))}>تغيير العنوان أو تحديده على الخريطة</button>'
    if old not in s: raise SystemExit("Cannot find checkout address anchor")
    s=s.replace(old,new,1)

replace_once(
 "`${address.area} – ${address.street} – ${address.landmark}`",
 "`${address.area} – ${address.street} – ${address.landmark} – ${address.unit||''}`",
 "checkout address details"
)

# Keep the courier-facing address readable and always open the free OSM map, not Google Maps.
if "فتح موقع التسليم على الخريطة" not in s:
    old="<p>📍 {o.address}</p><p>☎ {o.customer} – {o.phone}</p>"
    new="<p>📍 {o.address}</p>{o.deliveryMapUrl&&<p><a href={o.deliveryMapUrl} target=\"_blank\" rel=\"noreferrer\">فتح موقع التسليم على الخريطة ↗</a></p>}<p>☎ {o.customer} – {o.phone}</p>"
    if old not in s: raise SystemExit("Cannot find order card address anchor")
    s=s.replace(old,new,1)

p.write_text(s)

css=Path("src/style.css")
c=css.read_text()
if ".s3-location-bar" not in c:
 c += """
.s3-location-bar{width:100%;display:flex;align-items:center;gap:10px;text-align:right;padding:10px 16px;background:var(--surface,#fff);border:0;border-bottom:1px solid var(--line,#e8ecea);color:var(--ink,#17352e);cursor:pointer}.s3-location-bar>span:first-child{font-size:20px}.s3-location-bar small{display:block;color:var(--muted,#718078);font-size:10px}.s3-location-bar b{font-size:13px}.s3-location-change{margin-right:auto;color:#087f68;font-size:11px}.s3-loc-overlay{position:fixed;inset:0;z-index:1000;background:#0008;display:flex;align-items:center;justify-content:center;padding:12px}.s3-loc-modal{position:relative;background:var(--surface,#fff);color:var(--ink,#17352e);width:min(560px,100%);max-height:92dvh;overflow:auto;border-radius:18px;padding:20px;box-shadow:0 18px 70px #0003}.s3-loc-close{position:absolute;left:14px;top:10px;border:0;background:transparent;font-size:28px;color:inherit}.s3-loc-modal h2{margin:0 0 4px;font-size:20px}.s3-loc-modal p{font-size:12px;color:var(--muted,#718078);margin:0 0 14px}.s3-gps,.s3-save{width:100%;border:0;border-radius:11px;padding:13px;background:#087f68;color:#fff;font-weight:700;margin:8px 0;cursor:pointer}.s3-gps:disabled{opacity:.6}.s3-map{height:220px;background:#edf3f0;border-radius:12px;overflow:hidden;display:grid;place-items:center;margin:8px 0}.s3-coords{font-size:10px;color:var(--muted,#718078);margin-bottom:12px}.s3-loc-modal label{display:block;font-size:11px;font-weight:700;margin:10px 0 5px}.s3-loc-modal input,.s3-loc-modal select{width:100%;box-sizing:border-box;border:1px solid var(--line,#dce5e0);background:var(--surface,#fff);color:var(--ink,#17352e);padding:11px;border-radius:9px;font:inherit;font-size:12px}.s3-loc-error{background:#fff0ed;color:#a33420;padding:9px;border-radius:8px;font-size:11px;margin:8px 0}.s3-saved{width:100%;display:flex;justify-content:space-between;gap:8px;text-align:right;background:transparent;border:1px solid var(--line,#e5ebe7);border-radius:9px;padding:10px;margin:6px 0;color:inherit}.s3-saved span{font-size:10px;color:var(--muted,#718078)}.s3-map-link{display:block;text-align:center;color:#087f68;font-size:12px;margin:8px}.s3-attribution{display:block;text-align:center;color:var(--muted,#718078);font-size:9px;margin-top:10px}@media(max-width:600px){.s3-loc-modal{max-height:94dvh;padding:16px}.s3-map{height:190px}}
"""
 css.write_text(c)

tests=Path("tests/source-smoke.test.cjs")
if tests.exists():
 t=tests.read_text()
 block="""
test('smart address lookup uses GPS, editable pin and free OpenStreetMap geocoding', () => {
  const location = fs.readFileSync(path.join(root, 'src/LocationSystem.tsx'), 'utf8');
  assert.ok(location.includes('Geolocation.getCurrentPosition'));
  assert.ok(location.includes('draggable:true'));
  assert.ok(location.includes('nominatim.openstreetmap.org/reverse'));
  assert.ok(location.includes('s3-mallawi-areas'));
  assert.ok(location.includes('OpenStreetMap contributors'));
});
test('saved delivery address includes unit details and courier receives an OSM pin link', () => {
  const source = app();
  assert.ok(source.includes('delivery_unit_details'));
  assert.ok(source.includes('address.unit||'));
  assert.ok(source.includes('www.openstreetmap.org/?mlat='));
});
"""
 if 'smart address lookup uses GPS' not in t:
  tests.write_text(t + block)

print("Smart address selector, checkout snapshot and courier handoff patched.")
