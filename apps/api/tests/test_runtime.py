import functools
import sys
from pathlib import Path

import pytest
import httpx
from pydantic import ValidationError

from fattech import worker, worker_health
from fattech.config import Settings
from fattech.db import make_engine, session_factory
from fattech.migrate import migrate
from fattech.models import Tenant


@pytest.mark.parametrize("value", ["prodution", "Production", "", " "])
def test_environment_typos_never_bypass_production_guards(monkeypatch, value):
    monkeypatch.setenv("FATTECH_ENV", value)
    with pytest.raises(ValidationError, match="env"):
        Settings(_env_file=None)


@pytest.mark.parametrize("field", ["database_url", "allowed_origins", "public_tenant_slug"])
@pytest.mark.parametrize("value", ["", " \t"])
def test_explicit_blank_required_configuration_fails(monkeypatch, field, value):
    monkeypatch.setenv(f"FATTECH_{field.upper()}", value)
    with pytest.raises(ValidationError, match=field):
        Settings(_env_file=None, env="test")


def test_optional_empty_settings_and_valid_production_still_work(monkeypatch):
    monkeypatch.setenv("FATTECH_N8N_OUTBOUND_URL", "")
    monkeypatch.setenv("FATTECH_N8N_OUTBOUND_TOKEN", "")
    settings = Settings(_env_file=None, env="production",
                        database_url="postgresql+psycopg://app:example-pass@db/fattech",
                        allowed_origins="https://crm.example.com", webhook_secret="x" * 32)
    assert settings.production and settings.n8n_outbound_url == ""
    with pytest.raises(ValidationError) as error:
        Settings(_env_file=None, **{**settings.model_dump(), "allowed_origins": " "})
    assert "example-pass" not in str(error.value)
    with pytest.raises(ValidationError, match="webhook_secret"):
        Settings(_env_file=None, env="test", webhook_secret=" " * 32)
    with pytest.raises(ValidationError):
        Settings(_env_file=None, env="production", database_url="sqlite:///test.db")


def test_blank_boolean_does_not_fall_back_to_a_default(monkeypatch):
    monkeypatch.setenv("FATTECH_EXTERNAL_SENDS_ENABLED", "")
    with pytest.raises(ValidationError, match="external_sends_enabled"):
        Settings(_env_file=None, env="test")


def test_heartbeat_atomic_replacement_missing_stale_and_invalid(tmp_path, monkeypatch):
    path = tmp_path / "heartbeat"
    monkeypatch.setattr(worker_health.time, "monotonic", lambda: 1000.0)
    assert not worker_health.heartbeat_is_fresh(path)
    path.write_text("old", encoding="ascii")
    original_replace = worker_health.os.replace

    def replace(source, target):
        assert path.read_text(encoding="ascii") == "old"
        assert Path(source).read_text(encoding="ascii") == "1000.0"
        original_replace(source, target)

    monkeypatch.setattr(worker_health.os, "replace", replace)
    worker_health.write_heartbeat(path)
    assert worker_health.heartbeat_is_fresh(path)
    assert list(tmp_path.iterdir()) == [path]
    monkeypatch.setattr(worker_health.time, "monotonic", lambda: 1121.0)
    assert not worker_health.heartbeat_is_fresh(path)
    for invalid in ("garbage", "nan", "inf", "99999", ""):
        path.write_text(invalid, encoding="ascii")
        assert not worker_health.heartbeat_is_fresh(path)


def test_worker_idle_is_healthy_and_failed_iteration_invalidates_progress(tmp_path, monkeypatch, caplog):
    path = tmp_path / "heartbeat"
    settings = Settings(_env_file=None, env="test", database_url=f"sqlite:///{tmp_path / 'worker.db'}",
                        n8n_outbound_url="")
    monkeypatch.setattr(worker, "get_settings", lambda: settings)
    monkeypatch.setattr(worker, "HEARTBEAT_PATH", path)
    monkeypatch.setattr(worker, "write_heartbeat", functools.partial(worker_health.write_heartbeat, path))
    monkeypatch.setattr(sys, "argv", ["worker", "--once"])
    worker.main()
    assert worker_health.heartbeat_is_fresh(path)

    def failed_iteration(*args, on_progress):
        on_progress()
        assert worker_health.heartbeat_is_fresh(path)
        raise RuntimeError("credential-or-customer-data-must-not-be-logged")

    monkeypatch.setattr(worker, "run_once", failed_iteration)
    with pytest.raises(SystemExit) as exit_code:
        worker.main()
    assert exit_code.value.code == 1
    assert not worker_health.heartbeat_is_fresh(path)
    assert "worker_iteration_failed type=RuntimeError" in caplog.text
    assert "credential-or-customer-data" not in caplog.text


def test_progress_pulses_for_each_completed_tenant(tmp_path):
    engine = make_engine(f"sqlite:///{tmp_path / 'tenants.db'}")
    migrate(engine)
    factory = session_factory(engine)
    with factory() as db:
        db.add_all([Tenant(name="One", slug="one"), Tenant(name="Two", slug="two")])
        db.commit()
    progress = []
    settings = Settings(_env_file=None, env="test", n8n_outbound_url="https://n8n.example.com/webhook",
                        webhook_secret="x" * 32)
    with httpx.Client(transport=httpx.MockTransport(lambda request: pytest.fail("No pending event"))) as client:
        assert worker.run_once(factory, settings, client, on_progress=lambda: progress.append(True)) == 0
    assert len(progress) == 2
    engine.dispose()
