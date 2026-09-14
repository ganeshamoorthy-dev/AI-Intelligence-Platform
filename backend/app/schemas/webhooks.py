from pydantic import BaseModel
from typing import Optional, List

class GitHubWebhookPayload(BaseModel):
    action: str
    number: Optional[int] = None
    pull_request: Optional[dict] = None
    repository: Optional[dict] = None

class JobCreate(BaseModel):
    pr_number: int
    repo_url: str
    repo_full_name: str
    head_sha: str
    base_sha: str
    author: str
    title: str
