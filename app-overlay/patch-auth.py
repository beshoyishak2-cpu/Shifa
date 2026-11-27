from pathlib import Path
p=Path('src/lib/backend.ts')
s=p.read_text()
start=s.index('export async function requestPhoneOtp')
end=s.index('export async function listActiveMerchants')
new='''function normalizeEgyptianPhone(phone: string) {
  const value = phone.replace(/[\\s()-]/g, '');
  if (value.startsWith('+')) return value;
  if (value.startsWith('0020')) return `+${value.slice(2)}`;
  if (value.startsWith('20')) return `+${value}`;
  if (value.startsWith('0')) return `+2${value}`;
  return value;
}

// Internal, non-deliverable email identity derived from the phone number.
function phoneLoginEmail(phone: string) {
  const normalized = normalizeEgyptianPhone(phone);
  const digits = normalized.replace(/\\D/g, '');
  if (!/^201[0125][0-9]{8}$/.test(digits)) {
    throw new Error('اكتب رقم موبايل مصري صحيح');
  }
  return `${digits}@users.example.com`;
}

export async function registerWithPhone(phone: string, password: string, fullName: string) {
  if (!supabase || !backendReady) throw new Error('خدمة التسجيل غير متاحة حاليًا');
  const normalizedPhone = normalizeEgyptianPhone(phone);
  const { data, error } = await supabase.auth.signUp({
    email: phoneLoginEmail(phone),
    password,
    options: { data: { full_name: fullName.trim(), phone: normalizedPhone } }
  });
  if (error) throw error;
  return data;
}

export async function loginWithPhone(phone: string, password: string) {
  if (!supabase || !backendReady) throw new Error('خدمة تسجيل الدخول غير متاحة حاليًا');
  const { data, error } = await supabase.auth.signInWithPassword({
    email: phoneLoginEmail(phone),
    password
  });
  if (error) throw error;
  return data;
}
'''
if 'requestPhoneOtp' not in s: raise SystemExit('OTP backend functions not found')
p.write_text(s[:start]+new+s[end:])

p=Path('src/App.tsx')
s=p.read_text()
s=s.replace("import { requestPhoneOtp, verifyPhoneOtp } from './lib/backend';", "import { registerWithPhone, loginWithPhone } from './lib/backend';")
s=s.replace("[authPhone,setAuthPhone]=useState(''),[authCode,setAuthCode]=useState(''),[otpSent,setOtpSent]=useState(false),[signedInPhone,setSignedInPhone]=useState<string|null>(null);", "[authPhone,setAuthPhone]=useState(''),[authPassword,setAuthPassword]=useState(''),[authName,setAuthName]=useState(''),[authMode,setAuthMode]=useState<'login'|'register'>('login'),[signedInPhone,setSignedInPhone]=useState<string|null>(null);")

# Add password-auth hooks beside the existing phone-auth hooks.
# The source archive may use a different root component name.
if 'const [authPassword,setAuthPassword]' not in s:
    lines = s.splitlines(keepends=True)
    anchor = next((i for i, line in enumerate(lines)
                   if 'authPhone' in line and 'useState' in line), None)
    if anchor is None:
        raise SystemExit('Could not locate existing authPhone useState declaration')
    state = (
        "\\n  const [authPassword,setAuthPassword]=useState('');"
        "\\n  const [showAuthPassword,setShowAuthPassword]=useState(false);"
        "\\n  const [authName,setAuthName]=useState('');"
        "\\n  const [authMode,setAuthMode]=useState<'login'|'register'>('login');\\n"
    )
    lines.insert(anchor + 1, state)
    s = ''.join(lines)

old=""" const sendOtp=async()=>{try{await requestPhoneOtp(authPhone);setOtpSent(true);notify('تم إرسال رمز التحقق إلى هاتفك');}catch(e){notify(e instanceof Error?e.message:'تعذر إرسال رمز التحقق');}};
 const confirmOtp=async()=>{try{await verifyPhoneOtp(authPhone,authCode);window.dispatchEvent(new Event('saree3:auth-changed'));setModal('');notify('تم تسجيل الدخول بنجاح');}catch(e){notify(e instanceof Error?e.message:'رمز التحقق غير صحيح');}};"""
new=""" const submitPhoneAuth=async()=>{
  const phone=authPhone.replace(/[\\s()-]/g,'');
  if(!/^01[0125][0-9]{8}$/.test(phone) && !/^\\+?20?1[0125][0-9]{8}$/.test(phone)){notify('اكتب رقم موبايل مصري صحيح');return;}
  if(authPassword.length<6){notify('كلمة المرور يجب ألا تقل عن 6 أحرف أو أرقام');return;}
  try{
   if(authMode==='register'){
    if(!authName.trim()){notify('اكتب اسمك');return;}
    const data=await registerWithPhone(authPhone,authPassword,authName);
    setCustomer((v:any)=>({...v,name:authName.trim(),phone:authPhone}));
    if(data.session){setModal('');notify('تم إنشاء حسابك وتسجيل الدخول بنجاح');}
    else notify('تم إنشاء الحساب. تأكد من إعداد تأكيد الهاتف في Supabase للسماح بالدخول بدون OTP.');
   }else{
    await loginWithPhone(authPhone,authPassword);
    setCustomer((v:any)=>({...v,phone:authPhone}));setModal('');notify('تم تسجيل الدخول بنجاح');
   }
  }catch(e){notify(e instanceof Error?e.message:'تعذر إتمام العملية. راجع رقم الهاتف وكلمة المرور.');}
 };"""
if old not in s: raise SystemExit('OTP handlers block not found')
s=s.replace(old,new)
old=""" {modal==='login'&&<div className="overlay" onClick={()=>setModal('')}><div className="dialog" onClick={e=>e.stopPropagation()}><button className="close" onClick={()=>setModal('')}><X/></button><h2>تسجيل الدخول برقم الهاتف</h2><p className="muted">سيصلك رمز تحقق SMS من مشروع سريع المرتبط.</p><label>رقم الهاتف<input inputMode="tel" value={authPhone} onChange={e=>setAuthPhone(e.target.value)} placeholder="+201xxxxxxxxx"/></label>{otpSent&&<label>رمز التحقق<input inputMode="numeric" value={authCode} onChange={e=>setAuthCode(e.target.value)} placeholder="123456"/></label>}<button className="primary full" onClick={otpSent?confirmOtp:sendOtp}>{otpSent?'تأكيد الرمز':'إرسال رمز التحقق'}</button></div></div>}"""
new=""" {modal==='login'&&<div className="overlay" onClick={()=>setModal('')}><div className="dialog" onClick={e=>e.stopPropagation()}><button className="close" onClick={()=>setModal('')}><X/></button><h2>{authMode==='register'?'إنشاء حساب جديد':'تسجيل الدخول'}</h2><p className="muted">استخدم رقم موبايلك وكلمة المرور. لا نستخدم رسائل SMS أو OTP.</p>{authMode==='register'&&<label>الاسم بالكامل<input value={authName} onChange={e=>setAuthName(e.target.value)} placeholder="اسمك"/></label>}<label>رقم الهاتف<input inputMode="tel" value={authPhone} onChange={e=>setAuthPhone(e.target.value)} placeholder="010xxxxxxxx"/></label><label>كلمة المرور<div style={{display:'flex',gap:8,alignItems:'center'}}><input style={{flex:1}} type={showAuthPassword?'text':'password'} autoComplete={authMode==='register'?'new-password':'current-password'} value={authPassword} onChange={e=>setAuthPassword(e.target.value)} placeholder="6 أحرف أو أرقام على الأقل"/><button type="button" className="outline" onClick={()=>setShowAuthPassword(v=>!v)}>{showAuthPassword?'إخفاء':'إظهار'}</button></div></label><button className="primary full" onClick={submitPhoneAuth}>{authMode==='register'?'إنشاء الحساب':'دخول'}</button><button className="outline full" onClick={()=>setAuthMode(authMode==='register'?'login':'register')}>{authMode==='register'?'لديك حساب؟ سجل الدخول':'مستخدم جديد؟ أنشئ حسابًا'}</button></div></div>}"""
if old not in s: raise SystemExit('OTP modal block not found')
s=s.replace(old,new)
p.write_text(s)
