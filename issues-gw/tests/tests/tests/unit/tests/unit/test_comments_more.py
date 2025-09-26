# tests/unit/test_comments_more.py
from app.config import get_settings
S = get_settings()
OWNER = S.github_owner or "octocat"
REPO  = S.github_repo  or "hello-world"

def test_create_comment_unauthorized_maps_to_401(client, respx_mocked):
    respx_mocked.post(f"/repos/{OWNER}/{REPO}/issues/5/comments").respond(
        status_code=401, json={"message": "Bad credentials"}
    )
    r = client.post("/issues/5/comments", json={"body": "hey"})
    assert r.status_code == 401

def test_create_comment_502_on_upstream_error(client, respx_mocked):
    respx_mocked.post(f"/repos/{OWNER}/{REPO}/issues/6/comments").respond(
        status_code=500, json={"message": "oops"}
    )
    r = client.post("/issues/6/comments", json={"body": "hey"})
    assert r.status_code == 502
