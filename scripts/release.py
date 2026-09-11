"""Package the committed Git tree; private workspaces never enter a release."""
import hashlib
import subprocess
from pathlib import Path

root = Path(__file__).resolve().parents[1]
subprocess.run([__import__("sys").executable, "scripts/check_secrets.py"], cwd=root, check=True)
if subprocess.check_output(["git", "status", "--porcelain"], cwd=root).strip():
    raise SystemExit("Commit the reviewed changes before packaging a production release.")
target = root / ".local/release.tar.gz"
target.parent.mkdir(exist_ok=True)
subprocess.run(["git", "archive", "--format=tar.gz", f"--output={target}", "HEAD"], cwd=root, check=True)
digest = hashlib.sha256(target.read_bytes()).hexdigest()
target.with_suffix(".gz.sha256").write_text(f"{digest}  {target.name}\n", encoding="utf-8")
print(f"Release: {target.name}; SHA-256 {digest}; {target.stat().st_size} bytes")
