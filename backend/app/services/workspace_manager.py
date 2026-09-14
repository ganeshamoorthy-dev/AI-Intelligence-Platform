import tempfile
import shutil
import subprocess
import os
import logging
from contextlib import contextmanager

logger = logging.getLogger(__name__)

class WorkspaceManager:
    def __init__(self, run_id: str, repo_url: str, head_sha: str, base_sha: str):
        self.run_id = run_id
        self.repo_url = repo_url
        self.head_sha = head_sha
        self.base_sha = base_sha
        self.workspace_dir = None
        
    def setup(self):
        """Creates the temporary directory and clones the repository."""
        self.workspace_dir = tempfile.mkdtemp(prefix=f"workspace_{self.run_id}_")
        logger.info(f"Created ephemeral workspace at {self.workspace_dir}")
        
        try:
            # We do a shallow clone of the base branch/commit if possible, 
            # then fetch the head commit to get the diff.
            # For simplicity in this skeleton, we just clone the repo.
            clone_cmd = ["git", "clone", "--depth", "1", self.repo_url, self.workspace_dir]
            subprocess.run(clone_cmd, check=True, capture_output=True, text=True)
            logger.info("Successfully cloned repository")
            
            # Fetch the specific SHA we need to review
            # fetch_cmd = ["git", "-C", self.workspace_dir, "fetch", "origin", self.head_sha]
            # subprocess.run(fetch_cmd, check=True)
            # checkout_cmd = ["git", "-C", self.workspace_dir, "checkout", "FETCH_HEAD"]
            # subprocess.run(checkout_cmd, check=True)
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Git operation failed: {e.stderr}")
            self.cleanup()
            raise
            
        return self.workspace_dir
        
    def cleanup(self):
        """Guaranteed cleanup of the ephemeral directory."""
        if self.workspace_dir and os.path.exists(self.workspace_dir):
            try:
                shutil.rmtree(self.workspace_dir)
                logger.info(f"Purged ephemeral workspace {self.workspace_dir}")
            except Exception as e:
                logger.error(f"Failed to purge workspace {self.workspace_dir}: {e}")
            finally:
                self.workspace_dir = None

@contextmanager
def ephemeral_workspace(run_id: str, repo_url: str, head_sha: str, base_sha: str):
    """Context manager for safe usage of workspaces."""
    manager = WorkspaceManager(run_id, repo_url, head_sha, base_sha)
    try:
        workspace_path = manager.setup()
        yield workspace_path
    finally:
        manager.cleanup()
