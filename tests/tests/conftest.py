# tests/conftest.py
# code by Nikhil Manam
import os
import sys
import json
import hmac
import hashlib
import pathlib
import pytest
import respx
from fastapi.testclient import TestClient

# Put project root (folder that contains "app/") on sys.path
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))

from app.main import app  # noqa: E402
from app.config import get_settings  # noqa: E402

# Safe defaults (mocked tests won't hit real GitHub)
os.environ.setdefault("GITHUB_TOKEN", "test_token")
os.environ.setdefault("GITHUB_OWNER", "octocat")
os.environ.setdefault("GITHUB_REPO", "hello-world")
os.environ.setdefault("WEBHOOK_SECRET", "testsecret")
os.environ.setdefault("PORT", "8080")

def _seed_app_state():
    # attach settings
    if not hasattr(app.state, "settings") or app.state.settings is None:
        app.state.settings = get_settings()
    # minimal in-memory store for webhook events (if your code uses it)
    if not hasattr(app.state, "events") or app.state.events is None:
        app.state.events = []

_seed_app_state()

@pytest.fixture(scope="session")
def client() -> TestClient:
    # use context manager so lifespan/startup runs if defined
    with TestClient(app) as c:
        _seed_app_state()
        yield c

@pytest.fixture
def settings():
    return get_settings()

@pytest.fixture
def respx_mocked():
    with respx.mock(base_url="https://api.github.com") as mock:
        yield mock

def sign(body: bytes, secret: str) -> str:
    return "sha256=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()

@pytest.fixture
def webhook_ping_headers(settings):
    body = json.dumps({"zen": "Keep it logically awesome"}).encode()
    sig = sign(body, settings.webhook_secret or "testsecret")
    return {
        "X-GitHub-Event": "ping",
        "X-GitHub-Delivery": "test-delivery-id",
        "X-Hub-Signature-256": sig,
        "Content-Type": "application/json",
    }, body
