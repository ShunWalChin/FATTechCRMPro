"""Import the original company website byte-for-byte from its pinned Git revision.

Usage: python scripts/restore-company-site.py <local-website-clone> [revision]
Only public assets are exported; repository tooling and server configuration stay out.
"""
import hashlib
import json
from pathlib import Path, PurePosixPath
import subprocess
import sys

root = Path(__file__).resolve().parents[1]
repository = Path(sys.argv[1]).resolve()
revision = sys.argv[2] if len(sys.argv) > 2 else "origin/main"
commit = subprocess.check_output(["git", "-C", str(repository), "rev-parse", revision], text=True).strip()
names = subprocess.check_output(["git", "-C", str(repository), "ls-tree", "-r", "--name-only", commit], text=True).splitlines()
destination = root / "apps/web/public/company-site"
files = []
for name in names:
    path = PurePosixPath(name)
    if path.parts[0] in {"scripts", "docs", ".github"} or path.name in {"package.json", "package-lock.json"}:
        continue
    if path.suffix.lower() not in {".html", ".css", ".js", ".png", ".jpg", ".jpeg", ".svg", ".ico", ".webp"} and name not in {"robots.txt", "sitemap.xml", ".well-known/security.txt"}:
        continue
    target = (destination / name).resolve()
    if not target.is_relative_to(destination.resolve()):
        raise ValueError("Asset path escaped destination")
    data = subprocess.check_output(["git", "-C", str(repository), "show", f"{commit}:{name}"])
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(data)
    files.append({"path": name, "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()})
manifest = {"repository": "https://github.com/ShunWalChin/FAT-Tech---Website", "commit": commit,
            "mode": "original public files, unchanged bytes", "files": files}
(root / "apps/web/website-manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
print(f"Restored {len(files)} original public files from {commit}; content hashes recorded.")
