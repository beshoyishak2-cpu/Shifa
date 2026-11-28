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

# Install diagnostics before App/Supabase modules are evaluated so backend requests are covered.
diag=Path("src/lib/issue-log.ts")
diag.parent.mkdir(parents=True,exist_ok=True)
if not diag.exists():
 diag.write_text("""
const KEY='saree3:issue-log:v1';
function record(message:unknown){
 try{const old=JSON.parse(localStorage.getItem(KEY)||'[]');const rows=Array.isArray(old)?old:[];
 rows.unshift({at:new Date().toISOString(),screen:(window as any).__SAREE3_ACTIVE_SCREEN__||'غير محدد',message:String(message instanceof Error?message.message:message||'خطأ غير معروف').slice(0,500)});
 localStorage.setItem(KEY,JSON.stringify(rows.slice(0,50)));window.dispatchEvent(new Event('saree3:issue-log-updated'));
 }catch{}
}
if(typeof window!=='undefined'&&!(window as any).__SAREE3_DIAGNOSTICS_READY__){
 (window as any).__SAREE3_DIAGNOSTICS_READY__=true;
 window.addEventListener('error',(e:ErrorEvent)=>record(e.message||e.error));
 window.addEventListener('unhandledrejection',(e:PromiseRejectionEvent)=>record(e.reason));
 const original=window.fetch.bind(window);
 window.fetch=(async(...args:Parameters<typeof fetch>)=>{
  const u=typeof args[0]==='string'?args[0]:args[0] instanceof Request?args[0].url:String(args[0]);
  try{const response=await original(...args);if(!response.ok)record('فشل نداء الخادم ('+response.status+') '+u);return response}
  catch(e){record('تعذر الاتصال بالخادم '+u+': '+String(e));throw e}
 }) as typeof fetch;
}
""",encoding="utf-8")
main=Path("src/main.tsx")
if not main.exists(): raise SystemExit("src/main.tsx missing for diagnostics import")
mt=main.read_text(encoding="utf-8")
if "import './lib/issue-log';" not in mt:
 main.write_text("import './lib/issue-log';\n"+mt,encoding="utf-8")

effect=r"""
 useEffect(()=>{
  const refresh=()=>{try{const v=JSON.parse(localStorage.getItem(SAREE_ISSUE_KEY)||'[]');setIssueLog(Array.isArray(v)?v.slice(0,50):[])}catch{setIssueLog([])}};
  (window as any).__SAREE3_ACTIVE_SCREEN__=role+' / '+tab+(selectedStore?' / '+selectedStore:'');
  window.addEventListener('saree3:issue-log-updated',refresh);
  return()=>window.removeEventListener('saree3:issue-log-updated',refresh);
 },[role,tab,selectedStore]);
"""
if 'const count=cart.reduce' not in s: raise SystemExit("issue log effect anchor missing")
if 'saree-issue-page' not in s:
 anchor=' const count=cart.reduce'
 if anchor not in s: raise SystemExit("issue log effect anchor missing")
 s=s.replace(anchor,effect+'\n'+anchor,1)
s=s.replace("if 'SAREE3_FETCH_WRAPPED' not in s:\n anchor=' const count=cart.reduce'\n if anchor not in s: raise SystemExit('issue logger: effect anchor missing')\n s=s.replace(anchor,effect+'\\n'+anchor,1)","if 'saree-issue-page' not in s:\n anchor=' const count=cart.reduce'\n s=s.replace(anchor,effect+'\\n'+anchor,1)")
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
profile=" {role==='customer'&&tab==='profile'&&<>"
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


# Draw the home hero illustration as an original, clean SVG guided by the supplied reference.
brand_dir=Path("public/brand");brand_dir.mkdir(parents=True,exist_ok=True)
hero_svg="""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 460" role="img" aria-labelledby="title">
<title id="title">منزل وشجرة ومندوب سريع على دراجة توصيل</title>
<circle cx="300" cy="232" r="202" fill="#e8f5bd"/>
<path d="M48 388h504" stroke="#141b0d" stroke-width="13" stroke-linecap="round"/>
<path d="M92 225 215 115l127 110v160H92z" fill="#fff" stroke="#141b0d" stroke-width="17" stroke-linejoin="round"/>
<path d="M170 385V270h88v115" fill="#dff0b1" stroke="#141b0d" stroke-width="12"/>
<path d="M182 270h64M182 290h64" stroke="#141b0d" stroke-width="8" stroke-linecap="round"/>
<circle cx="259" cy="190" r="26" fill="#dff0b1" stroke="#141b0d" stroke-width="10"/>
<path d="M259 165v50M234 190h50" stroke="#141b0d" stroke-width="7"/>
<path d="M70 388c0-43 7-75 22-94 18-24 37-31 53-26 14 4 19 18 11 34-12 22-25 39-24 86" fill="#6fcb00" stroke="#141b0d" stroke-width="12" stroke-linejoin="round"/>
<path d="M104 284c-24-21-28-42-14-62 19 9 31 26 31 49M126 274c-2-29 8-48 31-57 7 25-1 44-22 61" fill="#a8e02a" stroke="#141b0d" stroke-width="8"/>
<path d="M430 75h112a24 24 0 0 1 24 24v54a24 24 0 0 1-24 24h-44l-26 25v-25h-42a24 24 0 0 1-24-24V99a24 24 0 0 1 24-24z" fill="#fff" stroke="#141b0d" stroke-width="10"/>
<path d="M453 116h66M453 139h44" stroke="#6fcb00" stroke-width="12" stroke-linecap="round"/>
<circle cx="407" cy="337" r="49" fill="#fff" stroke="#141b0d" stroke-width="14"/>
<circle cx="545" cy="337" r="49" fill="#fff" stroke="#141b0d" stroke-width="14"/>
<path d="M407 337h70l-34-91h-41l-24 91M443 246h52l39 91M476 246l18-48h29" fill="none" stroke="#141b0d" stroke-width="16" stroke-linecap="round" stroke-linejoin="round"/>
<path d="M379 338h-24l-20-31 13-13h42M492 337h67l-11 21h-57" fill="#6fcb00" stroke="#141b0d" stroke-width="12" stroke-linejoin="round"/>
<circle cx="462" cy="160" r="25" fill="#141b0d"/>
<path d="M441 157c2-31 31-44 53-22l15 22-15 15h-35z" fill="#6fcb00" stroke="#141b0d" stroke-width="9"/>
<path d="M444 182c-15 29-18 54-5 77l32 35 40-15-12-38 26-25-10-17-39 19-15-39z" fill="#6fcb00" stroke="#141b0d" stroke-width="12" stroke-linejoin="round"/>
<path d="M451 209 409 242l-24-14-13 17 39 29 60-31" fill="#fff" stroke="#141b0d" stroke-width="12" stroke-linejoin="round"/>
<path d="M467 286 442 328l-28 13 7 18h58l42-58" fill="#fff" stroke="#141b0d" stroke-width="12" stroke-linejoin="round"/>
<path d="M452 160h20" stroke="#fff" stroke-width="7" stroke-linecap="round"/>
<path d="M356 365h164" stroke="#6fcb00" stroke-width="10" stroke-linecap="round"/>
</svg>"""
(brand_dir/"saree-hero-illustration.svg").write_text(hero_svg,encoding="utf-8")
hero_art=re.compile(r'<div className="hero-art"[^>]*>[\s\S]*?</div>')
s,n=hero_art.subn('<div className="hero-art"><img src="/brand/saree-hero-illustration.svg" alt="" loading="eager"/></div>',s,count=1)
if n!=1: raise SystemExit("Could not replace home hero artwork with the approved-style SVG")

# Keep exactly one home promotion: the green "طلبك أقرب مما تتخيل" banner.
# Remove the legacy cream welcome hero that otherwise renders as a second banner.
def remove_legacy_welcome_hero(source: str) -> str:
    welcome = "أهلاً بك في سريع"
    pos = source.find(welcome)
    if pos < 0:
        # The extracted source may already have had its welcome copy removed.
        return source
    candidates = list(re.finditer(r"<(div|section)\b[^>]*className=['\"]hero(?:\s|['\"])[^>]*>", source[:pos]))
    if not candidates:
        raise SystemExit("Found the old welcome copy but could not locate its hero container")
    opening = candidates[-1]
    tag = opening.group(1)
    token = re.compile(r"</?"+tag+r"\b[^>]*>")
    depth = 0
    for match in token.finditer(source, opening.start()):
        if match.group(0).startswith('</'):
            depth -= 1
            if depth == 0:
                return source[:opening.start()] + source[match.end():]
        elif not match.group(0).endswith('/>'):
            depth += 1
    raise SystemExit("Legacy welcome hero JSX is not balanced")

s = remove_legacy_welcome_hero(s)

# Reuse the approved scooter/house SVG inside the green promo instead of the bag glyph.
promo_art = re.compile(r'<div className="saree-promo-art"[^>]*>.*?</div>', re.S)
s, promo_count = promo_art.subn(
    '<div className="saree-promo-art" aria-hidden="true"><img src="/brand/saree-hero-illustration.svg" alt="" loading="eager"/></div>',
    s, count=1
)
if promo_count != 1:
    raise SystemExit("Could not place the scooter illustration inside the single green home banner")

if s.count('className="saree-home-promo"') != 1:
    raise SystemExit("Home must contain exactly one green promotion banner")
if 'أهلاً بك في سريع' in s:
    raise SystemExit("Legacy cream welcome hero remains on the home screen")
# Keep the approved hero as the first focal card; remove the older duplicate promo/repeat strips.


# Update the source smoke assertion to follow the approved SVG asset instead of the old inline placeholder.
test_file=Path("tests/source-smoke.test.cjs")

if test_file.exists():
 t=test_file.read_text(encoding="utf-8")
 if "exactly one green home banner" not in t:
  t += """
test('home shows one green promo with scooter art and repeat-order card', () => {
  const source = fs.readFileSync(path.join(root, 'src/App.tsx'), 'utf8');
  assert.equal((source.match(/className="saree-home-promo"/g) || []).length, 1);
  assert.ok(source.includes('طلبك أقرب مما تتخيل'));
  assert.ok(source.includes('src="/brand/saree-hero-illustration.svg"'));
  assert.ok(source.includes('اطلب تاني'));
  assert.ok(!source.includes('أهلاً بك في سريع'));
});
"""
  test_file.write_text(t,encoding="utf-8")

 t=t.replace("""assert.ok(source.includes('className="hero-art" aria-hidden="true"><svg viewBox="0 0 160 160"'))""","""assert.ok(source.includes('src="/brand/saree-hero-illustration.svg"'))""")
 test_file.write_text(t,encoding="utf-8")

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
 css="@import url('https://fonts.googleapis.com/css2?family=Noto+Kufi+Arabic:wght@400;500;600;700;800&display=swap');\n"+css

 css += """
.hero{background:#F1FAD3!important;color:#111!important;border:0!important;border-radius:24px!important;box-shadow:0 8px 24px rgba(20,27,13,.06)!important;min-height:230px;padding:24px!important}
.hero h1{color:#111!important}.hero h1 em{color:#6FCB00!important;font-style:normal}.hero p{color:#42483d!important}
.hero-art{width:min(42%,280px)!important;min-width:170px!important;height:220px!important;background:transparent!important}
.hero-art img{width:100%;height:100%;object-fit:contain}
.hero .hero-tags span{background:#e6f5c3!important;color:#456c00!important;border-radius:999px!important;padding:7px 12px!important}
@media(max-width:700px){.hero{min-height:180px!important;padding:16px!important;gap:8px!important}.hero-art{width:38%!important;min-width:110px!important;height:150px!important}.hero h1{font-size:24px!important}.hero p{font-size:11px!important}}
"""

 c.write_text(css,encoding="utf-8")
print("Issue log, WebP merchant/product uploads and visual foundation patched.")
