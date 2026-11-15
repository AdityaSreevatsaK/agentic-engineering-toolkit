"""Tenant-specific RAG corpus access never falls back to shared documents."""
import json

import pytest
from fastapi.testclient import TestClient

from app.foundation import tenant_knowledge_path
from app.main import app

client = TestClient(app)
KEY_A = "alpha-secret-for-offline-test-012345678901234567"
KEY_B = "beta-secret-for-offline-test-0123456789012345678"


def test_hardened_tenant_corpus_isolation(monkeypatch, tmp_path):
    for tenant, window in (("alpha", 10), ("beta", 20)):
        directory = tmp_path / "tenants" / tenant
        directory.mkdir(parents=True)
        (directory / "knowledge.jsonl").write_text(
            json.dumps({
                "id": tenant,
                "text": f"The returns policy for {tenant} is {window} days.",
            }) + "\n", encoding="utf-8",
        )
    monkeypatch.setenv("AET_PROVIDER", "mock")
    monkeypatch.setenv("AET_SECURITY_MODE", "hardened")
    monkeypatch.setenv("AET_TENANT_KEYS_JSON", json.dumps({"alpha": KEY_A, "beta": KEY_B}))
    monkeypatch.setenv("AET_KNOWLEDGE_PATH", str(tmp_path / "knowledge.jsonl"))
    assert client.get("/ready").status_code == 200
    for key, own, other in ((KEY_A, "alpha", "beta"), (KEY_B, "beta", "alpha")):
        response = client.post(
            "/ask", json={"question": "returns policy"},
            headers={"Authorization": "Bearer " + key},
        )
        assert response.status_code == 200, response.text
        assert response.json()["source_ids"] == [own]
        assert own in response.json()["answer"]
        assert other not in response.json()["answer"]


def test_tenant_path_rejects_traversal():
    with pytest.raises(ValueError):
        tenant_knowledge_path("data/knowledge.jsonl", "../private")
