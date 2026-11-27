from pathlib import Path

source = Path("app-overlay/src/SareeOperationsPanel.tsx")
target = Path("src/SareeOperationsPanel.tsx")
advanced_source = Path("app-overlay/src/SareeAdvancedAdmin.tsx")
advanced_target = Path("src/SareeAdvancedAdmin.tsx")
main = Path("src/main.tsx")
if not source.exists():
    raise SystemExit("Saree operations panel source is missing")
if not advanced_source.exists():
    raise SystemExit("Saree advanced admin source is missing")
if not main.exists():
    raise SystemExit("Vite entrypoint src/main.tsx was not found")
target.write_text(source.read_text())
advanced_target.write_text(advanced_source.read_text())
text = main.read_text()
imports = []
if "SareeOperationsPanel" not in text:
    imports.append("import './SareeOperationsPanel';")
if "SareeAdvancedAdmin" not in text:
    imports.append("import './SareeAdvancedAdmin';")
if imports:
    main.write_text("\n".join(imports) + "\n" + text)
print("Mounted Saree operations and advanced admin panels.")
