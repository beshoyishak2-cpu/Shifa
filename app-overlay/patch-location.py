from pathlib import Path
p=Path("src/App.tsx")
s=p.read_text()
if "import LocationSystem from './LocationSystem';" not in s:
    s="import LocationSystem from './LocationSystem';\n"+s
if '<LocationSystem/>' not in s:
    if "</header>" not in s: raise SystemExit("Cannot find app header insertion point")
    s=s.replace("</header>","</header><LocationSystem/>",1)
listener = " useEffect(()=>{const syncAddress=(event?:Event)=>{let selected=(event as CustomEvent|undefined)?.detail;try{if(!selected){const raw=localStorage.getItem('saree3:selected-address');if(raw)selected=JSON.parse(raw)}}catch{}if(!selected)return;setAddress({name:selected.label||'المنزل',area:selected.area||'',street:selected.street||'',landmark:selected.landmark||'',lat:selected.lat??null,lng:selected.lng??null});};syncAddress();window.addEventListener('saree3:address-selected',syncAddress);return()=>window.removeEventListener('saree3:address-selected',syncAddress);},[]);\n"
if "saree3:address-selected" not in s:
    anchor=" useEffect(()=>save('cart',cart),[cart]);"
    if anchor not in s: raise SystemExit("Cannot find state persistence anchor")
    s=s.replace(anchor,listener+anchor,1)
if "deliveryMapUrl?:string" not in s:
    s=s.replace("notes:string;driver?:string;prescriptionName?:string;pickup?:string;dropoff?:string};","notes:string;driver?:string;prescriptionName?:string;pickup?:string;dropoff?:string;deliveryMapUrl?:string};",1)
if "deliveryMapUrl:address.lat!==null" not in s:
    old="address:`${address.area} – ${address.street} – ${address.landmark}`,createdAt:new Date().toISOString(),customer:customer.name,phone:customer.phone,notes}"
    new="address:`${address.area} – ${address.street} – ${address.landmark}`,deliveryMapUrl:address.lat!==null&&address.lng!==null?`https://www.google.com/maps?q=${address.lat},${address.lng}`:undefined,createdAt:new Date().toISOString(),customer:customer.name,phone:customer.phone,notes}"
    if old not in s: raise SystemExit("Cannot find order creation anchor")
    s=s.replace(old,new,1)
if "فتح موقع التسليم على الخريطة" not in s:
    old="<p>📍 {o.address}</p><p>☎ {o.customer} – {o.phone}</p>"
    new="<p>📍 {o.address}</p>{o.deliveryMapUrl&&<p><a href={o.deliveryMapUrl} target=\"_blank\" rel=\"noreferrer\">فتح موقع التسليم على الخريطة ↗</a></p>}<p>☎ {o.customer} – {o.phone}</p>"
    if old not in s: raise SystemExit("Cannot find order card address anchor")
    s=s.replace(old,new,1)
if "saree3:open-address" not in s:
    old='<label>عنوان التوصيل<input value={`${address.area} – ${address.street} – ${address.landmark}`} readOnly/></label>'
    new=old+'<button className="outline full" onClick={()=>window.dispatchEvent(new Event("saree3:open-address"))}>تغيير العنوان أو تحديده على الخريطة</button>'
    if old not in s: raise SystemExit("Cannot find checkout address anchor")
    s=s.replace(old,new,1)
p.write_text(s)
css=Path("src/style.css")
c=css.read_text()
if ".s3-location-bar" not in c:
 c += """
.s3-location-bar{width:100%;display:flex;align-items:center;gap:10px;text-align:right;padding:10px 16px;background:var(--surface,#fff);border:0;border-bottom:1px solid var(--line,#e8ecea);color:var(--ink,#17352e);cursor:pointer}.s3-location-bar>span:first-child{font-size:20px}.s3-location-bar small{display:block;color:var(--muted,#718078);font-size:10px}.s3-location-bar b{font-size:13px}.s3-location-change{margin-right:auto;color:#087f68;font-size:11px}.s3-loc-overlay{position:fixed;inset:0;z-index:1000;background:#0008;display:flex;align-items:center;justify-content:center;padding:12px}.s3-loc-modal{position:relative;background:var(--surface,#fff);color:var(--ink,#17352e);width:min(560px,100%);max-height:92dvh;overflow:auto;border-radius:18px;padding:20px;box-shadow:0 18px 70px #0003}.s3-loc-close{position:absolute;left:14px;top:10px;border:0;background:transparent;font-size:28px;color:inherit}.s3-loc-modal h2{margin:0 0 4px;font-size:20px}.s3-loc-modal p{font-size:12px;color:var(--muted,#718078);margin:0 0 14px}.s3-gps,.s3-save{width:100%;border:0;border-radius:11px;padding:13px;background:#087f68;color:#fff;font-weight:700;margin:8px 0;cursor:pointer}.s3-gps:disabled{opacity:.6}.s3-map{height:220px;background:#edf3f0;border-radius:12px;overflow:hidden;display:grid;place-items:center;margin:8px 0}.s3-coords{font-size:10px;color:var(--muted,#718078);margin-bottom:12px}.s3-loc-modal label{display:block;font-size:11px;font-weight:700;margin:10px 0 5px}.s3-loc-modal input,.s3-loc-modal select{width:100%;box-sizing:border-box;border:1px solid var(--line,#dce5e0);background:var(--surface,#fff);color:var(--ink,#17352e);padding:11px;border-radius:9px;font:inherit;font-size:12px}.s3-loc-error{background:#fff0ed;color:#a33420;padding:9px;border-radius:8px;font-size:11px;margin:8px 0}.s3-saved{width:100%;display:flex;justify-content:space-between;gap:8px;text-align:right;background:transparent;border:1px solid var(--line,#e5ebe7);border-radius:9px;padding:10px;margin:6px 0;color:inherit}.s3-saved span{font-size:10px;color:var(--muted,#718078)}.s3-map-link{display:block;text-align:center;color:#087f68;font-size:12px;margin:8px}@media(max-width:600px){.s3-loc-modal{max-height:94dvh;padding:16px}.s3-map{height:190px}}
"""
 css.write_text(c)
print("Location selector and checkout-to-courier handoff patched.")
