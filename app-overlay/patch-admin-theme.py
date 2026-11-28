"""Bring the two admin panels onto the agreed design and hide pharmacy-only tools.

The advanced panel and the operations centre are rendered from their own React
roots with inline styles, so they need their own pass. Pharmacy-specific admin
tabs (stock batches with expiry dates, drug alternatives) are removed from the
Sari3 admin surface; the code behind them stays untouched, nothing is deleted.
"""
from pathlib import Path

ADV = Path("src/SareeAdvancedAdmin.tsx")
OPS = Path("src/SareeOperationsPanel.tsx")
CSS = Path("src/style.css")


def edit(path, pairs):
    body = path.read_text(encoding="utf-8")
    for old, new in pairs:
        if old not in body:
            raise SystemExit(f"missing anchor in {path}: {old[:80]}")
        body = body.replace(old, new, 1)
    path.write_text(body, encoding="utf-8")


edit(ADV, [
    # pharmacy-only tabs out of the Sari3 admin surface
    ("[['stock','المخزون والصلاحية'],['zones','مناطق التوصيل'],['permissions','الصلاحيات'],"
     "['alternatives','بدائل الأدوية'],['refunds','الاسترجاع'],['audit','سجل العمليات']]",
     "[['permissions','الصلاحيات'],['zones','مناطق التوصيل'],['refunds','الاسترجاع'],['audit','سجل العمليات']]"),
    ("[tab,setTab]=useState('stock')", "[tab,setTab]=useState('permissions')"),
    ("المخزون والصلاحية والصلاحيات والتوصيل والاسترجاع", "الصلاحيات والتوصيل والاسترجاع وسجل العمليات"),
    # reference colours
    ("color:'#183a34'", "color:'#141B0D'"),
    ("trigger:{border:0,borderRadius:999,background:'#164e63'", "trigger:{border:0,borderRadius:999,background:'#6FCB00'"),
    ("border:'1px solid #d8e8e2',borderRadius:18,boxShadow:'0 14px 48px #052f2740'",
     "border:'1px solid #EDEFE8',borderRadius:22,boxShadow:'0 14px 48px #141b0d1f'"),
    ("head:{background:'#eaf4f7'", "head:{background:'#F1FAD3'"),
    ("btn:{border:0,borderRadius:8,padding:'8px 10px',background:'#164e63',color:'#fff',fontWeight:700}",
     "btn:{border:0,borderRadius:12,padding:'8px 10px',background:'#6FCB00',color:'#fff',fontWeight:700}"),
    ("background:soft?'#e7f0f2':'#164e63',color:soft?'#164e63':'white'",
     "background:soft?'#F1FAD3':'#6FCB00',color:soft?'#3E7A00':'white'"),
    ("border:'1px solid #cbdde1',borderRadius:8,background:'#fff'",
     "border:'1px solid #EDEFE8',borderRadius:10,background:'#F7F8F5'"),
    ("muted:{fontSize:12,color:'#637b82'}", "muted:{fontSize:12,color:'#8A8F86'}"),
    ("card:{border:'1px solid #dce8eb',borderRadius:11", "card:{border:'1px solid #EDEFE8',borderRadius:14"),
])

edit(OPS, [
    ("color: '#183a34', maxWidth: '46vw' }", "color: '#141B0D', maxWidth: '46vw' }"),
    ("trigger: { border: 0, borderRadius: 999, background: '#087f68'",
     "trigger: { border: 0, borderRadius: 999, background: '#6FCB00'"),
    ("background: '#f6faf8', border: '1px solid #d8e8e2', borderRadius: 22",
     "background: '#fff', border: '1px solid #EDEFE8', borderRadius: 22"),
    ("top: { background: 'linear-gradient(135deg,#075e50,#0b8b70)'", "top: { background: '#6FCB00'"),
    ("button: { border: 0, borderRadius: 9, padding: '9px 11px', background: '#087f68'",
     "button: { border: 0, borderRadius: 12, padding: '9px 11px', background: '#6FCB00'"),
    ("muted: { color: '#668079', fontSize: 12 },", "muted: { color: '#8A8F86', fontSize: 12 },"),
    ("border: '1px solid #cddfd8', borderRadius: 9, background: '#fff'",
     "border: '1px solid #EDEFE8', borderRadius: 10, background: '#F7F8F5'"),
    ("background: secondary ? '#e5f1ec' : '#087f68', color: secondary ? '#185046' : '#fff'",
     "background: secondary ? '#F1FAD3' : '#6FCB00', color: secondary ? '#3E7A00' : '#fff'"),
    ("card: { border: '1px solid #e1ebe6', borderRadius: 16", "card: { border: '1px solid #EDEFE8', borderRadius: 16"),
    ("background: '#dcece6', color: '#185046'", "background: '#F1FAD3', color: '#3E7A00'"),
])

EXTRA = """
/* never show one floating admin pill on top of the other open panel */
body:has(#saree-advanced-admin-root section) #saree-operations-root{display:none!important}
body:has(#saree-operations-root section) #saree-advanced-admin-root{display:none!important}
#saree-advanced-admin-root .dialog,#saree-operations-root .dialog{border-radius:22px}
"""
style = CSS.read_text(encoding="utf-8")
if "never show one floating admin pill" not in style:
    CSS.write_text(style.rstrip() + "\n" + EXTRA, encoding="utf-8")

print("Applied admin panel theme and hid pharmacy-only admin tabs.")
