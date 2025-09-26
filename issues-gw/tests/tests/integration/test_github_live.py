import os, pytest, httpx
pytestmark = pytest.mark.skipif(os.getenv("LIVE") != "1", reason="Set LIVE=1 to run live tests")

def test_live_create_and_get_issue():
    base = f"http://127.0.0.1:{os.getenv('PORT','8080')}"
    issue = {"title": "Live test issue", "body": "created by pytest"}
    r = httpx.post(f"{base}/issues", json=issue, timeout=30.0)
    assert r.status_code == 201
    num = r.json()["number"]

    r = httpx.get(f"{base}/issues/{num}", timeout=30.0)
    assert r.status_code == 200
    assert r.json()["number"] == num
