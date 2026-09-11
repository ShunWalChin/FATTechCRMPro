"""Inventory staged Git blobs, using canonical line endings. Stage changes before running."""
import csv
import hashlib
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
output = ROOT / "docs" / "FILE_INVENTORY.csv"
entries = subprocess.check_output(["git", "ls-files", "--stage", "-z"], cwd=ROOT).decode("utf-8").split("\0")
rows = []
for entry in filter(None, entries):
    metadata, name = entry.split("\t", 1)
    _, blob, stage = metadata.split()
    if stage != "0":
        raise RuntimeError("Resolve Git conflicts before generating the inventory")
    file = ROOT / name
    if file == output or not file.is_file():
        continue
    data = subprocess.check_output(["git", "cat-file", "blob", blob], cwd=ROOT)
    rows.append((name, len(data), hashlib.sha256(data).hexdigest()))
output.parent.mkdir(parents=True, exist_ok=True)
with output.open("w", newline="", encoding="utf-8") as stream:
    writer = csv.writer(stream)
    writer.writerow(("path", "bytes", "sha256"))
    writer.writerows(rows)
print(f"Inventoried {len(rows)} staged Git blobs -> docs/FILE_INVENTORY.csv")
