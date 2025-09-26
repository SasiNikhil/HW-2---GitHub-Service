from pydantic import BaseModel
from typing import List, Optional, Dict, Any

class Label(BaseModel):
    name: str

class IssueIn(BaseModel):
    title: str
    body: Optional[str] = None
    labels: Optional[List[str]] = None

class IssueOut(BaseModel):
    number: int
    html_url: str
    state: str
    title: str
    body: Optional[str]
    labels: List[Label] = []
    created_at: str
    updated_at: str

class IssueUpdate(BaseModel):
    title: Optional[str] = None
    body: Optional[str] = None
    state: Optional[str] = None

class CommentIn(BaseModel):
    body: str

class CommentOut(BaseModel):
    id: int
    body: str
    user: Dict[str, Any]
    created_at: str
    html_url: str
