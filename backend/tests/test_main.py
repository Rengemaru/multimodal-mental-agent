"""Tests for FastAPI app entrypoints (main.py)."""

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    from app.main import app
    return TestClient(app)


def test_health_endpoint_returns_ok(client):
    """/health は {"status": "ok"} を返す"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_root_endpoint_returns_message(client):
    """/ はバックエンド起動メッセージを返す"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "running" in data["message"]
