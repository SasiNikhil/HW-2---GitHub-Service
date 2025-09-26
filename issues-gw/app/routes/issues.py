# app/routes/issues.py
"""
Owner: (your name/email)
Summary: Issue CRUD endpoints for the GitHub Issues Gateway.
"""

from typing import Dict, List, Optional, Union

from fastapi import APIRouter, HTTPException, Response, status

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


@router.get("/issues", response_model=List[IssueOut])
async def list_issues(
    state: str = "open",
    labels: Optional[str] = None,  # comma-separated list to filter
    page: int = 1,
    per_page: int = 30,
    response: Response = None,  # FastAPI injects this
):
    if per_page > 100:
        per_page = 100

    params: Dict[str, Union[str, int]] = {"state": state, "page": page, "per_page": per_page}
    if labels:
        params["labels"] = labels

    gh = GitHubClient()
    try:
        r = await gh.list_issues(params)
    finally:
        await gh.close()

    if r.status_code != 200:
        if r.status_code in (401, 403):
            raise HTTPException(status_code=401, detail=r.text)
        raise HTTPException(status_code=502, detail=r.text)

    link = r.headers.get("Link")
    if link and response is not None:
        response.headers["Link"] = link

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
