import React, {useEffect, useRef, useState} from 'react';
import {Capacitor} from '@capacitor/core';
import {Geolocation} from '@capacitor/geolocation';

type SavedAddress={id:string;label:string;area:string;street:string;landmark:string;unit:string;lat:number|null;lng:number|null};
const KEY='saree3:saved-addresses';
const SUPABASE_URL=(import.meta as any).env?.VITE_SUPABASE_URL as string|undefined;
const SUPABASE_KEY=((import.meta as any).env?.VITE_SUPABASE_PUBLISHABLE_KEY||(import.meta as any).env?.VITE_SUPABASE_ANON_KEY) as string|undefined;
const areas=['وسط البلد','شارع العرفاني','شارع المجيدي','شارع الجمهورية','شارع الجلاء','شارع العاشر','شارع المحطة','حي جنوب','حي شمال','المحطة','الروضة','السوق القديم','تونة الجبل','ديروط أم نخلة','قرية أخرى'];
const empty:SavedAddress={id:'',label:'المنزل',area:'وسط البلد',street:'',landmark:'',unit:'',lat:null,lng:null};

function authSession():any{
  try{for(let i=0;i<localStorage.length;i++){const k=localStorage.key(i)||'';if(k.startsWith('sb-')&&k.endsWith('-auth-token')){const v=JSON.parse(localStorage.getItem(k)||'{}');if(v.access_token&&v.user?.id)return v}}}catch{}
  return null;
}
async function dbRequest(path:string,init:RequestInit={}){
  const session=authSession();
  if(!SUPABASE_URL||!SUPABASE_KEY||!session?.access_token||!session?.user?.id)throw new Error('سجّل الدخول لحفظ العنوان على حسابك');
  const response=await fetch(SUPABASE_URL+'/rest/v1/'+path,{...init,headers:{apikey:SUPABASE_KEY,Authorization:'Bearer '+session.access_token,'Content-Type':'application/json',...(init.headers||{})}});
  if(!response.ok)throw new Error(await response.text());
  return response.status===204?null:response.json();
}
function osmLink(lat:number,lng:number){return 'https://www.openstreetmap.org/?mlat='+lat+'&mlon='+lng+'#map=18/'+lat+'/'+lng}

export default function LocationSystem(){
  const [addresses,setAddresses]=useState<SavedAddress[]>(()=>{try{return JSON.parse(localStorage.getItem(KEY)||'[]')}catch{return[]}});
  const [current,setCurrent]=useState<SavedAddress>(()=>{try{return JSON.parse(localStorage.getItem('saree3:selected-address')||'null')||empty}catch{return empty}});
  const [open,setOpen]=useState(false),[busy,setBusy]=useState(false),[saving,setSaving]=useState(false),[geocoding,setGeocoding]=useState(false),[error,setError]=useState('');
  const mapRef=useRef<HTMLDivElement>(null),mapObj=useRef<any>(null),markerRef=useRef<any>(null);

  useEffect(()=>{const show=()=>setOpen(true);window.addEventListener('saree3:open-address',show);return()=>window.removeEventListener('saree3:open-address',show)},[]);
  useEffect(()=>{
    let live=true;
    const loadAddresses=async()=>{
      try{
        const rows=await dbRequest('customer_addresses?select=id,label,area,street,landmark,unit_details,latitude,longitude&order=created_at.desc');
        if(!live||!Array.isArray(rows))return;
        const mapped=rows.map((r:any)=>({id:r.id,label:r.label||'المنزل',area:r.area||'غير محدد',street:r.street||'',landmark:r.landmark||'',unit:r.unit_details||'',lat:r.latitude??null,lng:r.longitude??null}));
        setAddresses(mapped);localStorage.setItem(KEY,JSON.stringify(mapped));
      }catch{/* Keep locally saved addresses available while offline or signed out. */}
    };
    void loadAddresses();window.addEventListener('saree3:auth-changed',loadAddresses);
    return()=>{live=false;window.removeEventListener('saree3:auth-changed',loadAddresses)};
  },[]);

  const update=(patch:Partial<SavedAddress>)=>setCurrent(v=>({...v,...patch}));
  const chooseCoords=(lat:number,lng:number)=>{
    update({lat,lng});
    if(markerRef.current&&mapObj.current){markerRef.current.setLatLng([lat,lng]);mapObj.current.setView([lat,lng],16)}
  };
  const locate=async()=>{
    setError('');setBusy(true);
    try{
      let position:any;
      if(Capacitor.isNativePlatform()){
        let permission=await Geolocation.checkPermissions();
        if(permission.location!=='granted'&&permission.coarseLocation!=='granted')permission=await Geolocation.requestPermissions();
        if(permission.location!=='granted'&&permission.coarseLocation!=='granted')throw new Error('لم تسمح للتطبيق بالوصول إلى الموقع. افتح إعدادات التطبيق وفعّل إذن الموقع.');
        position=await Geolocation.getCurrentPosition({enableHighAccuracy:true,timeout:20000,maximumAge:0});
      }else{
        if(!navigator.geolocation)throw new Error('المتصفح لا يدعم تحديد الموقع');
        position=await new Promise<GeolocationPosition>((resolve,reject)=>navigator.geolocation.getCurrentPosition(resolve,reject,{enableHighAccuracy:true,timeout:20000,maximumAge:0}));
      }
      chooseCoords(position.coords.latitude,position.coords.longitude);
    }catch(e:any){
      const message=String(e?.message||'');
      setError(message.includes('denied')||message.includes('permission')?'اسمح للتطبيق باستخدام الموقع من إعدادات الهاتف ثم حاول مرة أخرى':message||'تعذر تحديد موقعك. تأكد من تشغيل GPS وحاول مرة أخرى');
    }finally{setBusy(false)}
  };

  const readAddressFromMap=async()=>{
    if(current.lat===null||current.lng===null){setError('حدد موقعك أولًا من GPS أو الخريطة');return}
    setGeocoding(true);setError('');
    try{
      const url='https://nominatim.openstreetmap.org/reverse?format=jsonv2&addressdetails=1&lat='+encodeURIComponent(current.lat)+'&lon='+encodeURIComponent(current.lng)+'&zoom=18&accept-language=ar';
      const response=await fetch(url,{headers:{Accept:'application/json'}});
      if(!response.ok)throw new Error('خدمة قراءة العنوان غير متاحة الآن. اكتب التفاصيل يدويًا.');
      const result=await response.json();
      const a=result.address||{};
      const area=a.neighbourhood||a.suburb||a.quarter||a.village||a.town||a.city_district||a.city||'';
      const street=a.road||a.pedestrian||a.residential||a.path||a.footway||'';
      const landmark=a.amenity||a.shop||a.building||a.public_building||'';
      update({area:area||current.area,street:street||current.street,landmark:current.landmark||landmark});
      if(!area&&!street&&!landmark)setError('لم نعثر على وصف تفصيلي لهذا الموقع. اكتب العنوان يدويًا.');
    }catch(e:any){setError(e?.message||'تعذر استخراج العنوان تلقائيًا؛ يمكنك إدخاله يدويًا.')}
    finally{setGeocoding(false)}
  };

  useEffect(()=>{
    if(!open||!mapRef.current)return;
    let cancelled=false;
    const init=()=>{
      if(cancelled||!(window as any).L||!mapRef.current)return;
      const L=(window as any).L,lat=current.lat??27.735,lng=current.lng??30.841;
      const map=L.map(mapRef.current).setView([lat,lng],current.lat!==null?16:13);
      L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',{attribution:'© OpenStreetMap contributors'}).addTo(map);
      const marker=L.marker([lat,lng],{draggable:true}).addTo(map);
      marker.on('dragend',()=>{const p=marker.getLatLng();update({lat:p.lat,lng:p.lng})});
      map.on('click',(e:any)=>{marker.setLatLng(e.latlng);update({lat:e.latlng.lat,lng:e.latlng.lng})});
      mapObj.current=map;markerRef.current=marker;
      window.setTimeout(()=>map.invalidateSize(),120);
    };
    if((window as any).L)init();
    else{
      const s=document.createElement('script');s.src='https://unpkg.com/leaflet@1.9.4/dist/leaflet.js';s.onload=init;document.head.appendChild(s);
      const l=document.createElement('link');l.rel='stylesheet';l.href='https://unpkg.com/leaflet@1.9.4/dist/leaflet.css';document.head.appendChild(l);
    }
    return()=>{cancelled=true;mapObj.current?.remove();mapObj.current=null;markerRef.current=null};
  },[open]);

  const select=(a:SavedAddress)=>{
    setCurrent(a);localStorage.setItem('saree3:selected-address',JSON.stringify(a));
    window.dispatchEvent(new CustomEvent('saree3:address-selected',{detail:a}));setOpen(false);setError('');
  };
  const save=async()=>{
    if(!current.street.trim()){setError('اكتب اسم الشارع أو المنطقة لتسهيل وصول الكابتن');return}
    if(current.lat===null||current.lng===null){setError('حدد موقع التسليم من GPS أو حرّك الدبوس على الخريطة');return}
    const validUuid=(v:string)=>/^[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i.test(v);
    const item={...current,id:validUuid(current.id)?current.id:crypto.randomUUID()};
    const next=[item,...addresses.filter(a=>a.id!==item.id)];
    setAddresses(next);localStorage.setItem(KEY,JSON.stringify(next));setSaving(true);
    try{
      const session=authSession();if(!session?.user?.id)throw new Error('سجّل الدخول لحفظ العنوان على حسابك');
      await dbRequest('customer_addresses?on_conflict=id',{method:'POST',headers:{Prefer:'resolution=merge-duplicates,return=minimal'},body:JSON.stringify({id:item.id,customer_id:session.user.id,label:item.label,area:item.area,street:item.street,address_text:[item.area,item.street,item.landmark,item.unit].filter(Boolean).join(' - '),landmark:item.landmark||null,unit_details:item.unit||null,latitude:item.lat,longitude:item.lng,is_default:item.label==='المنزل'})});
      select(item);
    }catch(e){setError('تم الاحتفاظ بالعنوان على هذا الجهاز، لكن لم يُزامن مع حسابك: '+(e as Error).message)}
    finally{setSaving(false)}
  };

  return <>
    <button className="s3-location-bar" onClick={()=>setOpen(true)}><span>📍</span><span><small>التوصيل إلى:</small><b>{current.area||'حدد عنوان التوصيل'}</b></span><span className="s3-location-change">تغيير⌄</span></button>
    {open&&<div className="s3-loc-overlay" onClick={()=>setOpen(false)}>
      <section className="s3-loc-modal" dir="rtl" onClick={e=>e.stopPropagation()}>
        <button className="s3-loc-close" onClick={()=>setOpen(false)}>×</button>
        <h2>عنوان التوصيل</h2><p>حدد مكانك بدقة، وسيصل العنوان والإحداثيات للكابتن مع الطلب</p>
        <button className="s3-gps" onClick={locate} disabled={busy}>{busy?'جارٍ تحديد موقعك...':'◎ تحديد موقعي الحالي تلقائيًا (GPS)'}</button>
        <div ref={mapRef} className="s3-map">خريطة ملوي - اضغط لتحديد موقعك أو اسحب الدبوس</div>
        <div className="s3-coords">{current.lat!==null?'الإحداثيات: '+current.lat.toFixed(5)+', '+(current.lng??0).toFixed(5):'حدد موقعك من الخريطة'}</div>
        <button className="s3-gps" onClick={readAddressFromMap} disabled={geocoding||current.lat===null}>{geocoding?'جارٍ قراءة العنوان...':'استخراج العنوان تلقائيًا من الخريطة'}</button>
        <label>المنطقة أو القرية *</label><input list="s3-mallawi-areas" value={current.area} onChange={e=>update({area:e.target.value})} placeholder="اختر أو اكتب اسم المنطقة/القرية"/><datalist id="s3-mallawi-areas">{areas.map(a=><option key={a} value={a}/>)}</datalist>
        <label>اسم الشارع أو المنطقة *</label><input value={current.street} onChange={e=>update({street:e.target.value})} placeholder="مثال: شارع المدرسة"/>
        <label>علامة مميزة قريبة منك</label><input value={current.landmark} onChange={e=>update({landmark:e.target.value})} placeholder="بجوار مسجد... أو أمام صيدلية..."/>
        <label>رقم العمارة / الدور / الشقة (اختياري)</label><input value={current.unit} onChange={e=>update({unit:e.target.value})} placeholder="عمارة 12، الدور الثاني، شقة 4"/>
        <label>اسم العنوان</label><select value={current.label} onChange={e=>update({label:e.target.value})}><option>المنزل</option><option>العمل</option><option>عنوان آخر</option></select>
        {error&&<div className="s3-loc-error">{error}</div>}
        {addresses.length>0&&<><h3>عناويني المحفوظة</h3>{addresses.map(a=><button className="s3-saved" key={a.id} onClick={()=>select(a)}><b>{a.label}</b><span>{a.area} · {a.street}</span></button>)}</>}
        <button className="s3-save" onClick={save} disabled={saving}>{saving?'جارٍ حفظ العنوان...':'حفظ واختيار العنوان'}</button>
        {current.lat!==null&&<a className="s3-map-link" href={osmLink(current.lat,current.lng??0)} target="_blank" rel="noreferrer">فتح الموقع على خريطة OpenStreetMap ↗</a>}
        <small className="s3-attribution">الخريطة © OpenStreetMap contributors · قراءة العنوان عبر Nominatim</small>
      </section>
    </div>}
  </>;
}
