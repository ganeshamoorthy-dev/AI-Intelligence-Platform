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
    def __init__(self, repo_url: str, branch_name: str = None, commit_sha: str = None, job_id: int = None):
        self.repo_url = repo_url
        self.branch_name = branch_name
        self.commit_sha = commit_sha
        self.job_id = job_id
        self.base_job_dir = None
        self.temp_dir = None  # This will be the actual code directory

    async def __aenter__(self) -> Path:
        import os
        from app.core.config import settings
        
        # Use WORKSPACE_BASE_DIR from env, fallback to backend/jobs/
        if settings.WORKSPACE_BASE_DIR:
            base_workspace_dir = settings.WORKSPACE_BASE_DIR
        else:
            base_backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
            base_workspace_dir = os.path.join(base_backend_dir, "jobs")
            
        # Create base job directory (e.g., <WORKSPACE_BASE_DIR>/<job_id>)
        self.base_job_dir = os.path.join(base_workspace_dir, str(self.job_id) if self.job_id else "unknown")
        
        # Create 'workspace' (actual code) and 'debug' directories inside it
        self.temp_dir = os.path.join(self.base_job_dir, "workspace")
        debug_dir = os.path.join(self.base_job_dir, "debug")
        
        os.makedirs(self.temp_dir, exist_ok=True)
        os.makedirs(debug_dir, exist_ok=True)
            
        logger.info(f"Created persistent job workspace at {self.base_job_dir}")
        
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
        # Only clean up the actual code (workspace dir) to save disk space.
        # We intentionally leave the debug_dir intact so developers can inspect the LLM outputs!
        if self.temp_dir and Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir, ignore_errors=True)
            logger.info(f"Cleaned up actual code at {self.temp_dir}, preserved debug outputs.")
