import shutil
from pathlib import Path

src_dir = Path("docs/archive/historical_reports")
dest_dir = Path("docs")

for file in src_dir.glob("*.md"):
    dest = dest_dir / file.name
    print(f"Restoring {file} -> {dest}")
    shutil.copy2(file, dest)

print("[SUCCESS] Restored all historical markdown files to docs root!")
