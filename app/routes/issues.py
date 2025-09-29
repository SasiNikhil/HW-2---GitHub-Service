# app/routes/issues.py
"""
Mikkilineni Sasi Nikhil
"""

from typing import Dict, List, Optional, Union
import hashlib
import json

from fastapi import APIRouter, HTTPException, Response, status, Request

from ..github import GitHubClient
from ..models import IssueIn, IssueOut, IssueUpdate

router = APIRouter()


@router.post("/issues", status_code=status.HTTP_201_CREATED, response_model=IssueOut)
async def create_issue(issue: IssueIn, response: Response):
    gh = GitHubClient()
    try:
        payload = issue.model_dump()
        r = await gh.create_issue(payload)
    finally:
        await gh.close()

    if r.status_code == 201:
        body = r.json()
        response.headers["Location"] = f"/issues/{body['number']}"
        return body

    if r.status_code in (401, 403):
        raise HTTPException(status_code=401, detail=r.text)
    if r.status_code == 422:
        raise HTTPException(status_code=400, detail=r.text)
    raise HTTPException(status_code=502, detail=f"GitHub error {r.status_code}: {r.text}")


# by lordphone
def _generate_cache_key(params: Dict[str, Union[str, int]]) -> str:
    """Generate a cache key from request parameters for ETag storage."""
    # Sort params for consistent key generation
    sorted_params = json.dumps(params, sort_keys=True)
    return hashlib.md5(sorted_params.encode()).hexdigest()


# by lordphone
def _handle_etag_cache(etag_cache: dict, cache_key: str, github_etag: str):
    """Handle ETag caching with size limits."""
    etag_cache[cache_key] = github_etag

    # Limit cache size to prevent memory growth
    if len(etag_cache) > 1000:
        # Remove oldest entries (simple FIFO)
        keys_to_remove = list(etag_cache.keys())[:100]
        for key in keys_to_remove:
            etag_cache.pop(key, None)


# by lordphone
def _check_client_etag_match(client_etag: str, github_etag: str) -> bool:
    """Check if client ETag matches GitHub ETag."""
    if not (client_etag and github_etag):
        return False
    return client_etag.strip('"') == github_etag.strip('"')


# ETag conditional GET implementation by lordphone
@router.get("/issues", response_model=List[IssueOut])
async def list_issues(
    request: Request,
    response: Response,
    state: str = "open",
    labels: Optional[str] = None,  # comma-separated list to filter
    page: int = 1,
    per_page: int = 30,
):
    if per_page > 100:
        per_page = 100

    params: Dict[str, Union[str, int]] = {"state": state, "page": page, "per_page": per_page}
    if labels:
        params["labels"] = labels

    # Generate cache key for this request
    cache_key = _generate_cache_key(params)

    # Check if we have a cached ETag for this request
    etag_cache = getattr(request.app.state, 'etag_cache', {})
    cached_etag = etag_cache.get(cache_key)

    # Check if client sent If-None-Match header
    client_etag = request.headers.get("If-None-Match")

    gh = GitHubClient()
    try:
        # Send If-None-Match to GitHub if we have a cached ETag
        github_headers = {}
        if cached_etag:
            github_headers["If-None-Match"] = cached_etag

        r = await gh.list_issues(params, headers=github_headers)
    finally:
        await gh.close()

    # Handle 304 Not Modified from GitHub
    if r.status_code == 304:
        response.status_code = 304
        if cached_etag:
            response.headers["ETag"] = cached_etag
        return Response(status_code=304)

    if r.status_code != 200:
        if r.status_code in (401, 403):
            raise HTTPException(status_code=401, detail=r.text)
        raise HTTPException(status_code=502, detail=r.text)

    # Extract and cache ETag from GitHub response
    github_etag = r.headers.get("ETag")
    if github_etag:
        _handle_etag_cache(etag_cache, cache_key, github_etag)
        response.headers["ETag"] = github_etag

    # Forward GitHub's Link header for pagination
    link = r.headers.get("Link")
    if link:
        response.headers["Link"] = link

    # Check if client's ETag matches current ETag (client-side conditional GET)
    if _check_client_etag_match(client_etag, github_etag):
        response.status_code = 304
        return Response(status_code=304)

    return r.json()


@router.get("/issues/{number}", response_model=IssueOut)
async def get_issue(number: int):
    gh = GitHubClient()
    try:
        r = await gh.get_issue(number)
    finally:
        await gh.close()

    if r.status_code == 404:
        raise HTTPException(status_code=404, detail="Issue not found")
    if r.status_code != 200:
        raise HTTPException(status_code=502, detail=r.text)
    return r.json()


@router.patch("/issues/{number}", response_model=IssueOut)
async def update_issue(number: int, patch: IssueUpdate):
    gh = GitHubClient()
    try:
        payload = patch.model_dump(exclude_unset=True)
        r = await gh.update_issue(number, payload)
    finally:
        await gh.close()

    if r.status_code == 404:
        raise HTTPException(status_code=404, detail="Issue not found")
    if r.status_code == 422:
        raise HTTPException(status_code=400, detail=r.text)
    if r.status_code != 200:
        raise HTTPException(status_code=502, detail=r.text)

    return r.json()
