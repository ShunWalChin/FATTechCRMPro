"""Run the test suite against the isolated PostgreSQL over SSH. Never emits generated credentials.

The whole suite runs, not only the isolation tests: the `refined` fixture exists so business rules are
exercised on the real engine, and CI already does that. A local check narrower than CI proves less than
it appears to.
"""
import json
import os
import subprocess
import sys
import time
from pathlib import Path

root = Path(__file__).resolve().parents[1]
settings = {}
config = subprocess.check_output(["ssh", "-G", "palantyr"], text=True)
for line in config.splitlines():
    key, _, value = line.partition(" ")
    settings.setdefault(key, value)
credentials = json.loads(subprocess.check_output([
    "ssh", "-o", "BatchMode=yes", "-o", "ClearAllForwardings=yes", "palantyr",
    "sudo -n cat /opt/fattechcrmpro-validation/database.json",
], text=True))
command = ["ssh", "-F", "none", "-N", "-o", "BatchMode=yes", "-o", "ExitOnForwardFailure=yes",
           "-o", "StrictHostKeyChecking=yes", "-i", settings["identityfile"].strip('"'),
           "-l", settings["user"], "-L", "15441:127.0.0.1:15440", settings["hostname"]]
tunnel = subprocess.Popen(command, stdout=subprocess.DEVNULL,
                          creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0)
try:
    time.sleep(1)
    if tunnel.poll() is not None:
        raise RuntimeError("SSH tunnel failed")
    env = os.environ.copy()
    env["FATTECH_TEST_POSTGRES_OWNER_URL"] = f"postgresql+psycopg://fattech_test_owner:{credentials['owner_password']}@127.0.0.1:15441/fattech_test"
    env["FATTECH_TEST_POSTGRES_APP_URL"] = f"postgresql+psycopg://fattech_app:{credentials['app_password']}@127.0.0.1:15441/fattech_test"
    env["FATTECH_TEST_DB_APP_PASSWORD"] = credentials["app_password"]
    python = root / ("apps/api/.venv/Scripts/python.exe" if os.name == "nt" else "apps/api/.venv/bin/python")
    selection = sys.argv[1:] or ["tests"]
    subprocess.run([str(python), "-m", "pytest", *selection, "-q"],
                   cwd=root / "apps/api", env=env, check=True)
finally:
    tunnel.terminate()
    tunnel.wait(timeout=10)
