from pathlib import Path
p=Path('src/App.tsx');s=p.read_text()
s=s.replace('type StoreItem = {id:string;', 'type StoreItem = {image?:string;id:string;',1)
s=s.replace("[doctorSearch,setDoctorSearch]=useState(''),", "[doctorSearch,setDoctorSearch]=useState(''),[doctorRows,setDoctorRows]=useState<Doctor[]>(supabase?[]:doctors),",1)
if "from('medical_providers')" not in s:
    anchor=" const count=cart.reduce"
    effect=""" useEffect(()=>{if(!supabase)return;let alive=true;(async()=>{const {data,error}=await supabase!.from('medical_providers').select('id,full_name,specialty,address,phone,working_days').eq('is_active',true).order('full_name');if(!alive)return;if(error){setDoctorRows([]);notify('تعذر تحميل دليل الأطباء: '+error.message);return;}setDoctorRows((data||[]).map((d:any)=>({id:d.id,name:d.full_name,specialty:d.specialty,address:d.address,phone:d.phone,days:d.working_days||'يرجى التواصل للتأكد من المواعيد'})));})();return()=>{alive=false}},[]);
"""
    if anchor not in s: raise SystemExit('doctor loader anchor missing')
    s=s.replace(anchor,effect+anchor,1)
s=s.replace('doctors.length===0','doctorRows.length===0')
start=s.find('doctors.filter(d=>'); end=s.find('.includes(doctorSearch))',start)+len('.includes(doctorSearch))')
if start>=0 and end>start: s=s[:start]+"doctorRows.filter(d=>(d.name+' '+d.specialty).includes(doctorSearch))"+s[end:]
needle='<h1>دليل الأطباء والعيادات</h1><div className="search">'
notice='<h1>دليل الأطباء والعيادات</h1><p className="muted">هذا الدليل لتسهيل الوصول إلى مقدمي الخدمة فقط، ولا يقدم التطبيق تشخيصًا أو علاجًا طبيًا. استشر طبيبًا مؤهلًا للحصول على المشورة الطبية.</p><div className="search">'
if needle in s:
    s=s.replace(needle,notice,1)
elif notice not in s:
    raise SystemExit('doctor directory disclaimer insertion point missing')
s=s.replace('[driverOnline,setDriverOnline]=useState(true)', '[driverOnline,setDriverOnline]=useState(false)')
s=s.replace('setDriverVerified(false);setCurrentUserId(null);return;', 'setDriverVerified(false);setDriverOnline(false);setCurrentUserId(null);return;')
helper=" const toggleDriverAvailability=async()=>{if(supabase){if(!driverVerified||!currentUserId){notify('حساب المندوب غير موثق بعد');return;}const {data,error}=await supabase.from('courier_profiles').update({is_available:!driverOnline}).eq('user_id',currentUserId).select('user_id').maybeSingle();if(error||!data){notify(error?.message||'تعذر تحديث حالة التوفر');return;}}setDriverOnline(v=>!v);};\n"
if 'const toggleDriverAvailability=async' not in s:
    s=s.replace(' const navItems:',helper+' const navItems:',1)
s=s.replace('onClick={()=>setDriverOnline(!driverOnline)}', 'disabled={!!supabase&&!driverVerified} onClick={()=>void toggleDriverAvailability()}')
s=s.replace("await verifyPhoneOtp(authPhone,authCode);setModal('');", "await verifyPhoneOtp(authPhone,authCode);window.dispatchEvent(new Event('saree3:auth-changed'));setModal('');")
s=s.replace("const chooseRole=(r:Role)=>{setRole(r);", "const chooseRole=(r:Role)=>{if(signedInPhone&&supabase){notify('نوع الحساب يحدده حسابك المعتمد لدى الإدارة');return;}setRole(r);")
p.write_text(s)
print('Applied final type, doctor directory, OTP address refresh and courier availability fixes.')

test_path=Path('tests/source-smoke.test.cjs')
if test_path.exists():
    t=test_path.read_text()
    if 'health directory includes a medical advice disclaimer' not in t:
        t += """
test('health directory includes a medical advice disclaimer', () => {
  assert.ok(app().includes('استشر طبيبًا مؤهلًا للحصول على المشورة الطبية'));
});
"""
    if 'clinic directory, courier availability and address refresh' not in t:
        t += """
test('clinic directory, courier availability and address refresh', () => {
  const app = fs.readFileSync(path.join(root, 'src/App.tsx'), 'utf8');
  const location = fs.readFileSync(path.join(root, 'src/LocationSystem.tsx'), 'utf8');
  assert.ok(app.includes("from('medical_providers')"));
  assert.ok(app.includes("courier_profiles').update({is_available"));
  assert.ok(app.includes("new Event('saree3:auth-changed')"));
  assert.ok(location.includes('saree3:auth-changed'));
  assert.ok(app.includes('image?:string'));
});
"""
        test_path.write_text(t)
