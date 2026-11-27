from pathlib import Path
p=Path('src/App.tsx'); s=p.read_text()
def once(old,new,label):
    global s
    if s.count(old)!=1: raise SystemExit(f'{label}: expected one anchor, got {s.count(old)}')
    s=s.replace(old,new,1)
# Extend the order model and live clinic/pharmacy state.
s=s.replace('deliveryMapUrl?:string};','deliveryMapUrl?:string;rideBacked?:boolean};',1)
s=s.replace("[doctorSearch,setDoctorSearch]=useState(''),", "[doctorSearch,setDoctorSearch]=useState(''),[doctorRows,setDoctorRows]=useState<Doctor[]>(supabase?[]:doctors),[selectedPharmacyId,setSelectedPharmacyId]=useState(''),[pharmacyQueue,setPharmacyQueue]=useState<any[]>([]),")
# Load verified doctor records only when backend is configured.
if "from('medical_providers')" not in s:
    anchor=" useEffect(()=>save('cart',cart),[cart]);"
    effect=""" useEffect(()=>{if(!supabase)return;let alive=true;(async()=>{const {data,error}=await supabase!.from('medical_providers').select('id,full_name,specialty,address,phone,working_days').eq('is_active',true).order('full_name');if(!alive)return;if(error){setDoctorRows([]);notify('تعذر تحميل دليل الأطباء: '+error.message);return;}setDoctorRows((data||[]).map((d:any)=>({id:d.id,name:d.full_name,specialty:d.specialty,address:d.address,phone:d.phone,days:d.working_days||'يرجى التواصل للتأكد من المواعيد'})));})();return()=>{alive=false}},[]);
"""
    once(anchor,effect+anchor,'doctor directory query')
start=s.find('doctors.filter(d=>'); end=s.find('.includes(doctorSearch))',start)+len('.includes(doctorSearch))')
if start>=0 and end>start: s=s[:start]+"doctorRows.filter(d=>(d.name+' '+d.specialty).includes(doctorSearch))"+s[end:]
s=s.replace('<p className="warning">الأسماء والأرقام المعروضة بيانات تجريبية وليست بيانات أطباء حقيقية. يجب التحقق منها قبل النشر.</p>', "{!supabase&&<p className=\"warning\">الأسماء والأرقام المعروضة بيانات تجريبية وليست بيانات أطباء حقيقية. يجب التحقق منها قبل النشر.</p>}{supabase&&doctorRows.length===0&&<p className=\"warning\">لا توجد بيانات أطباء موثقة منشورة حاليًا.</p>}")
# Replace local-only order fetch with combined orders + errands.
start=s.find(' const refreshOrders=async()=>'); end=s.find('\n useEffect(()=>{if(!supabase||!signedInPhone)',start)
if start<0 or end<0: raise SystemExit('refreshOrders anchor missing')
refresh=""" const refreshOrders=async()=>{if(!supabase)return;const [ordersResult,ridesResult]=await Promise.all([supabase.from('orders').select('id,merchant_id,status,payment_method,subtotal,delivery_fee,total,customer_note,created_at,delivery_area,delivery_street,delivery_landmark,delivery_latitude,delivery_longitude,delivery_map_url,customer_name,customer_phone,courier_id,merchants(name),order_items(product_id,quantity)').order('created_at',{ascending:false}).limit(100),supabase.from('errand_requests').select('id,status,pickup_address,dropoff_address,item_description,customer_phone,customer_note,delivery_fee,created_at,customer_name,customer_id,courier_id').order('created_at',{ascending:false}).limit(100)]);if(ordersResult.error){notify('تعذر تحديث الطلبات: '+ordersResult.error.message);return;}const orderRows=(ordersResult.data||[]).map((o:any)=>({id:o.id,number:String(o.id).slice(0,8),kind:'طلب متجر',storeId:o.merchant_id,storeName:o.merchants?.name||'متجر',lines:(o.order_items||[]).map((x:any)=>({productId:String(x.product_id||''),storeId:o.merchant_id,qty:x.quantity})),total:Number(o.subtotal||0),delivery:Number(o.delivery_fee||0),status:orderStatusFromDb(o.status),payment:'الدفع عند الاستلام',address:[o.delivery_area,o.delivery_street,o.delivery_landmark].filter(Boolean).join(' – '),deliveryMapUrl:o.delivery_map_url||((o.delivery_latitude!=null&&o.delivery_longitude!=null)?'https://www.google.com/maps?q='+o.delivery_latitude+','+o.delivery_longitude:undefined),createdAt:o.created_at,customer:o.customer_name||'',phone:o.customer_phone||'',notes:o.customer_note||'',courierId:o.courier_id||null}));const rideRows=(ridesResult.data||[]).map((r:any)=>({id:r.id,number:'R-'+String(r.id).slice(0,7),kind:'مشوار خاص',storeName:'ابعتلي / مشوار خاص',lines:[],total:Number(r.delivery_fee||25),delivery:0,status:orderStatusFromDb(r.status),payment:'نقدًا عند التسليم',address:'استلام: '+r.pickup_address+' | تسليم: '+r.dropoff_address,createdAt:r.created_at,customer:r.customer_name||'',phone:r.customer_phone||'',notes:[r.item_description,r.customer_note].filter(Boolean).join(' – '),pickup:r.pickup_address,dropoff:r.dropoff_address,courierId:r.courier_id||null,rideBacked:true}));setOrders([...orderRows,...rideRows].sort((a:any,b:any)=>new Date(b.createdAt).getTime()-new Date(a.createdAt).getTime()));if(ridesResult.error&&ridesResult.error.code!=='42P01')notify('تعذر تحميل المشاوير: '+ridesResult.error.message);};"""
s=s[:start]+refresh+s[end:]
# Subscribe to both order types and refresh periodically.
s=s.replace("const ch=supabase.channel('saree3-orders-live').on('postgres_changes',{event:'*',schema:'public',table:'orders'},()=>{void refreshOrders()}).subscribe();return()=>{void supabase?.removeChannel(ch)}", "const ch=supabase.channel('saree3-orders-live').on('postgres_changes',{event:'*',schema:'public',table:'orders'},()=>{void refreshOrders()}).on('postgres_changes',{event:'*',schema:'public',table:'errand_requests'},()=>{void refreshOrders()}).subscribe();const poll=window.setInterval(()=>void refreshOrders(),15000);return()=>{window.clearInterval(poll);void supabase?.removeChannel(ch)}")
# Persist private ride requests.
start=s.find(' const submitTrip='); end=s.find('\n const uploadPrescription=',start)
if start<0 or end<0: raise SystemExit('submitTrip block missing')
trip=""" const submitTrip=async()=>{if(!trip.pickup||!trip.dropoff||!trip.item||!trip.phone){notify('أكمل نقطة الاستلام والتسليم والغرض ورقم الهاتف');return;}if(!supabase||!signedInPhone){notify('سجّل الدخول أولًا لإرسال المشوار للمندوبين');setModal('login');return;}const {data:{user},error:userError}=await supabase.auth.getUser();if(userError||!user){notify('انتهت جلسة الدخول');return;}const {error}=await supabase.rpc('create_shifa_errand',{p_pickup_address:trip.pickup,p_dropoff_address:trip.dropoff,p_item_description:trip.item,p_customer_phone:trip.phone,p_customer_note:trip.notes||null});if(error){notify('تعذر إرسال المشوار: '+error.message);return;}setTrip({pickup:'',dropoff:'',item:'',phone:'',notes:''});setTab('orders');await refreshOrders();notify('تم إرسال المشوار للمندوبين المتاحين');};"""
s=s[:start]+trip+s[end:]
# Upload prescriptions to the private bucket and assign the pharmacy.
prescription_helper=""" const sendPrescription=async()=>{if(!prescription?.data){notify('اختر صورة الروشتة أولًا');return;}if(!supabase||!signedInPhone){notify('سجّل الدخول أولًا لإرسال الروشتة بأمان');setModal('login');return;}if(!isUuid(selectedPharmacyId)){notify('اختر صيدلية متصلة بالخادم');return;}const {data:{user},error:userError}=await supabase.auth.getUser();if(error||!user){notify('انتهت جلسة الدخول');return;}try{const response=await fetch(prescription.data);const blob=await response.blob();const ext=blob.type==='application/pdf'?'pdf':blob.type==='image/png'?'png':'jpg';const path=user.id+'/'+crypto.randomUUID()+'.'+ext;const {error:uploadError}=await supabase.storage.from('prescriptions').upload(path,blob,{contentType:blob.type||'image/jpeg',upsert:false});if(uploadError)throw uploadError;const {error:rowError}=await supabase.from('pharmacy_prescriptions').insert({customer_id:user.id,pharmacy_merchant_id:selectedPharmacyId,storage_path:path,status:'submitted'});if(rowError){await supabase.storage.from('prescriptions').remove([path]);throw rowError;}setPrescription(null);notify('تم إرسال الروشتة إلى الصيدلية في ملف خاص لمراجعة صيدلي مرخص.');}catch(e){notify('تعذر إرسال الروشتة: '+(e instanceof Error?e.message:'خطأ غير معروف'));}};
"""
if 'const sendPrescription=async' not in s: s=s.replace(' const renderOrders=',prescription_helper+' const renderOrders=',1)
s=s.replace('<p className="warning">الروشتة تُرسل إلى صيدلي مرخص لمراجعتها. لا يقوم التطبيق بتشخيص الحالة أو اقتراح دواء أو جرعة أو بديل تلقائيًا.</p><button className="primary full" disabled={!prescription} onClick={()=>{notify(\'حُفظت الروشتة على هذا الجهاز فقط. ربط الخادم مطلوب لإرسالها بأمان.\');}}>إرسال للصيدلية للمراجعة</button>', '<label>الصيدلية<select value={selectedPharmacyId} onChange={e=>setSelectedPharmacyId(e.target.value)}><option value="">اختر الصيدلية</option>{stores.filter(s=>s.type===\'pharmacy\'&&isUuid(s.id)).map(s=><option key={s.id} value={s.id}>{s.name}</option>)}</select></label><p className="warning">تُرفع الروشتة إلى مساحة خاصة ولا يطّلع عليها إلا صاحبها والصيدلية المعينة والصيدلي المرخص المعتمد. لا يوجد تشخيص أو اقتراح دواء أو بديل تلقائي.</p><button className="primary full" disabled={!prescription} onClick={()=>void sendPrescription()}>إرسال للصيدلية للمراجعة</button>')
# Restrict prescription queue to assigned merchant; policy checks pharmacist_verified.
queue=""" useEffect(()=>{if(!supabase||role!=='merchant'||!merchantIds.length){setPharmacyQueue([]);return;}let alive=true;const pharmacyId=stores.find(x=>x.type==='pharmacy'&&merchantIds.includes(x.id))?.id;if(!pharmacyId){setPharmacyQueue([]);return;}const load=async()=>{const {data,error}=await supabase!.from('pharmacy_prescriptions').select('id,storage_path,status,created_at,pharmacist_note').eq('pharmacy_merchant_id',pharmacyId).in('status',['submitted','under_review']).order('created_at',{ascending:false});if(!alive)return;if(error){notify('تعذر تحميل الروشتات: '+error.message);return;}setPharmacyQueue(data||[])};void load();const ch=supabase.channel('saree3-pharmacy-queue').on('postgres_changes',{event:'*',schema:'public',table:'pharmacy_prescriptions'},()=>void load()).subscribe();return()=>{alive=false;void supabase!.removeChannel(ch)}},[role,merchantIds,stores]);
 const reviewPrescription=async(id:string,status:'under_review'|'approved'|'rejected')=>{if(!supabase)return;const {error}=await supabase.from('pharmacy_prescriptions').update({status,reviewed_by:currentUserId,reviewed_at:new Date().toISOString()}).eq('id',id);if(error){notify(error.message);return;}notify('تم تحديث حالة الروشتة');};
 const openPrescriptionFile=async(path:string)=>{if(!supabase)return;const {data,error}=await supabase.storage.from('prescriptions').createSignedUrl(path,300);if(error||!data?.signedUrl){notify(error?.message||'تعذر فتح الروشتة');return;}window.open(data.signedUrl,'_blank','noopener,noreferrer');};
"""
if 'saree3-pharmacy-queue' not in s: s=s.replace(' const renderOrders=',queue+' const renderOrders=',1)
# Pharmacy profile queue UI.
old="{role==='merchant'&&tab==='profile'&&<section className=\"panel\"><h2>بيانات المتجر</h2><p>اسم تجريبي: صيدلية الشفاء – ملوي</p><p className=\"warning\">يجب رفع الترخيص والتحقق من الصيدلي المسؤول قبل استقبال أي وصفات أو طلبات أدوية.</p></section>}"
new="{role==='merchant'&&tab==='profile'&&<section className=\"panel\"><h2>روشتات الصيدلية</h2><p>الوارد: {pharmacyQueue.length}</p>{pharmacyQueue.map((r:any)=><article className=\"order-card\" key={r.id}><b>روشتة #{String(r.id).slice(0,8)}</b><p>{r.status==='submitted'?'جديدة':'قيد المراجعة'} · {new Date(r.created_at).toLocaleString('ar-EG')}</p><button className=\"outline\" onClick={()=>void openPrescriptionFile(r.storage_path)}>فتح الملف الخاص</button>{r.status==='submitted'&&<button className=\"outline\" onClick={()=>void reviewPrescription(r.id,'under_review')}>بدء المراجعة</button>}{r.status==='under_review'&&<button className=\"primary small\" onClick={()=>void reviewPrescription(r.id,'approved')}>اعتماد بعد المراجعة</button>}<button className=\"outline\" onClick={()=>void reviewPrescription(r.id,'rejected')}>رفض</button></article>)}<p className=\"warning\">مراجعة الروشتات متاحة فقط لصيدلية تم التحقق من ترخيصها إداريًا.</p></section>}"
s=s.replace(old,new)
# Server-side errand transitions and claims.
s=s.replace("const {error}=await supabase.rpc('transition_shifa_order',{p_order_id:o.id,p_next_status:orderStatusToDb(next)});", "const {error}=o.rideBacked?await supabase.rpc('transition_shifa_errand',{p_errand_id:o.id,p_next_status:orderStatusToDb(next)}):await supabase.rpc('transition_shifa_order',{p_order_id:o.id,p_next_status:orderStatusToDb(next)});")
s=s.replace("const {error}=await supabase.rpc('claim_shifa_order',{p_order_id:o.id});", "const {error}=o.rideBacked?await supabase.rpc('claim_shifa_errand',{p_errand_id:o.id}):await supabase.rpc('claim_shifa_order',{p_order_id:o.id});")
# Include pending errands in courier view and add their claim button.
s=s.replace("filter==='driver'?((o.status==='جاهز للاستلام'&&!o.courierId)||o.courierId===currentUserId)", "filter==='driver'?((o.status==='جاهز للاستلام'&&!o.courierId)||(o.rideBacked&&o.status==='جديد'&&!o.courierId)||o.courierId===currentUserId)")
s=s.replace("{filter==='driver'&&o.status==='جاهز للاستلام'&&!o.courierId&&<button className=\"outline\" onClick={()=>void acceptServerDelivery(o)}>قبول المهمة</button>}", "{filter==='driver'&&((o.status==='جاهز للاستلام'&&!o.rideBacked)||(o.rideBacked&&o.status==='جديد'))&&!o.courierId&&<button className=\"outline\" onClick={()=>void acceptServerDelivery(o)}>قبول المهمة</button>}")
# Auth refresh, driver availability and role locking.
s=s.replace("await verifyPhoneOtp(authPhone,authCode);setModal('');", "await verifyPhoneOtp(authPhone,authCode);window.dispatchEvent(new Event('saree3:auth-changed'));setModal('');")
if 'const toggleDriverAvailability=async' not in s:
    helper=" const toggleDriverAvailability=async()=>{if(!supabase||!driverVerified){notify('حساب المندوب غير موثق بعد');return;}if(!currentUserId)return;const {data,error}=await supabase.from('courier_profiles').update({is_available:!driverOnline}).eq('user_id',currentUserId).select('user_id').maybeSingle();if(error||!data){notify(error?.message||'تعذر تحديث حالة التوفر');return;}setDriverOnline(v=>!v);};\n"
    s=s.replace(' const navItems=',helper+' const navItems=',1)
s=s.replace("onClick={()=>setDriverOnline(!driverOnline)}", "disabled={!!supabase&&!driverVerified} onClick={()=>void toggleDriverAvailability()}")
s=s.replace('<select value={role} onChange={e=>chooseRole(e.target.value as Role)}>', '<select value={role} disabled={!!signedInPhone} onChange={e=>chooseRole(e.target.value as Role)}>')
s=s.replace("const chooseRole=(r:Role)=>{setRole(r);", "const chooseRole=(r:Role)=>{if(signedInPhone&&supabase){notify('نوع الحساب يحدده حسابك المعتمد لدى الإدارة');return;}setRole(r);")
p.write_text(s)
print('Operational features wired to Supabase.')

test_path=Path('tests/source-smoke.test.cjs')
if test_path.exists():
    test_content=test_path.read_text()
    if 'errands, private prescriptions and verified clinic directory' not in test_content:
        test_content += """
test('errands, private prescriptions and verified clinic directory', () => {
  const app = fs.readFileSync(path.join(root, 'src/App.tsx'), 'utf8');
  const location = fs.readFileSync(path.join(root, 'src/LocationSystem.tsx'), 'utf8');
  const errandMigration = fs.readFileSync(path.join(root, 'supabase/migrations/202611270008_errand_workflow_and_pharmacist_review.sql'), 'utf8');
  const directoryMigration = fs.readFileSync(path.join(root, 'supabase/migrations/202611270011_medical_directory_and_prescription_privacy.sql'), 'utf8');
  assert.ok(app.includes("rpc('create_shifa_errand'"));
  assert.ok(app.includes("rpc('claim_shifa_errand'"));
  assert.ok(app.includes("rpc('transition_shifa_errand'"));
  assert.ok(app.includes("storage.from('prescriptions').upload"));
  assert.ok(app.includes("from('medical_providers')"));
  assert.ok(location.includes('saree3:auth-changed'));
  assert.ok(errandMigration.includes('claim_shifa_errand'));
  assert.ok(directoryMigration.includes('medical_providers'));
});
"""
        test_path.write_text(test_content)
