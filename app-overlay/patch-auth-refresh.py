from pathlib import Path
p = Path("src/App.tsx")
s = p.read_text()
old = "supabase.auth.onAuthStateChange((_event:string,session:Session|null)=>{void hydrate(session)})"
new = "supabase.auth.onAuthStateChange((_event:string,session:Session|null)=>{window.dispatchEvent(new Event('saree3:auth-changed'));void hydrate(session)})"
if old in s:
    s = s.replace(old, new, 1)
elif new not in s:
    raise SystemExit("Could not locate Supabase auth state listener")
p.write_text(s)
print("Auth state changes now refresh saved addresses.")
