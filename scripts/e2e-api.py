"""Isolated loopback-only database/server for browser integration tests."""
import os
import sys
from pathlib import Path
from uuid import uuid4

root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root / "apps/api"))
data_dir = root / ".local/e2e"
data_dir.mkdir(parents=True, exist_ok=True)
os.environ.update({
    "FATTECH_ENV": "development",
    "FATTECH_DATABASE_URL": "sqlite:///" + (data_dir / f"{uuid4().hex}.db").as_posix(),
    "FATTECH_ALLOWED_ORIGINS": "http://127.0.0.1:3100,http://localhost:3100",
    "FATTECH_WEBHOOK_SECRET": "e2e-local-test-secret-not-for-production-2026",
})
from fattech.config import get_settings
from fattech.db import make_engine, session_factory
from fattech.migrate import migrate
from fattech.seed import bootstrap

engine = make_engine(get_settings().database_url)
migrate(engine)
with session_factory(engine)() as session:
    bootstrap(session, slug="fattech", email="e2e@fattech.com.br",
              password="Test-only-Fattech-Password-2026!", demo=True)
engine.dispose()
import uvicorn
uvicorn.run("fattech.main:app", host="127.0.0.1", port=8100, log_level="warning")
