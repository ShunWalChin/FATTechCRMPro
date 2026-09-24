import json

import pytest
from fastapi import HTTPException

from fattech import content_ops


def test_content_bank_is_read_from_packaged_layout(tmp_path, monkeypatch):
    original = content_ops.banco_de_pautas()
    packaged = tmp_path / "fattech"
    (packaged / "data").mkdir(parents=True)
    (packaged / "data/posiciona-pautas.json").write_text(json.dumps(original), encoding="utf-8")
    monkeypatch.setattr(content_ops, "__file__", str(packaged / "content_ops.py"))
    assert content_ops.banco_de_pautas() == original


def test_missing_packaged_bank_returns_service_unavailable(tmp_path, monkeypatch):
    monkeypatch.setattr(content_ops, "__file__", str(tmp_path / "content_ops.py"))
    with pytest.raises(HTTPException) as caught:
        content_ops.banco_de_pautas()
    assert caught.value.status_code == 503
