from pathlib import Path

p = Path("index.html")
if not p.exists():
    raise SystemExit("index.html was not found after extracting the app source")
s = p.read_text()
s = s.replace("<html lang=\"ar\" dir=\"rtl\">", "<html lang=\"ar\" dir=\"rtl\">", 1)
s = s.replace("<title>شفاء | Shifa - ملوي</title>", "<title>سريع | Saree - ملوي</title>")
s = s.replace('content="شفاء - خدمات وتوصيل محلي في ملوي، المنيا. مطاعم وبقالة وصيدليات ومشاوير خاصة."', 'content="سريع - خدمات وتوصيل محلي في ملوي، المنيا. مطاعم وبقالة وخضروات وصيدليات ومشاوير خاصة."')
p.write_text(s)
print("Applied Saree branding to the extracted mobile app.")
