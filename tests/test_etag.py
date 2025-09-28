# Test ETag functionality for Conditional GET
# Coded for extra credit implementation by lordphone

import pytest
from fastapi.testclient import TestClient
from app.main import app


# by lordphone
def test_etag_caching_functionality():
    """Test that ETag caching works for GET /issues endpoint."""
    client = TestClient(app)
    
    # Mock GitHub response with ETag
    import respx
    
    with respx.mock(base_url="https://api.github.com") as mock:
        # First request - GitHub returns ETag
        mock.get("/repos/octocat/hello-world/issues").respond(
            status_code=200,
            json=[{
                "number": 1,
                "html_url": "https://github.com/octocat/hello-world/issues/1",
                "state": "open",
                "title": "Test issue",
                "body": "Test body",
                "labels": [],
                "created_at": "2024-01-15T10:30:00Z",
                "updated_at": "2024-01-15T10:30:00Z"
            }],
            headers={"ETag": '"abc123def456"'}
        )
        
        # First request
        response1 = client.get("/issues")
        assert response1.status_code == 200
        assert "ETag" in response1.headers
        etag = response1.headers["ETag"]
        
        # Second request with If-None-Match - GitHub returns 304
        mock.get("/repos/octocat/hello-world/issues").respond(
            status_code=304,
            headers={"ETag": '"abc123def456"'}
        )
        
        response2 = client.get("/issues", headers={"If-None-Match": etag})
        assert response2.status_code == 304
        assert "ETag" in response2.headers


# by lordphone
def test_etag_cache_key_generation():
    """Test that different parameters generate different cache keys."""
    from app.routes.issues import _generate_cache_key
    
    params1 = {"state": "open", "page": 1, "per_page": 30}
    params2 = {"state": "closed", "page": 1, "per_page": 30}
    params3 = {"state": "open", "page": 2, "per_page": 30}
    
    key1 = _generate_cache_key(params1)
    key2 = _generate_cache_key(params2)
    key3 = _generate_cache_key(params3)
    
    # All keys should be different
    assert key1 != key2
    assert key1 != key3
    assert key2 != key3
    
    # Same params should generate same key
    key1_repeat = _generate_cache_key(params1)
    assert key1 == key1_repeat


# by lordphone
def test_etag_cache_size_limit():
    """Test that ETag cache doesn't grow indefinitely."""
    client = TestClient(app)
    
    # Access the app state to check cache size
    etag_cache = getattr(app.state, 'etag_cache', {})
    
    # Fill cache beyond limit (simulate many different requests)
    for i in range(1100):  # More than the 1000 limit
        cache_key = f"test_key_{i}"
        etag_cache[cache_key] = f'"etag_{i}"'
    
    # Trigger cache cleanup by making a request
    import respx
    with respx.mock(base_url="https://api.github.com") as mock:
        mock.get("/repos/octocat/hello-world/issues").respond(
            status_code=200,
            json=[],
            headers={"ETag": '"new_etag"'}
        )
        
        response = client.get("/issues")
        assert response.status_code == 200
    
    # Cache should be cleaned up
    assert len(etag_cache) <= 1000


# by lordphone
def test_client_side_conditional_get():
    """Test client-side conditional GET when client sends If-None-Match."""
    client = TestClient(app)
    
    import respx
    with respx.mock(base_url="https://api.github.com") as mock:
        # GitHub returns fresh content with ETag
        mock.get("/repos/octocat/hello-world/issues").respond(
            status_code=200,
            json=[{
                "number": 1,
                "html_url": "https://github.com/octocat/hello-world/issues/1",
                "state": "open",
                "title": "Test issue",
                "body": "Test body", 
                "labels": [],
                "created_at": "2024-01-15T10:30:00Z",
                "updated_at": "2024-01-15T10:30:00Z"
            }],
            headers={"ETag": '"same_etag"'}
        )
        
        # Client sends matching ETag - should get 304
        response = client.get("/issues", headers={"If-None-Match": '"same_etag"'})
        assert response.status_code == 304
