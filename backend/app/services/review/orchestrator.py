import logging
from datetime import datetime, timezone
from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models import ReviewRun, ReviewFinding
from app.services.workspace.manager import WorkspaceManager
from app.services.graphify.parser import GraphifyService
from app.services.llm.inference import LlmService
from app.services.scm.base import ScmProvider
from app.services.scm.github import GithubScmService
from app.services.graph.graph_traversal_service import GraphTraversalService, GraphTraversalConfig
from app.core.config import settings

logger = logging.getLogger(__name__)

class ReviewService:
    """
    Orchestrates the PR review pipeline.
    """
    def __init__(self, session: AsyncSession):
        self.session = session
        self.graphify = GraphifyService()
        self.graph_traversal = GraphTraversalService()
        self.llm = LlmService(model_name=settings.LLM_MODEL)

    async def execute_review(self, job: ReviewRun):
        """
        Runs the intelligence pipeline for a background job and publishes to GitHub.
        """
        repo_url = job.pull_request.project.repository_url
        if job.pull_request.project.scm_account:
            github_token = job.pull_request.project.scm_account.access_token
        else:
            github_token = job.pull_request.project.webhook_secret or settings.GITHUB_WEBHOOK_SECRET
        
        scm = GithubScmService(token=github_token)
        repo_full_name = repo_url.replace("https://github.com/", "").replace(".git", "")
        pr_number = job.pull_request.pr_number
        # Fetch Platform Settings for API Keys and Custom Instructions
        from sqlalchemy.future import select
        from app.db.models import PlatformSettings
        result = await self.session.execute(select(PlatformSettings).limit(1))
        platform_settings = result.scalars().first()
        
        # Dynamically switch LLM model for this specific job
        model_to_use = job.llm_model if job.llm_model else (platform_settings.default_llm_model if platform_settings else settings.LLM_MODEL)
        
        self.llm = LlmService(model_name=model_to_use, platform_settings=platform_settings)

        # 1. Pipeline Execution
        review_output, impact_graph, diff_data, input_tokens, output_tokens = await self._run_pipeline(
            repo_url=job.pull_request.project.repository_url,
            branch_name=getattr(job, "branch_name", None),
            commit_sha=job.commit_sha,
            repo_full_name=repo_full_name,
            pr_number=pr_number,
            scm=scm
        )
        
        job.status = "completed"
        job.blast_radius_summary = review_output.blast_radius_summary
        job.impact_graph_data = impact_graph
        job.diff_data = diff_data
        job.input_tokens = input_tokens
        job.output_tokens = output_tokens
        job.total_tokens = input_tokens + output_tokens
        
        # Save Findings
        saved_findings = []
        for item in review_output.findings:
            finding = ReviewFinding(
                review_run_id=job.id,
                file_path=item.file_path,
                line_number=item.line_number,
                severity=item.severity,
                category=item.category,
                description=item.description,
                suggested_fix=item.suggested_fix
            )
            self.session.add(finding)
            saved_findings.append(finding)
        
        await self.session.commit()
        logger.info(f"Successfully processed job {job.id} and saved findings.")
        
        # 3. Post to GitHub (Non-blocking)
        try:
            from app.services.github.publisher import GithubPublisherService
            github_publisher = GithubPublisherService(github_token=github_token)
            await github_publisher.post_pr_summary(repo_full_name, pr_number, saved_findings)
            return True
        except Exception as e:
            logger.error(f"Failed to post findings to GitHub, but review was successfully saved to DB: {e}")
            return False

    async def execute_sync(self, job: Any, scm: ScmProvider) -> List[Dict[str, Any]]:
        """
        Runs the intelligence pipeline instantly without background workers or DB persistence.
        Returns the findings directly to the caller.
        """
        repo_full_name = job.pull_request.project.repository_url.replace("https://github.com/", "").replace(".git", "")
        
        review_output, _, _ = await self._run_pipeline(
            repo_url=job.pull_request.project.repository_url,
            branch_name=getattr(job, "branch_name", None),
            commit_sha=job.commit_sha,
            repo_full_name=repo_full_name,
            pr_number=job.pull_request.pr_number,
            scm=scm
        )
        
        return [f.model_dump() for f in review_output.findings]

    async def _run_pipeline(self, repo_url: str, branch_name: str, commit_sha: str, repo_full_name: str, pr_number: int, scm: ScmProvider):
        """
        Core logic shared between async and sync execution flows.
        """
        logger.info(f"Starting core review pipeline for {repo_full_name}#{pr_number}")
        
        # 1. Ephemeral Workspace Setup
        async with WorkspaceManager(repo_url=repo_url, branch_name=branch_name, commit_sha=commit_sha) as workspace_path:
            # 2. Extract AST
            ast_data = await self.graphify.parse_workspace(workspace_path)
            
            # 3. Fetch Real Diff from SCM Provider
            diff_data = await scm.fetch_pr_diff(repo_full_name, pr_number)
            
            # 4. Extract modified files and line numbers from diff
            from app.services.graph.changed_symbol_service import ChangedSymbolService
            symbol_service = ChangedSymbolService()
            changed_lines = symbol_service.parse_diff(diff_data)
            modified_files = set(changed_lines.keys())
                    
            # 5. Generate subgraph
            logger.info("Extracting configurable subgraph via GraphTraversalService")
            config = GraphTraversalConfig(mode="symbol", depth=1, direction="both")
            subgraph = self.graph_traversal.extract_subgraph(ast_data, modified_files, config, changed_lines)
            
            # 6. Extract actual source code for subgraph nodes
            logger.info("Extracting source snippets from workspace")
            from app.services.graph.source_context_service import SourceContextService
            source_service = SourceContextService()
            source_snippets = source_service.extract_snippets(subgraph, str(workspace_path))
            
            # Attach source snippets to the subgraph so they are saved to the DB and sent to the frontend UI
            subgraph["source_snippets"] = source_snippets
            
            # 7. LLM Inference
            logger.info("Starting LLM analysis")
            review_output, impact_graph, input_tokens, output_tokens = await self.llm.analyze_ast(subgraph, diff_data, source_snippets)
            
            # 8. Post-process line numbers
            # If the LLM hallucinates a line number or comments on a line outside the diff, 
            # GitHub will reject the inline comment with a 422. We nullify them here so they fallback to general comments.
            for finding in review_output.findings:
                if finding.file_path in changed_lines:
                    if finding.line_number not in changed_lines[finding.file_path]:
                        finding.line_number = None
                else:
                    finding.line_number = None
            
            return review_output, impact_graph, diff_data, input_tokens, output_tokens
