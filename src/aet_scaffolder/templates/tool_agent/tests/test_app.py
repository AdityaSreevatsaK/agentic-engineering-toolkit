from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_invoke_mock():
    response = client.post("/invoke", json={"question": "hello"})
    assert response.status_code == 200
    assert response.json() == {"answer": "Mock response to: hello"}


def test_reject_empty_question():
    response = client.post("/invoke", json={"question": ""})
    assert response.status_code == 422
