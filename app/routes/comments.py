# app/routes/comments.py
"""
Authors:
Mikkilineni Sasi Nikhil
"""

from fastapi import APIRouter, HTTPException, status
import httpx

from ..models import CommentIn, CommentOut
from ..github import GitHubClient

router = APIRouter()

@router.post("/issues/{number}/comments", status_code=status.HTTP_201_CREATED, response_model=CommentOut)
async def create_comment(number: int, body: CommentIn):
    gh = GitHubClient()
    try:
        r = await gh.create_comment(number, body.model_dump())
    except httpx.HTTPError as e:
        # Network/transport layer error talking to GitHub → treat as upstream
        raise HTTPException(status_code=502, detail=f"GitHub request failed: {e}") from e
    finally:
        await gh.close()

    # Happy path
    if r.status_code == 201:
        return r.json()

    # Client-side mappings
    if r.status_code == 404:
        raise HTTPException(status_code=404, detail="Issue not found")
    if r.status_code in (401, 403):
        raise HTTPException(status_code=401, detail=r.text)
    if r.status_code == 422:
        raise HTTPException(status_code=400, detail=r.text)

    # Upstream/server errors from GitHub → map to 502 gateway error
    if 500 <= r.status_code < 600:
        raise HTTPException(status_code=502, detail=r.text)

    # Fallback for anything unexpected
    raise HTTPException(status_code=502, detail=f"GitHub error {r.status_code}: {r.text}")
