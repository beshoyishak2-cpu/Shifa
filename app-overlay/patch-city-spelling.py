#!/usr/bin/env python3
"""Correct the Arabic spelling of Mallawi in extracted application source.

This patch intentionally runs after every other overlay patch. It only edits
UTF-8 text files from the extracted app workspace; it does not touch overlay
scripts, dependencies, generated build output, native project files, or database
migrations. Latin identifiers such as com.shifa.mallawi are left unchanged.
"""
from pathlib import Path

ROOT = Path.cwd()
OLD = "ملوي"
NEW = "ملوى"
EXCLUDED_DIRS = {
    ".git", ".github", "app-overlay", "node_modules", "dist", "build",
    "android", "ios", "supabase", "docs", ".next", ".turbo",
}
TEXT_SUFFIXES = {
    ".html", ".htm", ".tsx", ".ts", ".jsx", ".js", ".mjs", ".cjs",
    ".css", ".scss", ".json", ".md", ".txt", ".xml", ".plist",
    ".swift", ".gradle", ".properties", ".yml", ".yaml", ".svg",
}

changed_files = 0
replacements = 0

for path in ROOT.rglob("*"):
    if not path.is_file():
        continue
    relative = path.relative_to(ROOT)
    if any(part in EXCLUDED_DIRS for part in relative.parts):
        continue
    if path.name != "index.html" and path.suffix.lower() not in TEXT_SUFFIXES:
        continue
    try:
        original = path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        continue
    count = original.count(OLD)
    if count:
        path.write_text(original.replace(OLD, NEW), encoding="utf-8")
        changed_files += 1
        replacements += count

remaining = []
for path in ROOT.rglob("*"):
    if not path.is_file():
        continue
    relative = path.relative_to(ROOT)
    if any(part in EXCLUDED_DIRS for part in relative.parts):
        continue
    if path.name != "index.html" and path.suffix.lower() not in TEXT_SUFFIXES:
        continue
    try:
        if OLD in path.read_text(encoding="utf-8"):
            remaining.append(str(relative))
    except (UnicodeDecodeError, OSError):
        continue

if remaining:
    raise SystemExit(
        "Incorrect city spelling remains in extracted source: " + ", ".join(remaining)
    )

if not (ROOT / "index.html").is_file():
    raise SystemExit("index.html is missing; city spelling verification cannot complete")

print(
    f"City spelling corrected: {replacements} replacements across "
    f"{changed_files} files; no incorrect spelling remains in extracted source."
)
