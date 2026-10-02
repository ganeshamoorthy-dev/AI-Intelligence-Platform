from abc import ABC, abstractmethod
from typing import Dict, Any

class ScmProvider(ABC):
    """
    Abstract base class for all Source Control Management providers (GitHub, GitLab, etc.)
    """
    
    @abstractmethod
    async def parse_pr_url(self, pr_url: str) -> Dict[str, Any]:
        """
        Parses a generic PR URL and retrieves necessary metadata from the SCM API.
        Expected return format:
        {
            "repo_full_name": "owner/repo",
            "pr_number": 123,
            "clone_url": "https://github.com/owner/repo.git",
            "branch_name": "feature-branch",
            "commit_sha": "abcdef..."
        }
        """
        pass

    @abstractmethod
    async def fetch_pr_diff(self, repo_full_name: str, pr_number: int) -> str:
        """
        Fetches the raw file diff string for the given Pull Request.
        """
        pass

    @abstractmethod
    async def publish_review(self, repo_full_name: str, pr_number: int, findings: list) -> None:
        """
        Publishes the AI findings as inline comments on the Pull Request.
        """
        pass

    @abstractmethod
    async def commit_fix(self, repo_full_name: str, branch_name: str, file_path: str, new_content: str, message: str) -> None:
        """
        Commits a fix directly to the Pull Request branch.
        """
        pass
