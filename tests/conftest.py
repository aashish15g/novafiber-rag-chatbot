import re

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app
from app.services.auth import hash_password


class TestTokenizer:
    def __call__(self, text, **kwargs):
        words = list(re.finditer(r"\S+", text))
        return {"offset_mapping": [word.span() for word in words]}


class TestEmbeddings:
    dimension = 1024
    tokenizer = TestTokenizer()

    def load(self):
        pass

    def encode(self, texts, query=False):
        return [[1.0] + [0.0] * 1023 for text in texts]


class TestGenerator:
    api_key = "test-key"

    def generate(self, question, passages):
        return f"According to the policy: {passages[0]['text']} [S1]", ["S1"]

    def close(self):
        pass


def login(client, email, password="TestPassword123!"):
    response = client.post("/api/auth/login", json={"email": email, "password": password})
    if response.status_code == 200:
        client.headers["X-CSRF-Token"] = client.cookies.get("csrf_token")
    return response


@pytest.fixture
def anonymous_client(tmp_path):
    settings = Settings(_env_file=None, data_dir=tmp_path, max_upload_mb=1,
                        jwt_secret="test-only-signing-key-not-for-production-123")
    with TestClient(create_app(settings, TestEmbeddings(), TestGenerator())) as client:
        client.app.state.rag.load()
        yield client


@pytest.fixture
def client(anonymous_client):
    anonymous_client.app.state.users.create("admin@example.com", hash_password("TestPassword123!"), role="admin")
    assert login(anonymous_client, "admin@example.com").status_code == 200
    return anonymous_client
