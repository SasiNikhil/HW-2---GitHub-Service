import httpx
from .config import get_settings

BASE = 'https://api.github.com'
HEADERS = {'Accept': 'application/vnd.github+json'}

class GitHubClient:
    def __init__(self):
        s = get_settings()
        self.client = httpx.AsyncClient(
            headers={**HEADERS, 'Authorization': f'Bearer {s.github_token}'}, timeout=30
        )
        self.owner = s.github_owner
        self.repo = s.github_repo

    def _repo(self) -> str:
        return f"{BASE}/repos/{self.owner}/{self.repo}"

    async def create_issue(self, payload: dict): return await self.client.post(f'{self._repo()}/issues', json=payload)
    async def list_issues(self, params: dict): return await self.client.get(f'{self._repo()}/issues', params=params)
    async def get_issue(self, number: int): return await self.client.get(f'{self._repo()}/issues/{number}')
    async def update_issue(self, number: int, payload: dict): return await self.client.patch(f'{self._repo()}/issues/{number}', json=payload)
    async def create_comment(self, number: int, payload: dict): return await self.client.post(f'{self._repo()}/issues/{number}/comments', json=payload)
    async def close(self): await self.client.aclose()
