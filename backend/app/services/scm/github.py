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

    async def publish_review(self, repo_full_name: str, pr_number: int, findings: list) -> None:
        """
        Publishes the AI findings as a formal Review on the GitHub PR, 
        adding inline comments for specific lines and a general summary body.
        """
        if not self.token:
            logger.warning("No GitHub token provided. Cannot publish review. Skipping.")
            return
            
        if not findings:
            logger.info("No findings to publish.")
            return

        url = f"{self.base_url}/repos/{repo_full_name}/pulls/{pr_number}/reviews"
        
        # Format the general body
        high_sev = sum(1 for f in findings if f.severity in ["high", "critical"])
        body = f"### 🤖 Antigravity AI Code Review\n\nI have analyzed this Pull Request and found **{len(findings)} issues** ({high_sev} high/critical severity).\n\n"
        
        comments = []
        for f in findings:
            if not f.line_number or f.line_number <= 0:
                # Fallback to general PR comment if we don't have a valid line number in the diff
                body += f"- **{f.severity.upper()}** ({f.file_path}): {f.description}\n"
                if hasattr(f, 'why_it_matters') and f.why_it_matters:
                    body += f"  - *Why it matters*: {f.why_it_matters}\n"
            else:
                comment_body = f"**[{f.severity.upper()}] {f.category}**\n\n{f.description}\n"
                if hasattr(f, 'why_it_matters') and f.why_it_matters:
                    comment_body += f"\n**Why it matters:**\n{f.why_it_matters}\n"
                if f.suggested_fix:
                    comment_body += f"\n**Suggested Fix:**\n```\n{f.suggested_fix}\n```\n"
                
                comments.append({
                    "path": f.file_path,
                    "line": f.line_number,
                    "body": comment_body
                })

        payload = {
            "body": body,
            "event": "COMMENT",  # Can be APPROVE, REQUEST_CHANGES, or COMMENT
            "comments": comments
        }
        
        logger.info(f"Publishing GitHub Review to {repo_full_name}#{pr_number} with {len(comments)} inline comments")
        
        async with httpx.AsyncClient() as client:
            # FIX: Check for and delete any existing 'PENDING' reviews from our bot 
            # to prevent the "User can only have one pending review" 422 error.
            try:
                list_reviews_url = f"{self.base_url}/repos/{repo_full_name}/pulls/{pr_number}/reviews"
                list_resp = await client.get(list_reviews_url, headers=self.headers)
                if list_resp.status_code == 200:
                    for review in list_resp.json():
                        if review.get("state") == "PENDING":
                            logger.info(f"Deleting stale PENDING review ({review['id']}) to make room for new review.")
                            await client.delete(f"{list_reviews_url}/{review['id']}", headers=self.headers)
            except Exception as e:
                logger.warning(f"Failed to clear pending reviews: {e}")

            resp = await client.post(url, headers=self.headers, json=payload)
            if resp.status_code == 422:
                # Parse the error to give a more accurate log
                error_data = resp.json()
                logger.error(f"GitHub rejected inline comments (422 Unprocessable Entity). Response: {error_data}")
                # Fallback: post a standard issue comment instead of a review with inline lines
                issue_url = f"{self.base_url}/repos/{repo_full_name}/issues/{pr_number}/comments"
                fallback_payload = {"body": body + "\n\n*Note: Inline comments failed to attach (GitHub 422 Error).*"}
                await client.post(issue_url, headers=self.headers, json=fallback_payload)
            else:
                resp.raise_for_status()

    async def commit_fix(self, repo_full_name: str, branch_name: str, file_path: str, new_content: str, message: str) -> None:
        """
        Commits a file change directly to the PR branch using the GitHub Contents API.
        """
        import base64
        
        if not self.token:
            raise ValueError("GitHub token required to push commits.")
            
        url = f"{self.base_url}/repos/{repo_full_name}/contents/{file_path}"
        
        async with httpx.AsyncClient() as client:
            # 1. Get current file SHA
            logger.info(f"Fetching current file SHA for {file_path} on branch {branch_name}")
            resp = await client.get(url, headers=self.headers, params={"ref": branch_name})
            
            if resp.status_code == 404:
                file_sha = None # It's a new file
            else:
                resp.raise_for_status()
                file_sha = resp.json()["sha"]
                
            # 2. Push new content
            encoded_content = base64.b64encode(new_content.encode("utf-8")).decode("utf-8")
            payload = {
                "message": f"🤖 Antigravity AI: {message}",
                "content": encoded_content,
                "branch": branch_name
            }
            if file_sha:
                payload["sha"] = file_sha
                
            logger.info(f"Pushing commit to {repo_full_name} ({branch_name}) for {file_path}")
            put_resp = await client.put(url, headers=self.headers, json=payload)
            put_resp.raise_for_status()
