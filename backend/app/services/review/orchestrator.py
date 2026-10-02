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
        project_settings = {
            "ignore_paths": job.pull_request.project.ignore_paths or "",
            "review_mode": job.pull_request.project.review_mode or "standard",
            "focus_categories": job.pull_request.project.focus_categories or ""
        }
        
        try:
            review_output, impact_graph, diff_data, input_tokens, output_tokens, stats = await self._run_pipeline(
                repo_url=job.pull_request.project.repository_url,
                branch_name=getattr(job, "branch_name", None),
                commit_sha=job.commit_sha,
                repo_full_name=repo_full_name,
                pr_number=pr_number,
                scm=scm,
                project_settings=project_settings,
                job_id=str(job.id)
            )
        except Exception as e:
            logger.error(f"Pipeline execution failed for job {job.id}: {e}")
            job.status = "failed"
            job.completed_at = datetime.now(timezone.utc)
            await self.session.commit()
            return False
        
        job.status = "completed"
        job.completed_at = datetime.now(timezone.utc)
        job.latency_ms = int((job.completed_at - job.started_at).total_seconds() * 1000)
        job.impact_graph_data = impact_graph
        job.diff_data = diff_data
        job.input_tokens = input_tokens
        job.output_tokens = output_tokens
        job.total_tokens = input_tokens + output_tokens
        
        job.changed_files_count = stats.get("changed_files_count", 0)
        job.changed_lines_count = stats.get("changed_lines_count", 0)
        job.changed_symbols_count = stats.get("changed_symbols_count", 0)
        job.affected_files_count = stats.get("affected_files_count", 0)
        job.affected_symbols_count = stats.get("affected_symbols_count", 0)
        job.related_tests_count = stats.get("related_tests_count", 0)
        job.risk_level = stats.get("risk_level", "medium")
        job.findings_count = len(review_output.findings)
        job.high_severity_findings_count = sum(1 for f in review_output.findings if getattr(f, "severity", "") in ["high", "critical"])
        
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
                suggested_fix=item.suggested_fix,
                evidence=item.evidence,
                why_it_matters=item.why_it_matters,
                confidence=item.confidence
            )
            self.session.add(finding)
            saved_findings.append(finding)
        
        await self.session.commit()
        logger.info(f"Successfully processed job {job.id} and saved findings.")
        
        # 3. Post to GitHub (Non-blocking)
        try:
            await scm.publish_review(repo_full_name, pr_number, saved_findings)
            return True
        except Exception as e:
            logger.error(f"Failed to publish review to GitHub: {e}")
            job.status = "completed_publish_failed"
            await self.session.commit()
            return False

    async def execute_sync(self, job: Any, scm: ScmProvider) -> List[Dict[str, Any]]:
        """
        Runs the intelligence pipeline instantly without background workers or DB persistence.
        Returns the findings directly to the caller.
        """
        repo_full_name = job.pull_request.project.repository_url.replace("https://github.com/", "").replace(".git", "")
        
        project_settings = {
            "ignore_paths": job.pull_request.project.ignore_paths or "",
            "review_mode": job.pull_request.project.review_mode or "standard",
            "focus_categories": job.pull_request.project.focus_categories or ""
        }
        
        review_output, _, _, _, _, _ = await self._run_pipeline(
            repo_url=job.pull_request.project.repository_url,
            branch_name=getattr(job, "branch_name", None),
            commit_sha=job.commit_sha,
            repo_full_name=repo_full_name,
            pr_number=job.pull_request.pr_number,
            scm=scm,
            project_settings=project_settings
        )
        
        return [f.model_dump() for f in review_output.findings]

    async def _run_pipeline(self, repo_url: str, branch_name: str, commit_sha: str, repo_full_name: str, pr_number: int, scm: ScmProvider, project_settings: dict = None, job_id: str = None):
        """
        Core logic shared between async and sync execution flows.
        """
        async def emit_status(msg: str, stage: str = None):
            logger.info(msg)
            if job_id and stage:
                from sqlalchemy.future import select
                from app.db.models import ReviewRun
                result = await self.session.execute(select(ReviewRun).where(ReviewRun.id == int(job_id)))
                job_record = result.scalars().first()
                if job_record:
                    job_record.status = stage
                    await self.session.commit()

        await emit_status(f"Starting core review pipeline for {repo_full_name}#{pr_number}")
        
        # 1. Ephemeral Workspace Setup
        await emit_status("Cloning workspace into ephemeral directory...", stage="Cloning Workspace")
        async with WorkspaceManager(repo_url=repo_url, branch_name=branch_name, commit_sha=commit_sha, job_id=job_id) as workspace_path:
            # 2. Extract AST
            await emit_status("Parsing abstract syntax tree (AST)...", stage="Parsing AST")
            ast_data = await self.graphify.parse_workspace(workspace_path)
            
            # 3. Fetch Real Diff from SCM Provider
            await emit_status("Fetching git diff...", stage="Fetching Diff")
            diff_data = await scm.fetch_pr_diff(repo_full_name, pr_number)
            
            # 4. Extract modified files and line numbers from diff using new ChangeAnalyzer
            await emit_status("Identifying changed semantic symbols...", stage="Analyzing Changes")
            from app.services.change.change_analyzer import ChangeAnalyzer
            change_analyzer = ChangeAnalyzer()
            change_analysis = change_analyzer.analyze(diff_data, ast_data)
            
            # Phase 8: Apply Path Exclusions
            ignore_paths = []
            if project_settings and project_settings.get("ignore_paths"):
                ignore_paths = [p.strip() for p in project_settings["ignore_paths"].split(",") if p.strip()]
                
            filtered_changed_files = []
            for f in change_analysis.changed_files:
                should_ignore = False
                for ignore_pattern in ignore_paths:
                    if ignore_pattern in f.file_path:
                        should_ignore = True
                        break
                if not should_ignore:
                    filtered_changed_files.append(f)
                    
            change_analysis.changed_files = filtered_changed_files
            
            # Convert change analysis back to legacy dict format for GraphTraversalService
            changed_lines = {
                f.file_path: set(f.changed_lines) for f in change_analysis.changed_files
            }
            modified_files = set(changed_lines.keys())
                    
            # 5. Generate subgraph
            await emit_status("Extracting impact subgraph (Blast Radius)...", stage="Calculating Blast Radius")
            config = GraphTraversalConfig(mode="symbol", depth=1, direction="both")
            subgraph = self.graph_traversal.extract_subgraph(ast_data, modified_files, config, changed_lines)
            
            # Attach structured changes to the subgraph so they are returned and persisted
            subgraph["changed_symbols"] = []
            for file_analysis in change_analysis.changed_files:
                for symbol in file_analysis.changed_symbols:
                    subgraph["changed_symbols"].append(symbol.model_dump())
            
            # 6. Extract actual source code for subgraph nodes
            await emit_status("Reading source code snippets for LLM context...", stage="Gathering Context")
            from app.services.graph.source_context_service import SourceContextService
            source_service = SourceContextService()
            source_snippets = source_service.extract_snippets(subgraph, str(workspace_path))
            
            # Attach source snippets to the subgraph so they are saved to the DB and sent to the frontend UI
            subgraph["source_snippets"] = source_snippets
            
            # Phase 3: Build Context using Context Engine
            await emit_status("Classifying dependencies and structuring context...", stage="Structuring Context")
            from app.services.context.context_engine import ContextEngine
            context_engine = ContextEngine()
            review_context = context_engine.build_context(subgraph, subgraph["changed_symbols"])
            context_markdown = context_engine.serialize(review_context)
            
            # Phase 6: Expose context to frontend
            subgraph["review_context"] = review_context.model_dump()
            
            # 7. LLM Inference
            await emit_status("Sending context to AI reviewer for analysis...", stage="AI Analysis in Progress")
            review_output, impact_graph, input_tokens, output_tokens = await self.llm.analyze_ast(
                subgraph=subgraph, 
                pr_diff=diff_data, 
                source_snippets=source_snippets,
                context_markdown=context_markdown,
                project_settings=project_settings
            )
            
            # 8. Post-process line numbers
            for finding in review_output.findings:
                if finding.file_path in changed_lines:
                    if finding.line_number not in changed_lines[finding.file_path]:
                        finding.line_number = None
                else:
                    finding.line_number = None
                    
            await emit_status("AI Analysis complete. Finalizing results...", stage="Finalizing Results")
            
            # --- DEBUG DUMPING ---
            try:
                import json
                import os
                
                if job_id:
                    from app.core.config import settings
                    if settings.WORKSPACE_BASE_DIR:
                        base_workspace_dir = settings.WORKSPACE_BASE_DIR
                    else:
                        base_backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
                        base_workspace_dir = os.path.join(base_backend_dir, "jobs")
                        
                    debug_dir = os.path.join(base_workspace_dir, str(job_id), "debug")
                    os.makedirs(debug_dir, exist_ok=True)
                else:
                    debug_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))), "debug_outputs", "sync")
                    os.makedirs(debug_dir, exist_ok=True)
                
                with open(os.path.join(debug_dir, "graph.json"), "w") as f:
                    json.dump(ast_data, f, indent=2)
                with open(os.path.join(debug_dir, "diff.txt"), "w") as f:
                    f.write(diff_data)
                with open(os.path.join(debug_dir, "change_analysis.json"), "w") as f:
                    json.dump(change_analysis.model_dump() if hasattr(change_analysis, "model_dump") else change_analysis, f, indent=2)
                with open(os.path.join(debug_dir, "subgraph.json"), "w") as f:
                    json.dump(subgraph, f, indent=2)
                with open(os.path.join(debug_dir, "review_context.json"), "w") as f:
                    json.dump(review_context.model_dump(), f, indent=2)
                with open(os.path.join(debug_dir, "context_markdown.md"), "w") as f:
                    f.write(context_markdown)
                with open(os.path.join(debug_dir, "llm_output.json"), "w") as f:
                    json.dump(review_output.model_dump() if hasattr(review_output, "model_dump") else review_output, f, indent=2)
                logger.info(f"Dumped debug files to {debug_dir}")
            except Exception as e:
                logger.warning(f"Failed to dump debug files: {e}")
            # ---------------------
            
            stats = {
                "changed_files_count": len(changed_lines),
                "changed_lines_count": sum(len(lines) for lines in changed_lines.values()),
                "changed_symbols_count": len(subgraph.get("changed_symbols", [])),
                "affected_files_count": len(set(node.get("file_path") for node in subgraph.get("dependencies", []) if node.get("file_path"))),
                "affected_symbols_count": len(subgraph.get("dependencies", [])),
                "related_tests_count": len(subgraph.get("related_tests", [])) if "related_tests" in subgraph else 0,
                "risk_level": getattr(review_output, "risk_level", "medium"),
            }
            return review_output, impact_graph, diff_data, input_tokens, output_tokens, stats
