from pathlib import Path

source = Path("app-overlay/src/SareeOperationsPanel.tsx")
target = Path("src/SareeOperationsPanel.tsx")
main = Path("src/main.tsx")
if not source.exists():
    raise SystemExit("Saree operations panel source is missing")
if not main.exists():
    raise SystemExit("Vite entrypoint src/main.tsx was not found")
target.write_text(source.read_text())
text = main.read_text()
if "SareeOperationsPanel" not in text:
    main.write_text("import './SareeOperationsPanel';\n" + text)
print("Mounted Saree operations panel.")
