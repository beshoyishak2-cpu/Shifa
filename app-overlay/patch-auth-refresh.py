from pathlib import Path
p = Path("src/App.tsx")
s = p.read_text()

# Phone sign-in uses an internal email identity, so the phone is stored in
# auth user metadata rather than Supabase's dedicated phone field.
old_phone = "setSignedInPhone(session?.user.phone??null);"
new_phone = "setSignedInPhone(session?.user.user_metadata?.phone??session?.user.phone??null);"
if old_phone in s:
    s = s.replace(old_phone, new_phone, 1)
elif new_phone not in s:
    raise SystemExit("Could not locate signed-in phone hydration")

# Explain the empty marketplace instead of rendering a blank product/store area.
old_store_grid = '<div className="store-grid">{visibleStores.map(s=><button className="store-card"'
new_store_grid = '<div className="store-grid">{visibleStores.length===0?<Empty title="لا توجد متاجر أو منتجات منشورة بعد" hint="لسه الإدارة ما أضافتش متاجر ومنتجات لملوي. تقدر تستخدم خدمة المشوار، وسيظهر التسوق هنا بعد إضافة أول متجر."/>:visibleStores.map(s=><button className="store-card"'
if old_store_grid in s:
    s = s.replace(old_store_grid, new_store_grid, 1)
elif new_store_grid not in s:
    raise SystemExit("Could not locate store grid for empty-state fix")

p.write_text(s)

test_path = Path("tests/source-smoke.test.cjs")
if test_path.exists():
    t = test_path.read_text()
    if "phone auth metadata restores authenticated customer state" not in t:
        t += """
test('phone auth metadata restores authenticated customer state', () => {
  assert.ok(app().includes('session?.user.user_metadata?.phone??session?.user.phone??null'));
});
test('empty marketplace explains that stores and products are not published', () => {
  assert.ok(app().includes('لا توجد متاجر أو منتجات منشورة بعد'));
});
"""
        test_path.write_text(t)

print("Fixed phone-session hydration and added a clear empty-marketplace state.")
