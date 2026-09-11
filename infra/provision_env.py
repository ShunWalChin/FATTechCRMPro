"""Run ON THE SERVER as root; generate private credentials without printing them."""
import argparse
import os
import re
import secrets
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument("--path", default="/etc/fattechcrmpro.env")
parser.add_argument("--origin", required=True, help="The verified HTTPS URL for this deployment")
parser.add_argument("--email", default="admin@fattech.com.br")
args = parser.parse_args()
if not re.fullmatch(r"https://[A-Za-z0-9.-]+(?::[0-9]{1,5})?", args.origin):
    parser.error("origin must be an HTTPS origin with DNS hostname and optional port, without path or shell syntax")
if not re.fullmatch(r"[A-Za-z0-9._+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,63}", args.email):
    parser.error("email must be a single email address")
target = Path(args.path)
values = {
    "POSTGRES_PASSWORD": secrets.token_hex(32),
    "FATTECH_DB_APP_PASSWORD": secrets.token_hex(32),
    "FATTECH_WEBHOOK_SECRET": secrets.token_hex(32),
    "FATTECH_ALLOWED_ORIGINS": args.origin,
    "FATTECH_SITE_URL": args.origin,
    "FATTECH_PUBLIC_TENANT_SLUG": "fattech",
    "FATTECH_BOOTSTRAP_EMAIL": args.email,
    "FATTECH_BOOTSTRAP_PASSWORD": secrets.token_urlsafe(24),
    "RELEASE_TAG": "local",
    "WEB_PORT": "4320",
    "API_PORT": "4321",
    "FATTECH_N8N_OUTBOUND_URL": "",
    "FATTECH_N8N_OUTBOUND_TOKEN": "",
}
# O_EXCL protects credentials from accidental replacement on a second run.
fd = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
with os.fdopen(fd, "w", encoding="utf-8") as stream:
    stream.write("\n".join(f"{key}={value}" for key, value in values.items()) + "\n")
print(f"Created protected environment: {target} (values withheld)")
