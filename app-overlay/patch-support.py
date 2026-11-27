from pathlib import Path

p = Path("src/App.tsx")
s = p.read_text()

s = s.replace("Moon, Sun } from 'lucide-react';", "Moon, Sun, MessageCircle } from 'lucide-react';", 1)
state_anchor = "[doctorSearch,setDoctorSearch]=useState(''),[doctorRows,setDoctorRows]=useState<Doctor[]>(supabase?[]:doctors),"
state_new = state_anchor + "[supportTickets,setSupportTickets]=useState<any[]>([]),[supportSubject,setSupportSubject]=useState(''),[supportMessage,setSupportMessage]=useState(''),"
if state_anchor in s:
    s = s.replace(state_anchor, state_new, 1)
elif "[supportTickets,setSupportTickets]" not in s:
    raise SystemExit("support state anchor missing")

effect_anchor = " const count=cart.reduce"
effect = """ useEffect(()=>{if(!supabase||!currentUserId||role!=='customer'){setSupportTickets([]);return;}let live=true;supabase.from('support_tickets').select('id,subject,message,status,created_at').eq('customer_id',currentUserId).order('created_at',{ascending:false}).limit(30).then(({data,error}:any)=>{if(!live)return;if(error){notify('تعذر تحميل الشكاوى: '+error.message);return;}setSupportTickets(data||[])});return()=>{live=false}},[currentUserId,role,signedInPhone]);
"""
if "from('support_tickets').select" not in s:
    if effect_anchor not in s: raise SystemExit("support loader anchor missing")
    s = s.replace(effect_anchor, effect + effect_anchor, 1)

fn_anchor = " const locate=async()=>"
fn = """ const submitSupportTicket=async()=>{if(!supportSubject.trim()||supportMessage.trim().length<5){notify('اكتب موضوع الشكوى وتفاصيل لا تقل عن 5 أحرف');return;}if(!supabase||!currentUserId||!signedInPhone){notify('سجّل الدخول أولًا لإرسال الشكوى');setModal('login');return;}const {data,error}=await supabase.from('support_tickets').insert({customer_id:currentUserId,subject:supportSubject.trim(),message:supportMessage.trim()}).select('id,subject,message,status,created_at').single();if(error){notify('تعذر إرسال الشكوى: '+error.message);return;}setSupportTickets(v=>[data,...v]);setSupportSubject('');setSupportMessage('');notify('تم إرسال الشكوى إلى فريق الدعم');};
"""
if "const submitSupportTicket=async" not in s:
    if fn_anchor not in s: raise SystemExit("support submit anchor missing")
    s = s.replace(fn_anchor, fn + fn_anchor, 1)

nav_anchor = "['profile','عناويني',MapPin]]:role==='merchant'"
nav_new = "['support','الدعم والشكاوى',MessageCircle],['profile','عناويني',MapPin]]:role==='merchant'"
if nav_anchor in s:
    s = s.replace(nav_anchor, nav_new, 1)
elif nav_new not in s:
    raise SystemExit("customer navigation anchor missing")

page_anchor = " {role==='customer'&&tab==='profile'&&"
page = """ {role==='customer'&&tab==='support'&&<><h1>الدعم والشكاوى</h1><section className="panel form-panel"><p className="muted">اكتب مشكلتك وسيراجعها فريق سريع. لا ترسل بيانات بطاقتك أو كلمات المرور.</p><a className="outline full" href="https://beshoyishak2-cpu.github.io/Shifa/delete-account.html">طلب حذف الحساب والبيانات</a><p><a href="https://beshoyishak2-cpu.github.io/Shifa/privacy-policy.html">سياسة الخصوصية</a></p><label>موضوع الشكوى<input value={supportSubject} onChange={e=>setSupportSubject(e.target.value)} placeholder="مثال: مشكلة في طلب أو توصيل"/></label><label>التفاصيل<textarea value={supportMessage} onChange={e=>setSupportMessage(e.target.value)} placeholder="اشرح المشكلة ورقم الطلب إن وجد"/></label><button className="primary full" onClick={()=>void submitSupportTicket()}>إرسال الشكوى</button></section><section className="panel"><h2>شكاواي السابقة</h2>{supportTickets.length===0?<Empty title="لا توجد شكاوى" hint="عند إرسال شكوى ستظهر حالتها هنا."/>:supportTickets.map(t=><article className="order-card" key={t.id}><b>{t.subject}</b><p>{t.message}</p><span className="status">{({open:'مفتوحة',in_progress:'قيد المتابعة',resolved:'تم الحل',closed:'مغلقة'} as any)[t.status]||'مفتوحة'}</span><small>{new Date(t.created_at).toLocaleString('ar-EG')}</small></article>)}</section></>}
"""
if page_anchor in s:
    s = s.replace(page_anchor, page + page_anchor, 1)
elif "tab==='support'" not in s:
    raise SystemExit("support page anchor missing")

p.write_text(s)

panel = Path("src/SareeOperationsPanel.tsx")
if not panel.exists():
    raise SystemExit("operations panel file missing")
q = panel.read_text()
q = q.replace("  const [applications, setApplications] = useState<Row[]>([]);", "  const [applications, setApplications] = useState<Row[]>([]);\n  const [supportTickets, setSupportTickets] = useState<Row[]>([]);", 1)
q = q.replace("const [a, p, s, o, mine, w, d, driver, settings, fees, customers] = await Promise.all([", "const [a, p, s, o, mine, w, d, driver, settings, fees, customers, tickets] = await Promise.all([", 1)
needle = "      currentRole === 'admin' ? db.from('profiles').select('id,full_name,phone').eq('role','customer').order('full_name') : Promise.resolve({ data: [] as Row[] })"
replacement = needle + ",\n      currentRole === 'admin' ? db.from('support_tickets').select('id,customer_id,subject,message,status,created_at,profiles(full_name,phone)').order('created_at', { ascending: false }).limit(50) : Promise.resolve({ data: [] as Row[] })"
if needle in q:
    q = q.replace(needle, replacement, 1)
elif "from('support_tickets').select" not in q:
    raise SystemExit("operations support query anchor missing")
q = q.replace("setWallet(w.data); setDriverAccount(d.data);", "setWallet(w.data); setSupportTickets(tickets.data || []); setDriverAccount(d.data);", 1)
q = q.replace("['applications','receipts','settlements','settings'].map(t => btn", "['applications','receipts','settlements','support','settings'].map(t => btn", 1)
q = q.replace("settlements:'التوريد',settings:'الإعدادات'", "settlements:'التوريد',support:'الشكاوى',settings:'الإعدادات'", 1)
support_anchor = "        {role === 'admin' && tab === 'settings' && <div style={styles.card}>"
support_ui = """        {role === 'admin' && tab === 'support' && <><b>شكاوى العملاء ({supportTickets.length})</b>{supportTickets.length===0 ? <div style={styles.card}>لا توجد شكاوى مسجلة.</div> : supportTickets.map(t => <article style={styles.card} key={t.id}><b>{t.subject}</b><span>{t.profiles?.full_name || 'عميل'} · {t.profiles?.phone || t.customer_id}</span><span>{t.message}</span><span style={styles.muted}>{({open:'مفتوحة',in_progress:'قيد المتابعة',resolved:'تم الحل',closed:'مغلقة'} as any)[t.status] || 'مفتوحة'} · {new Date(t.created_at).toLocaleString('ar-EG')}</span>{t.profiles?.phone && <a href={'tel:'+t.profiles.phone}>الاتصال بالعميل</a>}</article>)}</>}
"""
if support_anchor in q:
    q = q.replace(support_anchor, support_ui + support_anchor, 1)
elif "tab === 'support'" not in q:
    raise SystemExit("operations support UI anchor missing")
panel.write_text(q)

test_path = Path("tests/source-smoke.test.cjs")
if test_path.exists():
    t = test_path.read_text()
    if "in-app account deletion request is discoverable" not in t:
        t += """
test('in-app account deletion request is discoverable', () => {
  assert.ok(app().includes('طلب حذف الحساب والبيانات'));
});
"""
    if "customer support tickets are submitted and listed" not in t:
        t += """
test('customer support tickets are submitted and listed', () => {
  assert.ok(app().includes(\"from('support_tickets').insert\"));
  assert.ok(app().includes(\"tab==='support'\"));
});
"""
        test_path.write_text(t)

print("Added customer support tickets and an admin support inbox.")
