import React, {useEffect, useRef, useState} from 'react';
type SavedAddress={id:string;label:string;area:string;street:string;landmark:string;unit:string;lat:number|null;lng:number|null};
const KEY='saree3:saved-addresses';
const areas=['وسط البلد','شارع العرفاني','شارع المجيدي','حي جنوب','حي شمال','المحطة','الروضة','تونة الجبل','ديروط أم نخلة','قرية أخرى'];
const empty:SavedAddress={id:'',label:'المنزل',area:'وسط البلد',street:'',landmark:'',unit:'',lat:null,lng:null};
export default function LocationSystem(){
 const [addresses,setAddresses]=useState<SavedAddress[]>(()=>{try{return JSON.parse(localStorage.getItem(KEY)||'[]')}catch{return[]}});
 const [current,setCurrent]=useState<SavedAddress>(()=>{try{return JSON.parse(localStorage.getItem('saree3:selected-address')||'null')||empty}catch{return empty}});
 const [open,setOpen]=useState(false),[busy,setBusy]=useState(false),[error,setError]=useState('');
 const mapRef=useRef<HTMLDivElement>(null),mapObj=useRef<any>(null),markerRef=useRef<any>(null);
 const update=(patch:Partial<SavedAddress>)=>setCurrent(v=>({...v,...patch}));
 const chooseCoords=(lat:number,lng:number)=>{update({lat,lng});if(markerRef.current&&mapObj.current){markerRef.current.setLatLng([lat,lng]);mapObj.current.setView([lat,lng],16)}};
 const locate=()=>{setError('');if(!navigator.geolocation){setError('المتصفح لا يدعم تحديد الموقع');return}setBusy(true);navigator.geolocation.getCurrentPosition(p=>{chooseCoords(p.coords.latitude,p.coords.longitude);setBusy(false)},e=>{setBusy(false);setError(e.code===1?'اسمح للتطبيق باستخدام الموقع من إعدادات الهاتف':'تعذر تحديد موقعك، حاول مرة أخرى')},{enableHighAccuracy:true,timeout:15000,maximumAge:0})};
 useEffect(()=>{if(!open||!mapRef.current)return;let cancelled=false;const init=()=>{if(cancelled||!(window as any).L||!mapRef.current)return;const L=(window as any).L;const lat=current.lat??27.735,lng=current.lng??30.841;const map=L.map(mapRef.current).setView([lat,lng],current.lat?16:13);L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',{attribution:'© OpenStreetMap'}).addTo(map);const marker=L.marker([lat,lng],{draggable:true}).addTo(map);marker.on('dragend',()=>{const p=marker.getLatLng();update({lat:p.lat,lng:p.lng})});map.on('click',(e:any)=>{marker.setLatLng(e.latlng);update({lat:e.latlng.lat,lng:e.latlng.lng})});mapObj.current=map;markerRef.current=marker};if((window as any).L)init();else{const s=document.createElement('script');s.src='https://unpkg.com/leaflet@1.9.4/dist/leaflet.js';s.onload=init;document.head.appendChild(s);const l=document.createElement('link');l.rel='stylesheet';l.href='https://unpkg.com/leaflet@1.9.4/dist/leaflet.css';document.head.appendChild(l)}return()=>{cancelled=true;mapObj.current?.remove();mapObj.current=null;markerRef.current=null}},[open]);
 const select=(a:SavedAddress)=>{setCurrent(a);localStorage.setItem('saree3:selected-address',JSON.stringify(a));window.dispatchEvent(new CustomEvent('saree3:address-selected',{detail:a}));setOpen(false);setError('')};
 const save=()=>{if(!current.street.trim()||!current.landmark.trim()){setError('اكتب الشارع والعلامة المميزة لتسهيل وصول الكابتن');return}const item={...current,id:current.id||String(Date.now())};const next=[item,...addresses.filter(a=>a.id!==item.id)];setAddresses(next);localStorage.setItem(KEY,JSON.stringify(next));select(item)};
 return <><button className="s3-location-bar" onClick={()=>setOpen(true)}><span>📍</span><span><small>التوصيل إلى:</small><b>{current.area||'حدد عنوان التوصيل'}</b></span><span className="s3-location-change">تغيير⌄</span></button>
 {open&&<div className="s3-loc-overlay" onClick={()=>setOpen(false)}><section className="s3-loc-modal" dir="rtl" onClick={e=>e.stopPropagation()}><button className="s3-loc-close" onClick={()=>setOpen(false)}>×</button><h2>عنوان التوصيل</h2><p>حدد مكانك على الخريطة واكتب وصفًا واضحًا للكابتن</p>
 <button className="s3-gps" onClick={locate} disabled={busy}>{busy?'جارٍ تحديد موقعك...':'◎ تحديد موقعي الحالي تلقائيًا (GPS)'}</button><div ref={mapRef} className="s3-map">خريطة ملوي - اضغط لتحديد موقعك أو اسحب الدبوس</div>
 <div className="s3-coords">{current.lat!==null?'الإحداثيات: '+current.lat.toFixed(5)+', '+(current.lng||0).toFixed(5):'حدد موقعك من الخريطة'}</div>
 <label>المنطقة أو القرية *</label><select value={current.area} onChange={e=>update({area:e.target.value})}>{areas.map(a=><option key={a}>{a}</option>)}</select>
 <label>اسم الشارع أو المنطقة *</label><input value={current.street} onChange={e=>update({street:e.target.value})} placeholder="مثال: شارع المدرسة" />
 <label>علامة مميزة قريبة منك *</label><input value={current.landmark} onChange={e=>update({landmark:e.target.value})} placeholder="بجوار مسجد... أو أمام صيدلية..." />
 <label>رقم العمارة / الدور / الشقة (اختياري)</label><input value={current.unit} onChange={e=>update({unit:e.target.value})} placeholder="عمارة 12، الدور الثاني" />
 <label>اسم العنوان</label><select value={current.label} onChange={e=>update({label:e.target.value})}><option>المنزل</option><option>العمل</option><option>عنوان آخر</option></select>
 {error&&<div className="s3-loc-error">{error}</div>}
 {addresses.length>0&&<><h3>عناويني المحفوظة</h3>{addresses.map(a=><button className="s3-saved" key={a.id} onClick={()=>select(a)}><b>{a.label}</b><span>{a.area} · {a.street}</span></button>)}</>}
 <button className="s3-save" onClick={save}>حفظ واختيار العنوان</button>
 {current.lat!==null&&<a className="s3-map-link" href={'https://www.google.com/maps?q='+current.lat+','+current.lng} target="_blank" rel="noreferrer">فتح الموقع على الخريطة ↗</a>}
 </section></div>}</>
}
