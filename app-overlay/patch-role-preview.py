from pathlib import Path

panel = Path("src/SareeOperationsPanel.tsx")
app = Path("src/App.tsx")
if not panel.exists() or not app.exists():
    raise SystemExit("Role preview patch: required source files are missing")

p = panel.read_text()
anchor = '      <div style={styles.body}>'
insert = """      <div style={styles.body}>
        {role === 'admin' && <section style={{ ...styles.card, border: '1px solid #80b9a7', background: '#f0faf6' }}>
          <b>وضع تجربة التطبيق</b>
          <div style={styles.muted}>معاينة واجهات الأدوار دون تغيير صلاحيات حساب الأدمن أو بيانات الحساب.</div>
          <div style={styles.row}>
            {([{id:'customer',label:'العميل'},{id:'driver',label:'المندوب'},{id:'merchant',label:'التاجر'},{id:'admin',label:'إنهاء المعاينة'}] as const).map(item => <button key={item.id} style={{ ...styles.button, background: item.id === 'admin' ? '#e5f1ec' : '#087f68', color: item.id === 'admin' ? '#185046' : '#fff' }} onClick={() => window.dispatchEvent(new CustomEvent('saree3:preview-role', { detail: item.id }))}>{item.label}</button>)}
          </div>
          <div style={styles.muted}>المعاينة تغيّر شكل الواجهة فقط؛ تنفيذ الطلبات والمدفوعات الحقيقية يحتاج حسابًا منفصلًا بالدور المعتمد.</div>
        </section>}
"""
if "وضع تجربة التطبيق" not in p:
    if p.count(anchor) != 1:
        raise SystemExit("Role preview panel insertion point not found exactly once")
    p = p.replace(anchor, insert, 1)
    panel.write_text(p)

s = app.read_text()
needle = "const chooseRole="
effect = """useEffect(() => {
  const onPreviewRole = (event: Event) => {
    const requested = (event as CustomEvent).detail;
    if (!['customer', 'driver', 'merchant', 'admin'].includes(requested)) return;
    setRole(requested as Role);
    setTab('home');
    setSelectedStore(null);
    setModal('');
  };
  window.addEventListener('saree3:preview-role', onPreviewRole);
  return () => window.removeEventListener('saree3:preview-role', onPreviewRole);
}, []);
"""
if "saree3:preview-role" not in s:
    i = s.find(needle)
    if i < 0:
        raise SystemExit("Could not locate chooseRole to install role-preview listener")
    s = s[:i] + effect + s[i:]
    app.write_text(s)
print("Installed admin-only visual role preview without changing authenticated role.")
