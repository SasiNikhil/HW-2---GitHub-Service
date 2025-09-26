# tests/unit/test_webhook_more.py
import json
import hmac
import hashlib
from app.config import get_settings

def _sig(body: bytes, secret: str) -> str:
    return "sha256=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()

def test_webhook_valid_ping_204(client):
    secret = get_settings().webhook_secret or "testsecret"
    body = json.dumps({"zen": "hello"}).encode()
    r = client.post(
        "/webhook",
        data=body,
        headers={
            "X-GitHub-Event": "ping",
            "X-GitHub-Delivery": "abc123",
            "X-Hub-Signature-256": _sig(body, secret),
            "Content-Type": "application/json",
        },
    )
    assert r.status_code == 204

def test_webhook_invalid_signature_401(client):
    body = b'{"anything":"tampered"}'
    r = client.post(
        "/webhook",
        data=body,
        headers={
            "X-GitHub-Event": "ping",
            "X-GitHub-Delivery": "abc123",
            "X-Hub-Signature-256": "sha256=deadbeef",
            "Content-Type": "application/json",
        },
    )
    assert r.status_code == 401

def test_webhook_issues_event_204_and_idempotent(client):
    secret = get_settings().webhook_secret or "testsecret"
    payload = {"action": "opened", "issue": {"number": 123}}
    body = json.dumps(payload).encode()
    headers = {
        "X-GitHub-Event": "issues",
        "X-GitHub-Delivery": "delivery-1",
        "X-Hub-Signature-256": _sig(body, secret),
        "Content-Type": "application/json",
    }
    r1 = client.post("/webhook", data=body, headers=headers)
    r2 = client.post("/webhook", data=body, headers=headers)  # same delivery → should be safe/idempotent
    assert r1.status_code == 204
    assert r2.status_code in (204, 200)  # depending on your dedupe strategy

def test_webhook_issue_comment_event_204(client):
    secret = get_settings().webhook_secret or "testsecret"
    payload = {"action": "created", "issue": {"number": 123}, "comment": {"id": 777}}
    body = json.dumps(payload).encode()
    headers = {
        "X-GitHub-Event": "issue_comment",
        "X-GitHub-Delivery": "delivery-2",
        "X-Hub-Signature-256": _sig(body, secret),
        "Content-Type": "application/json",
    }
    r = client.post("/webhook", data=body, headers=headers)
    assert r.status_code == 204

def test_events_endpoint_if_present(client):
    r = client.get("/events")
    if r.status_code == 200:
        assert isinstance(r.json(), list)
    else:
        assert r.status_code == 404
