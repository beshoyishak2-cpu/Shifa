import React, { useEffect, useState } from 'react';
import { createRoot } from 'react-dom/client';
import { createClient, type SupabaseClient, type Session } from '@supabase/supabase-js';

const URL = import.meta.env.VITE_SUPABASE_URL as string | undefined;
const KEY = (import.meta.env.VITE_SUPABASE_PUBLISHABLE_KEY || import.meta.env.VITE_SUPABASE_ANON_KEY) as string | undefined;
const db: SupabaseClient | null = URL && KEY ? createClient(URL, KEY) : null;
type Role = 'customer' | 'merchant' | 'driver' | 'admin';
type Row = Record<string, any>;

async function compressedImage(file: File): Promise<File> {
  if (!file.type.startsWith('image/')) return file;
  try {
    const bitmap = await createImageBitmap(file);
    const scale = Math.min(1, 1600 / Math.max(bitmap.width, bitmap.height));
    const canvas = document.createElement('canvas');
    canvas.width = Math.round(bitmap.width * scale); canvas.height = Math.round(bitmap.height * scale);
    const ctx = canvas.getContext('2d'); if (!ctx) return file;
    ctx.drawImage(bitmap, 0, 0, canvas.width, canvas.height); bitmap.close();
    const blob = await new Promise<Blob | null>(resolve => canvas.toBlob(resolve, 'image/jpeg', .78));
    return blob ? new File([blob], file.name.replace(/\.[^.]+$/, '.jpg'), { type: 'image/jpeg' }) : file;
  } catch { return file; }
}
async function upload(bucket: string, userId: string, file: File) {
  if (!db) throw new Error('الاتصال غير متاح');
  const safeName = file.name.replace(/[^\p{L}\p{N}._-]/gu, '_');
  const path = userId + '/' + Date.now() + '-' + crypto.randomUUID() + '-' + safeName;
  const prepared = await compressedImage(file);
  const { error } = await db.storage.from(bucket).upload(path, prepared, { upsert: false, contentType: prepared.type || undefined });
  if (error) throw error;
  return path;
}
const money = (v: any) => Number(v || 0).toLocaleString('ar-EG', { maximumFractionDigits: 2 }) + ' ج.م';

function SareeOperationsPanel() {
  const [session, setSession] = useState<Session | null>(null);
  const [role, setRole] = useState<Role | null>(null);
  const [open, setOpen] = useState(false);
  const [tab, setTab] = useState('main');
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState('');
  const [applications, setApplications] = useState<Row[]>([]);
  const [receipts, setReceipts] = useState<Row[]>([]);
  const [settlements, setSettlements] = useState<Row[]>([]);
  const [orders, setOrders] = useState<Row[]>([]);
  const [myOrders, setMyOrders] = useState<Row[]>([]);
  const [wallet, setWallet] = useState<Row | null>(null);
  const [walletAmounts, setWalletAmounts] = useState<Record<string, string>>({});
  const [adminCustomers, setAdminCustomers] = useState<Row[]>([]);
  const [walletCredit, setWalletCredit] = useState({ customer_id: '', amount: '', note: '' });
  const [driverAccount, setDriverAccount] = useState<Row | null>(null);
  const [driverProfile, setDriverProfile] = useState<Row | null>(null);
  const [appSettings, setAppSettings] = useState<Row>({ mobile_wallet_enabled: true, instapay_enabled: true, transfer_phone: '01221236118' });
  const [commission, setCommission] = useState<Row>({ commission_mode: 'percent', commission_value: 0, daily_due_time: '22:00:00', max_debt: 500, auto_lock_enabled: true, transfer_phone: '01221236118' });
  const [appForm, setAppForm] = useState({ application_type: 'merchant', business_type: 'restaurant', display_name: '', phone: '', area_name: 'ملوي', address: '', vehicle_type: 'motorcycle' });
  const [docs, setDocs] = useState<FileList | null>(null);
  const [paymentMethod, setPaymentMethod] = useState('mobile_wallet');

  const uid = session?.user.id;
  const say = (s: string) => setMessage(s);
  const run = async (fn: () => Promise<void>) => { setBusy(true); setMessage(''); try { await fn(); } catch (e) { say((e as Error).message || 'حدث خطأ'); } finally { setBusy(false); } };

  async function load() {
    if (!db || !uid) return;
    const { data: profile } = await db.from('profiles').select('role').eq('id', uid).maybeSingle();
    const currentRole = (profile?.role || 'customer') as Role; setRole(currentRole);
    const [a, p, s, o, mine, w, d, driver, settings, fees, customers] = await Promise.all([
      currentRole === 'admin' ? db.from('partner_applications').select('*').eq('status', 'pending').order('created_at', { ascending: false }) : Promise.resolve({ data: [] as Row[] }),
      currentRole === 'admin' ? db.from('payment_receipts').select('*,orders(total,customer_name,customer_phone)').eq('status', 'pending').order('created_at', { ascending: false }) : Promise.resolve({ data: [] as Row[] }),
      currentRole === 'admin' ? db.from('courier_settlements').select('*').eq('status', 'pending').order('created_at', { ascending: false }) : Promise.resolve({ data: [] as Row[] }),
      currentRole === 'driver' ? db.from('orders').select('id,total,status,customer_name,customer_phone,delivery_area,delivery_street,delivery_landmark,delivery_unit_details,delivery_latitude,delivery_longitude,delivery_map_url,merchant_id').eq('status', 'ready_for_pickup').is('courier_id', null).order('created_at', { ascending: true }) : Promise.resolve({ data: [] as Row[] }),
      db.from('orders').select('id,total,status,payment_status,payment_method,created_at,customer_name,customer_phone').eq(currentRole === 'driver' ? 'courier_id' : 'customer_id', uid).in('status', currentRole === 'driver' ? ['ready_for_pickup','picked_up'] : ['pending','accepted','preparing','ready_for_pickup']).order('created_at', { ascending: false }).limit(20),
      currentRole === 'customer' ? db.from('wallet_accounts').select('*').eq('customer_id', uid).maybeSingle() : Promise.resolve({ data: null as Row | null }),
      currentRole === 'driver' ? db.from('courier_settlement_accounts').select('*').eq('courier_id', uid).maybeSingle() : Promise.resolve({ data: null as Row | null }),
      currentRole === 'driver' ? db.from('courier_profiles').select('is_available,is_verified,locked_for_settlement').eq('user_id', uid).maybeSingle() : Promise.resolve({ data: null as Row | null }),
      db.from('saree_app_settings').select('*').eq('id', true).maybeSingle(),
      currentRole === 'admin' ? db.from('saree_commission_settings').select('*').eq('id', true).maybeSingle() : Promise.resolve({ data: null as Row | null }),
      currentRole === 'admin' ? db.from('profiles').select('id,full_name,phone').eq('role','customer').order('full_name') : Promise.resolve({ data: [] as Row[] })
    ]);
    setApplications(a.data || []); setReceipts(p.data || []); setSettlements(s.data || []); setOrders(o.data || []); setMyOrders(mine.data || []);
    setWallet(w.data); setDriverAccount(d.data); setDriverProfile(driver.data); setAdminCustomers(customers.data || []); if (!walletCredit.customer_id && customers.data?.length) setWalletCredit(v => ({ ...v, customer_id: customers.data[0].id })); if (settings.data) setAppSettings(settings.data); if (fees.data) setCommission(fees.data);
  }

  useEffect(() => {
    if (!db) return;
    db.auth.getSession().then(({ data }) => setSession(data.session));
    const { data: listener } = db.auth.onAuthStateChange((_event, next) => { setSession(next); setRole(null); });
    return () => listener.subscription.unsubscribe();
  }, []);
  useEffect(() => { if (uid) void load(); else setRole(null); }, [uid]);
  useEffect(() => {
    if (!db || !uid) return;
    const channel = db.channel('saree-ops-' + uid)
      .on('postgres_changes', { event: '*', schema: 'public' }, () => { void load(); })
      .subscribe();
    return () => { void db.removeChannel(channel); };
  }, [uid, role]);

  async function submitPartner() {
    if (!db || !uid) throw new Error('سجّل الدخول أولاً');
    if (!appForm.display_name.trim() || !appForm.phone.trim()) throw new Error('أكمل الاسم ورقم الهاتف');
    if (!docs?.length) throw new Error('ارفع المستندات المطلوبة قبل إرسال الطلب');
    const paths: string[] = [];
    for (const file of Array.from(docs || [])) paths.push(await upload('partner-documents', uid, file));
    const { error } = await db.from('partner_applications').insert({ ...appForm, applicant_id: uid, document_paths: paths, status: 'pending' });
    if (error) throw error;
    say('تم إرسال طلب الانضمام للإدارة للمراجعة.');
  }
  async function reviewApplication(id: string, approve: boolean) {
    if (!db) return;
    const reason = approve ? null : (window.prompt('اكتب سبب الرفض') || '');
    if (!approve && (reason || '').trim().length < 3) throw new Error('سبب الرفض مطلوب');
    const { error } = await db.rpc('saree_admin_review_partner_application', { p_application_id: id, p_approve: approve, p_reason: reason });
    if (error) throw error; await load(); say(approve ? 'تم قبول الطلب وتفعيل الحساب.' : 'تم رفض الطلب وتسجيل السبب.');
  }
  async function reviewReceipt(id: string, approve: boolean) {
    if (!db) return;
    const note = approve ? null : (window.prompt('سبب رفض الإيصال') || '');
    const { error } = await db.rpc('saree_admin_review_payment', { p_receipt_id: id, p_approve: approve, p_note: note });
    if (error) throw error; await load(); say(approve ? 'تم تأكيد استلام المبلغ.' : 'تم رفض الإيصال.');
  }
  async function confirmSettlement(id: string) {
    if (!db) return;
    const { error } = await db.rpc('saree_admin_confirm_settlement', { p_settlement_id: id, p_note: 'تم استلام التوريد' });
    if (error) throw error; await load(); say('تم تأكيد التوريد وفتح حساب المندوب.');
  }
  async function openPrivateFile(bucket: string, path: string) {
    if (!db) return;
    const { data, error } = await db.storage.from(bucket).createSignedUrl(path, 90);
    if (error) throw error; if (data?.signedUrl) window.open(data.signedUrl, '_blank', 'noopener');
  }
  async function acceptOrder(id: string) {
    if (!db) return;
    const { error } = await db.rpc('claim_shifa_order', { p_order_id: id });
    if (error) throw error; await load(); say('تم إسناد الطلب لك.');
  }
  async function releaseOrder(id: string) {
    if (!db) return;
    const reason = window.prompt('سبب الاعتذار عن الطلب؟') || '';
    if (reason.trim().length < 2) throw new Error('سبب الاعتذار مطلوب');
    const { error } = await db.rpc('saree_driver_release_order', { p_order_id: id, p_reason: reason });
    if (error) throw error; await load(); say('تم إرجاع الطلب لطابور المناديب.');
  }
  async function moveOrder(id: string, next: string) {
    if (!db) return;
    const { error } = await db.rpc('transition_shifa_order', { p_order_id: id, p_next_status: next });
    if (error) throw error; await load(); say('تم تحديث حالة الطلب.');
  }
  async function toggleDriverAvailability() {
    if (!db || !uid || !driverProfile?.is_verified) throw new Error('حساب المندوب غير موثق');
    const next = !driverProfile.is_available;
    if (next && driverProfile.locked_for_settlement) throw new Error('حسابك مقفول لحين تأكيد التوريد');
    const { data, error } = await db.from('courier_profiles').update({ is_available: next }).eq('user_id', uid).select('is_available,is_verified,locked_for_settlement').maybeSingle();
    if (error || !data) throw error || new Error('تعذر تحديث حالة التوفر');
    setDriverProfile(data); say(next ? 'أنت متاح لاستقبال الطلبات.' : 'تم إيقاف استقبال الطلبات.'); await load();
  }
  async function applyWalletToOrder(id: string) {
    if (!db) return;
    const amount = Number(walletAmounts[id] || 0);
    if (!Number.isFinite(amount) || amount <= 0) throw new Error('اكتب مبلغًا صحيحًا من رصيد المحفظة');
    const { error } = await db.rpc('saree_apply_wallet_to_order', { p_order_id: id, p_amount: amount });
    if (error) throw error; await load(); say('تم خصم المبلغ من المحفظة وتحديث الطلب.');
  }
  async function adminCreditWallet() {
    if (!db || !walletCredit.customer_id) throw new Error('اختر العميل');
    const amount = Number(walletCredit.amount);
    if (!Number.isFinite(amount) || amount <= 0) throw new Error('اكتب مبلغًا صحيحًا');
    const { error } = await db.rpc('saree_admin_credit_wallet', { p_customer_id: walletCredit.customer_id, p_amount: amount, p_type: 'admin_credit', p_note: walletCredit.note || 'إضافة رصيد من الإدارة', p_reference_id: null, p_idempotency_key: 'admin-credit-' + crypto.randomUUID() });
    if (error) throw error; setWalletCredit(v => ({ ...v, amount: '', note: '' })); say('تم إضافة الرصيد إلى محفظة العميل.');
  }
  async function submitSettlement(file?: File) {
    if (!db || !uid || !file) throw new Error('اختر صورة إيصال التوريد');
    const path = await upload('payment-receipts', uid, file);
    const { error } = await db.rpc('saree_driver_submit_settlement', { p_receipt_path: path });
    if (error) throw error; await load(); say('تم إرسال إيصال التوريد للإدارة.');
  }
  async function submitOrderPayment(id: string, file?: File) {
    if (!db || !uid || !file) throw new Error('ارفع صورة إيصال التحويل');
    const path = await upload('payment-receipts', uid, file);
    const { error } = await db.rpc('saree_submit_order_payment', { p_order_id: id, p_method: paymentMethod, p_receipt_path: path });
    if (error) throw error; await load(); say('تم إرسال الإيصال، والطلب ينتظر مراجعة الإدارة.');
  }
  async function savePaymentSettings() {
    if (!db) return;
    const { error } = await db.rpc('saree_admin_update_payment_settings', { p_wallet_enabled: !!appSettings.mobile_wallet_enabled, p_instapay_enabled: !!appSettings.instapay_enabled, p_transfer_phone: appSettings.transfer_phone });
    if (error) throw error; say('تم حفظ إعدادات الدفع.');
  }
  async function saveCommissionSettings() {
    if (!db) return;
    const { error } = await db.rpc('saree_admin_update_commission_settings', { p_mode: commission.commission_mode, p_value: Number(commission.commission_value), p_due_time: commission.daily_due_time, p_max_debt: Number(commission.max_debt), p_auto_lock: !!commission.auto_lock_enabled, p_transfer_phone: commission.transfer_phone });
    if (error) throw error;
    const paymentUpdate = await db.rpc('saree_admin_update_payment_settings', { p_wallet_enabled: !!appSettings.mobile_wallet_enabled, p_instapay_enabled: !!appSettings.instapay_enabled, p_transfer_phone: commission.transfer_phone });
    if (paymentUpdate.error) throw paymentUpdate.error;
    setAppSettings(v => ({ ...v, transfer_phone: commission.transfer_phone })); say('تم حفظ إعدادات العمولة والتوريد ورقم التحويل.');
  }

  const styles: Record<string, React.CSSProperties> = {
    shell: { position: 'fixed', zIndex: 2147483001, left: 12, bottom: 'max(14px, env(safe-area-inset-bottom))', direction: 'rtl', fontFamily: 'inherit', color: '#183a34' },
    trigger: { border: 0, borderRadius: 999, background: '#087f68', color: '#fff', padding: '12px 17px', fontWeight: 800, boxShadow: '0 7px 24px #052f2750' },
    panel: { width: 'min(420px, calc(100vw - 24px))', maxHeight: 'min(78dvh, 720px)', overflow: 'auto', background: '#fff', border: '1px solid #d8e8e2', borderRadius: 18, boxShadow: '0 14px 48px #052f2740' },
    top: { background: '#eaf7f2', padding: '13px 15px', display: 'flex', alignItems: 'center', justifyContent: 'space-between', position: 'sticky', top: 0, zIndex: 2 },
    body: { padding: 14, display: 'grid', gap: 10 },
    card: { border: '1px solid #e0ece7', borderRadius: 12, padding: 11, display: 'grid', gap: 7, background: '#fbfefd' },
    button: { border: 0, borderRadius: 9, padding: '9px 11px', background: '#087f68', color: '#fff', fontWeight: 700 },
    muted: { color: '#668079', fontSize: 12 },
    input: { width: '100%', boxSizing: 'border-box', padding: 10, border: '1px solid #cddfd8', borderRadius: 9, background: '#fff', color: '#173b33', font: 'inherit' },
    row: { display: 'flex', flexWrap: 'wrap', gap: 7, alignItems: 'center' }
  };
  const btn = (label: string, action: () => void, secondary = false) => <button style={{ ...styles.button, background: secondary ? '#e5f1ec' : '#087f68', color: secondary ? '#185046' : '#fff' }} disabled={busy} onClick={action}>{label}</button>;
  const field = (label: string, value: any, change: (v: string) => void, type = 'text') => <label style={{ display: 'grid', gap: 4, fontSize: 12 }}>{label}<input style={styles.input} type={type} value={value ?? ''} onChange={e => change(e.target.value)} /></label>;

  if (!db || !session || !role) return null;
  return <div style={styles.shell}>
    {!open ? <button style={styles.trigger} onClick={() => { setOpen(true); void load(); }}>سريع · {role === 'admin' ? 'الإدارة' : role === 'driver' ? 'الكابتن' : 'خدمات الحساب'}</button> :
    <section style={styles.panel}>
      <header style={styles.top}><div><b>سريع | مركز العمليات</b><div style={styles.muted}>{role === 'admin' ? 'لوحة الإدارة' : role === 'driver' ? 'حساب المندوب' : 'حساب العميل'}</div></div><button style={{ ...styles.button, background: '#dcece6', color: '#185046' }} onClick={() => setOpen(false)}>إغلاق</button></header>
      <div style={styles.body}>
        <div style={styles.row}>{btn('تحديث', () => void run(load), true)}{role === 'customer' && btn('انضم كشريك', () => setTab(tab === 'partner' ? 'main' : 'partner'), true)}{role === 'admin' && ['applications','receipts','settlements','settings'].map(t => btn(({applications:'طلبات الانضمام',receipts:'إيصالات الدفع',settlements:'التوريد',settings:'الإعدادات'} as any)[t], () => setTab(t), tab !== t))}</div>
        {message && <div role="status" style={{ ...styles.card, color: '#145b45' }}>{message}</div>}
        {tab === 'partner' && role === 'customer' && <div style={styles.card}>
          <b>طلب انضمام كشريك</b>
          <select style={styles.input} value={appForm.application_type} onChange={e => setAppForm({ ...appForm, application_type: e.target.value })}><option value="merchant">تسجيل متجر</option><option value="driver">التسجيل كمندوب توصيل</option></select>
          {appForm.application_type === 'merchant' && <select style={styles.input} value={appForm.business_type} onChange={e => setAppForm({ ...appForm, business_type: e.target.value })}><option value="restaurant">مطعم</option><option value="pharmacy">صيدلية</option><option value="cafe">كافيه</option><option value="grocery">سوبر ماركت</option><option value="vegetables">خضار وفاكهة</option></select>}
          {field('الاسم / اسم النشاط', appForm.display_name, v => setAppForm({ ...appForm, display_name: v }))}
          {field('رقم الهاتف', appForm.phone, v => setAppForm({ ...appForm, phone: v }))}
          {field('المنطقة', appForm.area_name, v => setAppForm({ ...appForm, area_name: v }))}
          {appForm.application_type === 'merchant' ? field('العنوان', appForm.address, v => setAppForm({ ...appForm, address: v })) : <label style={{ display: 'grid', gap: 4, fontSize: 12 }}>نوع المركبة<select style={styles.input} value={appForm.vehicle_type} onChange={e => setAppForm({ ...appForm, vehicle_type: e.target.value })}><option value="motorcycle">موتوسيكل</option><option value="car">سيارة</option><option value="bicycle">دراجة</option></select></label>}
          <label style={{ display: 'grid', gap: 4, fontSize: 12 }}>المستندات المطلوبة<input style={styles.input} type="file" multiple accept="image/*,.pdf" onChange={e => setDocs(e.target.files)} /></label>
          {btn('إرسال طلب الانضمام', () => void run(submitPartner))}
        </div>}
        {role === 'admin' && tab === 'applications' && <><b>طلبات الانضمام الجديدة ({applications.length})</b>{applications.map(a => <article style={styles.card} key={a.id}><b>{a.display_name} · {a.application_type === 'driver' ? 'مندوب' : a.business_type}</b><span>{a.phone} · {a.area_name}</span><span style={styles.muted}>{a.address || a.vehicle_type || ''}</span><div style={styles.row}>{(a.document_paths || []).map((p: string) => btn('عرض مستند', () => void run(() => openPrivateFile('partner-documents', p)), true))}</div><div style={styles.row}>{btn('قبول وتفعيل', () => void run(() => reviewApplication(a.id, true)))}{btn('رفض', () => void run(() => reviewApplication(a.id, false)), true)}</div></article>)}</>}
        {role === 'admin' && tab === 'receipts' && <><b>إيصالات الدفع المعلقة ({receipts.length})</b>{receipts.map(r => <article style={styles.card} key={r.id}><b>{money(r.amount)} · {r.payment_method === 'instapay' ? 'إنستا باي' : 'محفظة إلكترونية'}</b><span>الطلب: {r.order_id}</span><div style={styles.row}>{btn('عرض الإيصال', () => void run(() => openPrivateFile('payment-receipts', r.storage_path)), true)}{btn('تأكيد استلام المبلغ', () => void run(() => reviewReceipt(r.id, true)))}{btn('رفض الإيصال', () => void run(() => reviewReceipt(r.id, false)), true)}</div></article>)}</>}
        {role === 'admin' && tab === 'settlements' && <><b>طلبات التوريد ({settlements.length})</b>{settlements.map(s => <article style={styles.card} key={s.id}><b>{money(s.amount)}</b><span>المندوب: {s.courier_id}</span><div style={styles.row}>{s.receipt_path && btn('عرض الإيصال', () => void run(() => openPrivateFile('payment-receipts', s.receipt_path)), true)}{btn('تأكيد استلام التوريد', () => void run(() => confirmSettlement(s.id)))}</div></article>)}</>}
        {role === 'admin' && tab === 'settings' && <div style={styles.card}>
          <b>إعدادات الدفع</b>
          <label><input type="checkbox" checked={!!appSettings.mobile_wallet_enabled} onChange={e => setAppSettings({ ...appSettings, mobile_wallet_enabled: e.target.checked })}/> تفعيل المحافظ الإلكترونية</label>
          <label><input type="checkbox" checked={!!appSettings.instapay_enabled} onChange={e => setAppSettings({ ...appSettings, instapay_enabled: e.target.checked })}/> تفعيل إنستا باي</label>
          {field('رقم التحويل', appSettings.transfer_phone, v => setAppSettings({ ...appSettings, transfer_phone: v }))}
          {btn('حفظ إعدادات الدفع', () => void run(savePaymentSettings))}
          <hr/><b>العمولة والتوريد اليومي</b>
          <select style={styles.input} value={commission.commission_mode} onChange={e => setCommission({ ...commission, commission_mode: e.target.value })}><option value="percent">نسبة مئوية</option><option value="fixed">مبلغ ثابت</option></select>
          {field('قيمة العمولة', commission.commission_value, v => setCommission({ ...commission, commission_value: v }), 'number')}
          {field('موعد التوريد اليومي', String(commission.daily_due_time).slice(0,5), v => setCommission({ ...commission, daily_due_time: v + ':00' }))}
          {field('الحد الأقصى للمديونية', commission.max_debt, v => setCommission({ ...commission, max_debt: v }), 'number')}
          {field('رقم تحويل التوريد', commission.transfer_phone, v => setCommission({ ...commission, transfer_phone: v }))}
          <label><input type="checkbox" checked={!!commission.auto_lock_enabled} onChange={e => setCommission({ ...commission, auto_lock_enabled: e.target.checked })}/> تفعيل القفل التلقائي</label>
          {btn('حفظ إعدادات العمولة', () => void run(saveCommissionSettings))}
          <hr/><b>إضافة مبلغ لمحفظة عميل</b>
          <select style={styles.input} value={walletCredit.customer_id} onChange={e => setWalletCredit(v => ({ ...v, customer_id: e.target.value }))}><option value="">اختر العميل</option>{adminCustomers.map(x => <option key={x.id} value={x.id}>{x.full_name || x.phone || x.id} · {x.phone || ''}</option>)}</select>
          {field('مبلغ الإضافة', walletCredit.amount, v => setWalletCredit(x => ({ ...x, amount: v })), 'number')}
          {field('ملاحظة / سبب الإضافة', walletCredit.note, v => setWalletCredit(x => ({ ...x, note: v })))}
          {btn('إضافة المبلغ للمحفظة', () => void run(adminCreditWallet))}
        </div>}
        {role === 'driver' && <><div style={styles.card}><b>المبلغ المستحق للتوريد</b><strong style={{ fontSize: 24 }}>{money(driverAccount?.amount_due)}</strong><span style={styles.muted}>{driverProfile?.locked_for_settlement ? 'حسابك موقوف مؤقتًا لحين التوريد' : driverProfile?.is_verified ? 'حسابك موثق' : 'حسابك ينتظر التوثيق'}</span>{btn(driverProfile?.is_available ? 'إيقاف استقبال الطلبات' : 'متاح لاستقبال الطلبات', () => void run(toggleDriverAvailability), true)}<span>رقم التحويل: {appSettings.transfer_phone}</span><label style={{ display: 'grid', gap: 5 }}>إيصال التوريد<input style={styles.input} type="file" accept="image/*" id="saree-settlement-file"/></label>{btn('إرسال إيصال التوريد', () => { const el=document.getElementById('saree-settlement-file') as HTMLInputElement; void run(() => submitSettlement(el.files?.[0])); })}</div>
          <b>الطلبات المتاحة ({orders.length})</b>{orders.map(o => <article style={styles.card} key={o.id}><b>{money(o.total)} · طلب جاهز للاستلام</b><span>{o.customer_name} · {o.customer_phone}</span><span>{[o.delivery_area,o.delivery_street,o.delivery_landmark,o.delivery_unit_details].filter(Boolean).join(' - ')}</span>{o.delivery_map_url && <a href={o.delivery_map_url} target="_blank" rel="noreferrer">فتح موقع العميل على الخريطة</a>}{btn('قبول الطلب', () => void run(() => acceptOrder(o.id)))}</article>)}
          <b>الطلبات المسندة إليك</b>{myOrders.map(o => <article style={styles.card} key={o.id}><b>{money(o.total)} · {o.status}</b>{o.status==='ready_for_pickup' && <div style={styles.row}>{btn('استلمت من المتجر', () => void run(() => moveOrder(o.id,'picked_up')))}{btn('اعتذار / إلغاء', () => void run(() => releaseOrder(o.id)), true)}</div>}{o.status==='picked_up' && btn('تم تسليم الطلب', () => void run(() => moveOrder(o.id,'delivered')))}</article>)}</>}
        {role === 'customer' && tab === 'main' && <><div style={styles.card}><b>رصيد محفظتك</b><strong style={{ fontSize: 24 }}>{money(wallet?.balance)}</strong></div><b>طلباتك التي تنتظر الدفع</b>{myOrders.filter(o => o.status === 'pending' && o.payment_status !== 'paid').map(o => <article style={styles.card} key={o.id}><b>طلب {o.id.slice(0,8)} · {money(o.total)}</b><span>حالة الدفع: {o.payment_status || 'unpaid'}</span><select style={styles.input} value={paymentMethod} onChange={e => setPaymentMethod(e.target.value)}><option value="mobile_wallet">محفظة إلكترونية</option><option value="instapay">إنستا باي</option></select><span>حوّل إلى: {appSettings.transfer_phone}</span><label style={{ display: 'grid', gap: 4 }}>المبلغ المستخدم من المحفظة<input style={styles.input} type="number" min="0" max={Math.min(Number(wallet?.balance || 0), Number(o.total))} value={walletAmounts[o.id] ?? '0'} onChange={e => setWalletAmounts(v => ({ ...v, [o.id]: e.target.value }))}/></label>{Number(wallet?.balance || 0) > 0 && btn('استخدام رصيد المحفظة', () => void run(() => applyWalletToOrder(o.id)), true)}<label>صورة إيصال التحويل<input style={styles.input} type="file" accept="image/*" id={'pay-'+o.id}/></label>{btn('إرسال الإيصال', () => {const el=document.getElementById('pay-'+o.id) as HTMLInputElement;void run(()=>submitOrderPayment(o.id,el.files?.[0]));})}</article>)}</>}
      </div>
    </section>}
  </div>;
}

function mount() {
  if (!db || document.getElementById('saree-operations-root')) return;
  const host = document.createElement('div'); host.id = 'saree-operations-root'; document.body.appendChild(host);
  createRoot(host).render(<SareeOperationsPanel />);
}
if (typeof document !== 'undefined') {
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', mount, { once: true });
  else mount();
}
