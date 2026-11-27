from pathlib import Path
import re

p=Path("src/App.tsx"); c=Path("src/style.css")
s=p.read_text(encoding="utf-8"); css=c.read_text(encoding="utf-8")

# Bounded local diagnostics: JS errors, unhandled rejections and failed HTTP calls.
logger = r"""
const SAREE_ISSUE_KEY='saree3:issue-log:v1';
function sareeRecordIssue(message:unknown,screen?:string){
 try{
  const old=JSON.parse(localStorage.getItem(SAREE_ISSUE_KEY)||'[]');
  const rows=Array.isArray(old)?old:[];
  rows.unshift({at:new Date().toISOString(),screen:screen||(window as any).__SAREE3_ACTIVE_SCREEN__||'غير محدد',message:String(message instanceof Error?message.message:message||'خطأ غير معروف').slice(0,500)});
  localStorage.setItem(SAREE_ISSUE_KEY,JSON.stringify(rows.slice(0,50)));
  window.dispatchEvent(new Event('saree3:issue-log-updated'));
 }catch{}
}
"""
if 'function sareeRecordIssue(' not in s:
 anchor="type Role = 'customer' | 'merchant' | 'driver' | 'admin';"
 if anchor not in s: raise SystemExit('issue logger: role type anchor missing')
 s=s.replace(anchor,logger+'\n'+anchor,1)

state=re.search(r"\[role,setRole\]=useState<Role>\('customer'\)",s)
if state and '[issueLog,setIssueLog]' not in s:
 s=s[:state.end()]+",[issueLog,setIssueLog]=useState<any[]>(()=>{try{return JSON.parse(localStorage.getItem(SAREE_ISSUE_KEY)||'[]')}catch{return []}})"+s[state.end():]

effect=r"""
 useEffect(()=>{
  const screen=()=>role+' / '+tab+(selectedStore?' / '+selectedStore:'');
  const refresh=()=>{try{const v=JSON.parse(localStorage.getItem(SAREE_ISSUE_KEY)||'[]');setIssueLog(Array.isArray(v)?v.slice(0,50):[])}catch{setIssueLog([])}};
  const onError=(e:ErrorEvent)=>sareeRecordIssue(e.message||e.error,screen());
  const onReject=(e:PromiseRejectionEvent)=>sareeRecordIssue(e.reason,screen());
  (window as any).__SAREE3_ACTIVE_SCREEN__=screen();
  window.addEventListener('error',onError);window.addEventListener('unhandledrejection',onReject);
  window.addEventListener('saree3:issue-log-updated',refresh);
  const originalFetch=window.fetch.bind(window);
  if(!(window as any).__SAREE3_FETCH_WRAPPED__){
   (window as any).__SAREE3_FETCH_WRAPPED__=true;
   window.fetch=(async(...args:Parameters<typeof fetch>)=>{
    const u=typeof args[0]==='string'?args[0]:args[0] instanceof Request?args[0].url:String(args[0]);
    try{const response=await originalFetch(...args);if(!response.ok)sareeRecordIssue('فشل نداء الخادم ('+response.status+') '+u,(window as any).__SAREE3_ACTIVE_SCREEN__);return response}
    catch(error){sareeRecordIssue('تعذر الاتصال بالخادم '+u+': '+String(error),(window as any).__SAREE3_ACTIVE_SCREEN__);throw error}
   }) as typeof fetch;
  }
  return()=>{window.removeEventListener('error',onError);window.removeEventListener('unhandledrejection',onReject);window.removeEventListener('saree3:issue-log-updated',refresh)};
 },[role,tab,selectedStore]);
"""
if 'SAREE3_FETCH_WRAPPED' not in s:
 anchor=' const count=cart.reduce'
 if anchor not in s: raise SystemExit('issue logger: effect anchor missing')
 s=s.replace(anchor,effect+'\n'+anchor,1)

page=r"""
 {tab==='issue-log'&&<section className="panel saree-issue-page" dir="rtl"><div className="section-title"><h2>سجل المشاكل</h2><button className="outline" onClick={()=>setTab('profile')}>رجوع</button></div>
 {!issueLog.length?<p className="muted">مفيش مشاكل مسجلة</p>:issueLog.map((x:any,i:number)=><article className="saree-issue-item" key={i}><b>{new Date(x.at).toLocaleString('ar-EG')}</b><small>{x.screen||'غير محدد'}</small><p>{x.message}</p></article>)}
 <button className="primary full" onClick={async()=>{const report=issueLog.map((x:any,i:number)=>(i+1)+') '+new Date(x.at).toLocaleString('ar-EG')+' | '+x.screen+' | '+x.message).join('\n')||'مفيش مشاكل مسجلة';try{await navigator.clipboard.writeText(report);notify('تم النسخ')}catch{const a=document.createElement('textarea');a.value=report;document.body.appendChild(a);a.select();const ok=document.execCommand('copy');a.remove();notify(ok?'تم النسخ':'تعذر النسخ')}}}>انسخ التقرير</button></section>}
"""
if 'saree-issue-page' not in s:
 anchor=" {role==='customer'&&tab==='support'&&"
 if anchor not in s: anchor=" {role==='customer'&&tab==='profile'&&"
 if anchor not in s: raise SystemExit('issue log: page insertion anchor missing')
 s=s.replace(anchor,page+'\n'+anchor,1)
profile=" {role==='customer'&&tab==='profile'&&"
if profile in s and 'saree-issue-shortcut' not in s:
 s=s.replace(profile,profile+'<button className="outline full saree-issue-shortcut" onClick={()=>setTab(\'issue-log\')}>سجل المشاكل</button>',1)

# Extend existing store queries to retrieve the optional merchant image.
s=s.replace("pharmacist_verified').eq('is_active',true)","pharmacist_verified,image_url').eq('is_active',true)")
s=s.replace("pharmacistVerified:Boolean(m.pharmacist_verified)}","pharmacistVerified:Boolean(m.pharmacist_verified),image:m.image_url||undefined}")
s=s.replace("commission_percent,delivery_fee,min_order')","commission_percent,delivery_fee,min_order,image_url')")

# WebP client compression and uploads to the already-existing product-images bucket.
upload=r"""
 const makeSareeWebp=async(file:File):Promise<Blob>=>{
  if(!file.type.startsWith('image/'))throw new Error('اختر صورة صالحة');
  const bmp=await createImageBitmap(file),scale=Math.min(1,800/Math.max(bmp.width,bmp.height));
  const canvas=document.createElement('canvas');canvas.width=Math.max(1,Math.round(bmp.width*scale));canvas.height=Math.max(1,Math.round(bmp.height*scale));
  const ctx=canvas.getContext('2d');if(!ctx)throw new Error('تعذر تجهيز الصورة');ctx.drawImage(bmp,0,0,canvas.width,canvas.height);bmp.close();
  return await new Promise<Blob>((resolve,reject)=>canvas.toBlob(b=>b?resolve(b):reject(new Error('تعذر ضغط الصورة')),'image/webp',.82));
 };
 const uploadSareeImage=async(kind:'merchant'|'product',id:string,file?:File)=>{
  if(!file)return;if(!supabase){notify('رفع الصور يحتاج اتصال الخادم');return}
  const merchantId=kind==='merchant'?id:products.find((p:any)=>p.id===id)?.storeId;
  if(!merchantId||!merchantIds.includes(merchantId)){notify('لا تملك صلاحية رفع الصورة');return}
  try{
   const blob=await makeSareeWebp(file),path=merchantId+'/'+kind+'/'+id+'.webp';
   const {error:upErr}=await supabase.storage.from('product-images').upload(path,blob,{contentType:'image/webp',upsert:true,cacheControl:'3600'});if(upErr)throw upErr;
   const url=supabase.storage.from('product-images').getPublicUrl(path).data.publicUrl;
   if(kind==='product'){const {error}=await supabase.from('products').update({image_url:url}).eq('id',id);if(error)throw error;setProducts((v:any[])=>v.map(p=>p.id===id?{...p,imageUrl:url}:p))}
   else{const {error}=await supabase.rpc('set_merchant_image_url',{p_merchant_id:id,p_image_url:url});if(error)throw error;setMerchantStoreRows((v:any[])=>v.map(m=>m.id===id?{...m,image_url:url}:m));setStores((v:any[])=>v.map(m=>m.id===id?{...m,image:url}:m))}
   notify('تم رفع الصورة بنجاح')
  }catch(e:any){sareeRecordIssue(e?.message||e);notify('تعذر رفع الصورة: '+(e?.message||'خطأ غير معروف'))}
 };
"""
if 'const makeSareeWebp=' not in s:
 anchor=' const toggleMerchantStoreOpen=async(store:any)=>'
 if anchor not in s: raise SystemExit('merchant upload: operations helper missing')
 s=s.replace(anchor,upload+'\n'+anchor,1)

panel=r"""
 <section className="panel saree-merchant-images"><h2>صور المتجر والمنتجات</h2>
 {merchantStoreRows.map((m:any)=><article className="saree-upload-row" key={m.id}><div className="saree-upload-preview">{m.image_url?<img src={m.image_url} alt={m.name}/>:<span>{m.name?.slice(0,1)||'م'}</span>}</div><b>{m.name}</b><label className="outline saree-upload-button">صورة المتجر<input hidden type="file" accept="image/*" onChange={e=>void uploadSareeImage('merchant',m.id,e.target.files?.[0])}/></label></article>)}
 <h3>صور المنتجات</h3>{products.filter((p:any)=>merchantIds.includes(p.storeId)).map((p:any)=><article className="saree-upload-row" key={p.id}><div className="saree-upload-preview">{p.imageUrl?<img src={p.imageUrl} alt={p.name}/>:<span>{p.name?.slice(0,1)||'ص'}</span>}</div><b>{p.name}</b><label className="outline saree-upload-button">رفع صورة<input hidden type="file" accept="image/*" onChange={e=>void uploadSareeImage('product',p.id,e.target.files?.[0])}/></label></article>)}
 </section>
"""
if 'saree-merchant-images' not in s:
 marker='<p className="muted">مواعيد العمل الأسبوعية'
 if marker not in s: raise SystemExit('merchant upload: profile insertion anchor missing')
 s=s.replace(marker,panel+'\n'+marker,1)

p.write_text(s,encoding="utf-8")
if 'SAREE3 pixel-faithful visual foundation' not in css:
 css += """
@import url('https://fonts.googleapis.com/css2?family=Noto+Kufi+Arabic:wght@400;500;600;700;800&display=swap');
:root{--green:#6FCB00;--lime:#A8E02A;--soft:#F1FAD3;--surface:#fff;--bg:#F3F4F1;--ink:#111;--muted:#81877c;--line:#e8ebe2}
html,body,#root,button,input,textarea,select{font-family:'Noto Kufi Arabic',sans-serif}
body{background:#F3F4F1;color:#111}
.panel,.store-card,.order-card,.product,.dialog,.cart-line{border:0!important;border-radius:24px!important;box-shadow:0 8px 24px rgba(20,27,13,.07)}
button.primary,.primary,.add,.cart-btn{background:#6FCB00!important;border-color:#6FCB00!important;color:#111!important;border-radius:999px!important}
.saree-issue-page{padding:18px}.saree-issue-item{background:#F3F4F1;border-radius:16px;padding:12px;margin:8px 0}.saree-issue-item b,.saree-issue-item small{display:block}.saree-issue-item small{color:#81877c}.saree-issue-item p{overflow-wrap:anywhere}
.saree-merchant-images{padding:18px}.saree-upload-row{display:flex;align-items:center;gap:10px;padding:10px 0;border-bottom:1px solid #e8ebe2}.saree-upload-preview{width:56px;height:56px;border-radius:14px;overflow:hidden;background:#F1FAD3;display:grid;place-items:center}.saree-upload-preview img{width:100%;height:100%;object-fit:cover}.saree-upload-row>b{flex:1}.saree-upload-button{cursor:pointer;white-space:nowrap}
@media(prefers-reduced-motion:no-preference){button{transition:transform .18s ease}button:active{transform:scale(.97)}}
@media(prefers-reduced-motion:reduce){*,*::before,*::after{animation-duration:.01ms!important;transition-duration:.01ms!important}}
"""
 css=css.replace("@import url('https://fonts.googleapis.com/css2?family=Noto+Kufi+Arabic:wght@400;500;600;700;800&display=swap');","")
 css="@import url('https://fonts.googleapis.com/css2?family=Noto+Kufi+Arabic:wght@400;500;600;700;800&display=swap');\\n"+css
 c.write_text(css,encoding="utf-8")
print("Issue log, WebP merchant/product uploads and visual foundation patched.")
