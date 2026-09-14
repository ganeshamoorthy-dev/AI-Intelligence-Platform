import tempfile
import subprocess
import shutil
from pathlib import Path
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)

class WorkspaceManager:
    """
    Manages ephemeral Git workspaces for PR reviews.
    Uses async context managers for guaranteed cleanup.
    """
    def __init__(self, repo_url: str, branch_name: str = None, commit_sha: str = None):
        self.repo_url = repo_url
        self.branch_name = branch_name
        self.commit_sha = commit_sha
        self.temp_dir = None

    async def __aenter__(self) -> Path:
        if settings.WORKSPACE_BASE_DIR:
            base_dir = Path(settings.WORKSPACE_BASE_DIR)
            base_dir.mkdir(parents=True, exist_ok=True)
            self.temp_dir = tempfile.mkdtemp(prefix="ai_reviewer_", dir=str(base_dir))
        else:
            self.temp_dir = tempfile.mkdtemp(prefix="ai_reviewer_")
            
        logger.info(f"Created temporary workspace at {self.temp_dir}")
        
        try:
            # Clone specific branch to optimize fetch time
            clone_cmd = ["git", "clone"]
            if self.branch_name:
                clone_cmd.extend(["--branch", self.branch_name, "--single-branch"])
            clone_cmd.extend([self.repo_url, "."])
            
            logger.info(f"Cloning repo: {' '.join(clone_cmd)}")
            subprocess.run(
                clone_cmd,
                cwd=self.temp_dir,
                check=True,
                capture_output=True
            )
            
            # Checkout specific commit if provided
            if self.commit_sha:
                subprocess.run(
                    ["git", "checkout", self.commit_sha],
                    cwd=self.temp_dir,
                    check=True,
                    capture_output=True
                )
            
            return Path(self.temp_dir)
        except subprocess.CalledProcessError as e:
            logger.error(f"Git operation failed: {e.stderr.decode()}")
            await self._cleanup()
            raise Exception("Failed to setup workspace") from e

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self._cleanup()
        
    async def _cleanup(self):
        if self.temp_dir and Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir, ignore_errors=True)
            logger.info(f"Cleaned up workspace at {self.temp_dir}")
