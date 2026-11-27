from pathlib import Path

p = Path('src/App.tsx')
s = p.read_text()

old_import = "import { useEffect, useMemo, useState } from 'react';"
if old_import not in s:
    raise SystemExit('React import anchor missing')
if "import { App as CapacitorApp } from '@capacitor/app';" not in s:
    s = s.replace(old_import, old_import + "\nimport { App as CapacitorApp } from '@capacitor/app';", 1)

old_state = "[tab,setTab]=useState('home'),[service"
new_state = "[tab,setTabState]=useState('home'),[tabHistory,setTabHistory]=useState<string[]>([]),[service"
if old_state in s:
    s = s.replace(old_state, new_state, 1)
elif "[tab,setTabState]=useState('home')" not in s:
    raise SystemExit('Tab state anchor missing')

anchor = " const notify=(s:string)=>{setToast(s);window.setTimeout(()=>setToast(''),3000)};"
logic = """
 const setTab=(next:string)=>{if(next===tab)return;setTabHistory(prev=>[...prev,tab]);setTabState(next);};
 const goBack=()=>{if(modal){setModal('');return;}if(selectedStore){setSelectedStore(null);return;}if(tabHistory.length){setTabState(tabHistory[tabHistory.length-1]);setTabHistory(prev=>prev.slice(0,-1));return;}const home=role==='customer'?'home':'overview';if(tab!==home){setTabState(home);return;}};
 useEffect(()=>{if(!isNativeApp())return;let active=true;let handle:{remove:()=>Promise<void>}|undefined;CapacitorApp.addListener('backButton',()=>{if(modal||selectedStore||tabHistory.length||tab!==(role==='customer'?'home':'overview')){goBack();return;}void CapacitorApp.exitApp();}).then(h=>{if(active)handle=h;else void h.remove();}).catch(()=>{});return()=>{active=false;if(handle)void handle.remove();};},[modal,selectedStore,tabHistory,tab,role]);
"""
if "const goBack=()=>{" not in s:
    if anchor not in s: raise SystemExit('notify anchor missing')
    s = s.replace(anchor, anchor + logic, 1)

old_header = '<header><button className="icon-btn" aria-label="فتح القائمة" onClick={()=>setModal(\'menu\')}><Menu/></button>'
new_header = '<header>{tabHistory.length||selectedStore||tab!==(role===\'customer\'?\'home\':\'overview\')?<button className="icon-btn" aria-label="رجوع" onClick={goBack}><ArrowLeft/></button>:null}<button className="icon-btn" aria-label="فتح القائمة" onClick={()=>setModal(\'menu\')}><Menu/></button>'
if old_header in s:
    s = s.replace(old_header, new_header, 1)
elif 'aria-label="رجوع" onClick={goBack}' not in s:
    raise SystemExit('Header navigation anchor missing')

p.write_text(s)
print('Added Android hardware back handling and in-app back navigation.')
