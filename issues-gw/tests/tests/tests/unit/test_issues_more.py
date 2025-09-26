# tests/unit/test_issues_more.py
from app.config import get_settings

S = get_settings()
OWNER = S.github_owner or "octocat"
REPO  = S.github_repo  or "hello-world"

def test_create_issue_422_maps_to_400(client, respx_mocked):
    respx_mocked.post(f"/repos/{OWNER}/{REPO}/issues").respond(
        status_code=422, json={"message": "Validation Failed"}
    )
    r = client.post("/issues", json={"title": ""})  # invalid title
    assert r.status_code == 400

def test_list_issues_with_labels_and_cap_per_page(client, respx_mocked):
    respx_mocked.get(f"/repos/{OWNER}/{REPO}/issues").respond(status_code=200, json=[])
    # ask for >100 per_page → server should cap at 100 (still returns 200 OK)
    r = client.get("/issues?state=open&labels=bug,ui&per_page=500&page=1")
    assert r.status_code == 200
    assert r.json() == []

def test_get_issue_502_on_upstream_error(client, respx_mocked):
    respx_mocked.get(f"/repos/{OWNER}/{REPO}/issues/77").respond(status_code=500, json={"message": "oops"})
    r = client.get("/issues/77")
    assert r.status_code == 502

def test_patch_issue_502_on_upstream_error(client, respx_mocked):
    respx_mocked.patch(f"/repos/{OWNER}/{REPO}/issues/88").respond(status_code=500, json={"message": "oops"})
    r = client.patch("/issues/88", json={"state": "closed"})
    assert r.status_code == 502
