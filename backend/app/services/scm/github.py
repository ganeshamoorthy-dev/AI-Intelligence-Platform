import httpx
import re
import logging
from typing import Dict, Any
from app.services.scm.base import ScmProvider

logger = logging.getLogger(__name__)

class GithubScmService(ScmProvider):
    def __init__(self, token: str = None):
        self.token = token
        self.base_url = "https://api.github.com"
        self.headers = {
            "Accept": "application/vnd.github.v3+json",
            "X-GitHub-Api-Version": "2022-11-28"
        }
        if self.token:
            self.headers["Authorization"] = f"Bearer {self.token}"

    async def parse_pr_url(self, pr_url: str) -> Dict[str, Any]:
        """
        Extracts owner, repo, and PR number from a standard GitHub PR URL.
        e.g., https://github.com/testuser/test-repo/pull/1
        """
        match = re.search(r"github\.com/([^/]+)/([^/]+)/pull/(\d+)", pr_url)
        if not match:
            raise ValueError(f"Invalid GitHub PR URL format: {pr_url}")
            
        owner, repo, pr_number = match.groups()
        repo_full_name = f"{owner}/{repo}"
        
        url = f"{self.base_url}/repos/{repo_full_name}/pulls/{pr_number}"
        logger.info(f"Fetching PR metadata from GitHub API: {url}")
        
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, headers=self.headers)
            if resp.status_code == 401 and "Authorization" in self.headers:
                logger.warning("GitHub token rejected (401). Retrying without token for public access.")
                headers_no_auth = {k: v for k, v in self.headers.items() if k != "Authorization"}
                resp = await client.get(url, headers=headers_no_auth)
                
            resp.raise_for_status()
            data = resp.json()
            
            return {
                "repo_full_name": repo_full_name,
                "pr_number": int(pr_number),
                "clone_url": data["head"]["repo"]["clone_url"],
                "branch_name": data["head"]["ref"],
                "commit_sha": data["head"]["sha"],
                "base_sha": data["base"]["sha"],
                "title": data.get("title", f"PR #{pr_number}"),
                "author": data.get("user", {}).get("login", "unknown")
            }

    async def fetch_pr_diff(self, repo_full_name: str, pr_number: int) -> str:
        url = f"{self.base_url}/repos/{repo_full_name}/pulls/{pr_number}"
        
        # Override accept header to get the raw diff
        diff_headers = self.headers.copy()
        diff_headers["Accept"] = "application/vnd.github.v3.diff"
        
        logger.info(f"Fetching raw PR diff for {repo_full_name}#{pr_number}")
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, headers=diff_headers)
            if resp.status_code == 401 and "Authorization" in diff_headers:
                logger.warning("GitHub token rejected (401) for diff fetch. Retrying without token for public access.")
                headers_no_auth = {k: v for k, v in diff_headers.items() if k != "Authorization"}
                resp = await client.get(url, headers=headers_no_auth)
                
            resp.raise_for_status()
            return resp.text

    async def register_webhook(self, repo_full_name: str, secret: str) -> dict:
        """
        Registers a webhook on the given GitHub repository.
        Requires admin privileges on the repo.
        """
        from app.core.config import settings
        url = f"{self.base_url}/repos/{repo_full_name}/hooks"
        
        # Determine the public URL of our platform to receive webhooks
        # (For local dev, this might need to be an ngrok URL in settings)
        webhook_target_url = getattr(settings, "WEBHOOK_URL", f"https://api.example.com/api/v1/webhooks/github")
        
        payload = {
            "name": "web",
            "active": True,
            "events": ["pull_request"],
            "config": {
                "url": webhook_target_url,
                "content_type": "json",
                "insecure_ssl": "0",
                "secret": secret
            }
        }
        
        logger.info(f"Registering webhook for {repo_full_name} -> {webhook_target_url}")
        async with httpx.AsyncClient() as client:
            resp = await client.post(url, headers=self.headers, json=payload)
            resp.raise_for_status()
            return resp.json()
