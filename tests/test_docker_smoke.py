"""Pure unit checks for the Docker smoke harness; no Docker daemon needed."""
import pytest

from scripts import docker_smoke


def test_docker_probe_rejects_non_loopback_binding(monkeypatch):
    monkeypatch.setattr(docker_smoke, "_docker", lambda *args: "0.0.0.0:49155")
    with pytest.raises(RuntimeError, match="127.0.0.1"):
        docker_smoke._check_container("test", "/invoke", "synthetic question")


def test_docker_probe_exercises_health_readiness_api_and_invalid_input(monkeypatch):
    requests = []
    monkeypatch.setattr(docker_smoke, "_docker", lambda *args: "127.0.0.1:49156")

    def fake_request(url, *, question=None):
        requests.append((url, question))
        if url.endswith("/health"):
            return 200, {"status": "ok"}
        if url.endswith("/ready"):
            return 200, {"status": "ready"}
        if question == "":
            return 422, {}
        return 200, {"answer": "synthetic response"}

    monkeypatch.setattr(docker_smoke, "_request", fake_request)
    docker_smoke._check_container("test", "/ask", "synthetic question")
    assert [url.rsplit("/", 1)[-1] for url, _ in requests] == [
        "health", "ready", "ask", "ask",
    ]
    assert requests[-1][1] == ""


def test_docker_probe_rejects_blank_answer(monkeypatch):
    monkeypatch.setattr(docker_smoke, "_docker", lambda *args: "127.0.0.1:49156")

    def fake_request(url, *, question=None):
        if url.endswith("/health"):
            return 200, {"status": "ok"}
        if url.endswith("/ready"):
            return 200, {"status": "ready"}
        return 200, {"answer": ""}

    monkeypatch.setattr(docker_smoke, "_request", fake_request)
    with pytest.raises(RuntimeError, match="API probe failed"):
        docker_smoke._check_container("test", "/ask", "synthetic question")
