"""Small repository guard. Prints only filename/line/category, never matching secrets."""
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
patterns = {
    "private key": re.compile(r"-----BEGIN (?:OPENSSH|RSA|EC|DSA|ENCRYPTED) PRIVATE KEY-----"),
    "GitHub token": re.compile(r"\b(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{50,})\b"),
    "provider secret": re.compile(r"\bsk-(?:proj-|ant-)?[A-Za-z0-9_-]{30,}\b"),
    "AWS access key": re.compile(r"\bAKIA[A-Z0-9]{16}\b"),
    "Cloudflare token": re.compile(r"\bcfat_[A-Za-z0-9_-]{30,}\b"),
    "database credentials": re.compile(r"postgres(?:ql)?(?:\+psycopg)?://[^\s:/]+:[A-Za-z0-9+/=_-]{16,}@"),
}
names = subprocess.check_output(
    ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"], cwd=ROOT
).decode("utf-8").split("\0")
errors = []
for name in sorted(set(filter(None, names))):
    file = ROOT / name
    if not file.is_file():
        continue
    if file.suffix in {".key", ".pem", ".p12"} or (file.name.startswith(".env") and not file.name.endswith(".example")):
        errors.append(f"{name}: prohibited credential file")
    data = file.read_bytes()
    if b"\0" in data:
        continue
    for line_number, line in enumerate(data.decode("utf-8", errors="replace").splitlines(), 1):
        for kind, pattern in patterns.items():
            if pattern.search(line):
                errors.append(f"{name}:{line_number}: {kind}")
if errors:
    print("\n".join(errors))
    sys.exit(1)
print("No credential patterns found in repository candidates.")
