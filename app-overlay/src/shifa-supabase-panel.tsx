/// <reference types="vite/client" />
import { useEffect, useState } from 'react';
import type { CSSProperties } from 'react';
import { createRoot } from 'react-dom/client';
import { createClient, type Session } from '@supabase/supabase-js';

const url = import.meta.env.VITE_SUPABASE_URL as string | undefined;
const key = (import.meta.env.VITE_SUPABASE_PUBLISHABLE_KEY || import.meta.env.VITE_SUPABASE_ANON_KEY) as string | undefined;
const supabase = url && key ? createClient(url, key) : null;

type Category = { id: string; name_ar: string; slug: string; sort_order: number };

function ShifaConnectionPanel() {
  const [open, setOpen] = useState(false);
  const [categories, setCategories] = useState<Category[]>([]);
  const [loading, setLoading] = useState(true);
  const [connectionError, setConnectionError] = useState('');
  const [session, setSession] = useState<Session | null>(null);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [authBusy, setAuthBusy] = useState(false);
  const [authMessage, setAuthMessage] = useState('');

  async function loadCategories() {
    if (!supabase) {
      setConnectionError('إعدادات الاتصال غير موجودة في نسخة التطبيق.');
      setLoading(false);
      return;
    }
    setLoading(true);
    const { data, error } = await supabase
      .from('categories')
      .select('id,name_ar,slug,sort_order')
      .eq('is_active', true)
      .order('sort_order', { ascending: true });
    if (error) {
      setConnectionError(error.message);
      setCategories([]);
    } else {
      setConnectionError('');
      setCategories(data || []);
    }
    setLoading(false);
  }

  useEffect(() => {
    if (!supabase) {
      setConnectionError('إعدادات الاتصال غير موجودة في نسخة التطبيق.');
      setLoading(false);
      return;
    }
    supabase.auth.getSession().then(({ data }) => setSession(data.session));
    const { data: listener } = supabase.auth.onAuthStateChange((_event, nextSession) => setSession(nextSession));
    void loadCategories();
    return () => listener.subscription.unsubscribe();
  }, []);

  async function authenticate(mode: 'signin' | 'signup') {
    if (!supabase) return;
    setAuthBusy(true);
    setAuthMessage('');
    const result = mode === 'signup'
      ? await supabase.auth.signUp({ email: email.trim(), password })
      : await supabase.auth.signInWithPassword({ email: email.trim(), password });
    if (result.error) {
      setAuthMessage(result.error.message);
    } else if (mode === 'signup' && !result.data.session) {
      setAuthMessage('تم إنشاء طلب التسجيل. راجع بريدك الإلكتروني لتأكيد الحساب ثم سجّل الدخول.');
    } else {
      setAuthMessage(mode === 'signup' ? 'تم إنشاء الحساب وتسجيل الدخول.' : 'تم تسجيل الدخول بنجاح.');
    }
    setAuthBusy(false);
  }

  async function signOut() {
    if (!supabase) return;
    const { error } = await supabase.auth.signOut();
    setAuthMessage(error ? error.message : 'تم تسجيل الخروج.');
  }

  const shell: CSSProperties = {
    position: 'fixed', zIndex: 2147483000, right: 12, bottom: 'max(14px, env(safe-area-inset-bottom))',
    width: 'min(360px, calc(100vw - 24px))', fontFamily: 'Cairo, system-ui, sans-serif', direction: 'rtl',
    color: '#15332e'
  };
  const card: CSSProperties = {
    background: '#ffffff', border: '1px solid #d5e8e2', borderRadius: 18,
    boxShadow: '0 12px 38px rgba(9,45,37,.22)', overflow: 'hidden'
  };
  const button: CSSProperties = {
    border: 0, borderRadius: 11, padding: '10px 13px', background: '#087f68',
    color: '#fff', fontWeight: 800, fontFamily: 'inherit', cursor: 'pointer'
  };
  const input: CSSProperties = {
    width: '100%', boxSizing: 'border-box', border: '1px solid #cbded8', borderRadius: 10,
    padding: '10px 12px', font: 'inherit', marginTop: 7, background: '#fff', color: '#15332e'
  };

  return <div style={shell}>
    {!open ? (
      <button style={{ ...button, borderRadius: 999, boxShadow: '0 5px 20px #0b443655' }} onClick={() => setOpen(true)}>
        شفاء · {loading ? 'جارٍ الاتصال…' : connectionError ? 'تحقق من الاتصال' : 'متصل بقاعدة البيانات'}
      </button>
    ) : (
      <div style={card}>
        <div style={{ background: '#eaf7f2', padding: '12px 15px', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div><strong style={{ display: 'block', fontSize: 16 }}>شفاء | خدمات ملوي</strong><small>{loading ? 'جارٍ تحميل البيانات…' : connectionError ? 'تعذر تحميل التصنيفات' : 'اتصال مباشر بقاعدة البيانات'}</small></div>
          <button aria-label="إغلاق" onClick={() => setOpen(false)} style={{ ...button, padding: '6px 11px', background: '#d9ebe5', color: '#17483e' }}>×</button>
        </div>
        <div style={{ padding: 14, maxHeight: 'min(65vh, 520px)', overflowY: 'auto' }}>
          {connectionError ? <div style={{ color: '#a52828', fontSize: 13, marginBottom: 10 }}>خطأ الاتصال: {connectionError}</div> : null}
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 9 }}>
            <strong>الأقسام المتاحة</strong>
            <button onClick={() => void loadCategories()} style={{ ...button, padding: '6px 10px', fontSize: 12 }}>تحديث</button>
          </div>
          {loading ? <p>بنحمّل أقسام ملوي…</p> : categories.length ? (
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2,minmax(0,1fr))', gap: 8 }}>
              {categories.map(category => <div key={category.id} style={{ background: '#f0f8f5', border: '1px solid #dcece6', borderRadius: 11, padding: '11px 8px', fontWeight: 700, textAlign: 'center' }}>{category.name_ar}</div>)}
            </div>
          ) : <p style={{ fontSize: 13 }}>لا توجد تصنيفات ظاهرة حاليًا.</p>}
          <div style={{ height: 1, background: '#e3eeea', margin: '15px 0' }} />
          <strong>{session ? 'حسابك' : 'تسجيل الدخول أو إنشاء حساب'}</strong>
          {session ? (
            <div style={{ marginTop: 8 }}>
              <div style={{ fontSize: 13, overflowWrap: 'anywhere' }}>{session.user.email}</div>
              <button onClick={() => void signOut()} style={{ ...button, marginTop: 10, background: '#31564e' }}>تسجيل الخروج</button>
            </div>
          ) : (
            <>
              <input style={input} type="email" autoComplete="email" placeholder="البريد الإلكتروني" value={email} onChange={e => setEmail(e.target.value)} />
              <input style={input} type="password" autoComplete="current-password" placeholder="كلمة المرور (6 أحرف على الأقل)" value={password} onChange={e => setPassword(e.target.value)} />
              <div style={{ display: 'flex', gap: 8, marginTop: 10 }}>
                <button disabled={authBusy || !email.trim() || password.length < 6} onClick={() => void authenticate('signin')} style={{ ...button, flex: 1, opacity: authBusy ? .6 : 1 }}>دخول</button>
                <button disabled={authBusy || !email.trim() || password.length < 6} onClick={() => void authenticate('signup')} style={{ ...button, flex: 1, background: '#31564e', opacity: authBusy ? .6 : 1 }}>حساب جديد</button>
              </div>
            </>
          )}
          {authMessage ? <p role="status" style={{ fontSize: 12, lineHeight: 1.6, marginBottom: 0 }}>{authMessage}</p> : null}
          <p style={{ color: '#6b827b', fontSize: 11, lineHeight: 1.5, marginBottom: 0 }}>هذه نافذة ربط واختبار أولي. لا تُرسل بيانات طبية أو وصفات هنا.</p>
        </div>
      </div>
    )}
  </div>;
}

function mount() {
  if (document.getElementById('shifa-supabase-panel')) return;
  const host = document.createElement('div');
  host.id = 'shifa-supabase-panel';
  document.body.appendChild(host);
  createRoot(host).render(<ShifaConnectionPanel />);
}

if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', mount, { once: true });
else mount();
