# app/config.py
from pydantic import BaseModel, Field
import os
from pathlib import Path

# Load .env from the project root: issues-gw/.env
try:
    from dotenv import load_dotenv
    ROOT = Path(__file__).resolve().parents[1]   # .../issues-gw
    load_dotenv(dotenv_path=ROOT / ".env", override=True)
except Exception:
    pass

class Settings(BaseModel):
    github_token: str = Field(default_factory=lambda: os.getenv('GITHUB_TOKEN', ''))
    github_owner: str = Field(default_factory=lambda: os.getenv('GITHUB_OWNER', ''))
    github_repo: str = Field(default_factory=lambda: os.getenv('GITHUB_REPO', ''))
    webhook_secret: str = Field(default_factory=lambda: os.getenv('WEBHOOK_SECRET', ''))
    port: int = Field(default_factory=lambda: int(os.getenv('PORT', '8080')))

def get_settings() -> Settings:
    s = Settings()
    print(">>> Loaded settings:", {k: ('***' if 'token' in k else v) for k, v in s.model_dump().items()})
    return s