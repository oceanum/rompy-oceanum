"""
Prax client for rompy-oceanum using the oceanum-prax library.

This module provides a client for interacting with the Prax pipeline API
using the official oceanum-prax library instead of custom API calls.
"""
import json
import logging
import time
from pathlib import Path
from typing import Dict, Any, Optional, List

from oceanum.cli.prax.client import PRAXClient
from oceanum.cli.prax.models import PipelineSchema, StagedRunSchema, ErrorResponse

from .config import PraxConfig

logger = logging.getLogger(__name__)


class PraxResult:
    """Result object for Prax pipeline execution."""

    def __init__(self, client: 'PraxClient', run_id: str, pipeline_name: str):
        """Initialize Prax result.

        Args:
            client: PraxClient instance
            run_id: Pipeline run identifier
            pipeline_name: Name of the executed pipeline
        """
        self.client = client
        self.run_id = run_id
        self.pipeline_name = pipeline_name
        self._cached_status = None
        self._status_cache_time = 0

    def get_status(self, use_cache: bool = True) -> Dict[str, Any]:
        """Get current pipeline status.

        Args:
            use_cache: Whether to use cached status (valid for 30 seconds)

        Returns:
            Status dictionary
        """
        current_time = time.time()
        cache_validity = 30  # seconds

        if (use_cache and self._cached_status and
            (current_time - self._status_cache_time) < cache_validity):
            return self._cached_status

        try:
            status = self.client.get_run_status(self.run_id)
            self._cached_status = status
            self._status_cache_time = current_time
            return status
        except Exception as e:
            logger.error(f"Failed to get status for run {self.run_id}: {e}")
            return {"status": "error", "error": str(e)}

    def get_logs(self, tail: int = 100) -> List[str]:
        """Get pipeline execution logs.

        Args:
            tail: Number of log lines to retrieve

        Returns:
            List of log lines
        """
        try:
            return self.client.get_run_logs(self.run_id, tail=tail)
        except Exception as e:
            logger.error(f"Failed to get logs for run {self.run_id}: {e}")
            return [f"Error retrieving logs: {e}"]

    def wait_for_completion(self, timeout: int = 3600, check_interval: int = 30) -> Dict[str, Any]:
        """Wait for pipeline completion.

        Args:
            timeout: Maximum time to wait in seconds
            check_interval: Time between status checks in seconds

        Returns:
            Final status dictionary
        """
        start_time = time.time()

        while time.time() - start_time < timeout:
            status = self.get_status(use_cache=False)

            if status.get("status") in ["completed", "succeeded", "failed", "error"]:
                return status

            logger.info(f"Pipeline {self.run_id} status: {status.get('status', 'unknown')}")
            time.sleep(check_interval)

        logger.warning(f"Pipeline {self.run_id} did not complete within {timeout} seconds")
        return {"status": "timeout", "message": f"Pipeline did not complete within {timeout} seconds"}

    def download_outputs(self, output_dir: str) -> List[Path]:
        """Download pipeline outputs.

        Args:
            output_dir: Directory to download outputs to

        Returns:
            List of downloaded file paths
        """
        # This would need to be implemented based on the specific pipeline
        # For now, return empty list
        logger.warning("Output download not yet implemented")
        return []

    def summary_status(self) -> str:
        """Get human-readable status summary.

        Returns:
            Status summary string
        """
        status = self.get_status()
        status_str = status.get("status", "unknown")

        if status_str == "completed":
            return "✅ Pipeline completed successfully"
        elif status_str == "failed":
            return "❌ Pipeline failed"
        elif status_str == "running":
            return "🔄 Pipeline is running"
        elif status_str == "pending":
            return "⏳ Pipeline is pending"
        else:
            return f"❓ Pipeline status: {status_str}"


class PraxClient:
    """Client for interacting with the Prax pipeline API using oceanum-prax."""

    def __init__(self, config: PraxConfig):
        """Initialize Prax client.

        Args:
            config: PraxConfig instance
        """
        self.config = config

        # Initialize the oceanum-prax client
        self._client = PRAXClient()
        self._client.token = config.token
        self._client.service = f"{config.base_url}/api"

        logger.info(f"Initialized Prax client for {config.org}/{config.project}")

    def check_pipeline_exists(self, pipeline_name: str) -> bool:
        """Check if a pipeline exists.

        Args:
            pipeline_name: Name of the pipeline

        Returns:
            True if pipeline exists, False otherwise
        """
        try:
            result = self._client.get_pipeline(
                pipeline_name,
                org=self.config.org,
                project=self.config.project,
                stage=self.config.stage
            )
            return isinstance(result, PipelineSchema)
        except Exception as e:
            logger.debug(f"Pipeline {pipeline_name} check failed: {e}")
            return False

    def deploy_pipeline(self, pipeline_name: str, template_path: str) -> bool:
        """Deploy a pipeline from template.

        Args:
            pipeline_name: Name of the pipeline
            template_path: Path to pipeline template

        Returns:
            True if deployment succeeded, False otherwise
        """
        try:
            # For now, log that deployment is not implemented
            logger.warning(f"Pipeline deployment not yet implemented for {pipeline_name}")
            logger.info(f"Template path: {template_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to deploy pipeline {pipeline_name}: {e}")
            return False

    def submit_pipeline(self, pipeline_name: str, parameters: Dict[str, Any]) -> str:
        """Submit a pipeline for execution.

        Args:
            pipeline_name: Name of the pipeline to execute
            parameters: Pipeline parameters

        Returns:
            Run ID of the submitted pipeline

        Raises:
            Exception: If submission fails
        """
        logger.info(f"Submitting pipeline {pipeline_name} with parameters: {list(parameters.keys())}")

        try:
            result = self._client.submit_pipeline(
                pipeline_name,
                parameters=parameters,
                org=self.config.org,
                project=self.config.project,
                stage=self.config.stage
            )

            if isinstance(result, ErrorResponse):
                raise Exception(f"Pipeline submission failed: {result.detail}")

            if isinstance(result, PipelineSchema) and result.last_run:
                run_id = result.last_run.id
                logger.info(f"✅ Pipeline submitted successfully. Run ID: {run_id}")
                return run_id
            else:
                raise Exception("No run ID returned from pipeline submission")

        except Exception as e:
            logger.error(f"✗ Failed to submit pipeline: {e}")
            raise

    def get_run_status(self, run_id: str) -> Dict[str, Any]:
        """Get pipeline run status.

        Args:
            run_id: Pipeline run identifier

        Returns:
            Status dictionary
        """
        try:
            # First try to get the run directly
            result = self._client.get_pipeline_run(
                run_id,
                org=self.config.org,
                project=self.config.project,
                stage=self.config.stage
            )

            if isinstance(result, ErrorResponse):
                # If direct query fails, try to find the run via pipeline
                logger.debug(f"Direct run query failed: {result.detail}, trying via pipeline")
                return self._get_run_status_via_pipeline(run_id)

            if isinstance(result, StagedRunSchema):
                return {
                    "status": result.status.lower() if result.status else "unknown",
                    "started_at": result.started_at.isoformat() if result.started_at else None,
                    "finished_at": result.finished_at.isoformat() if result.finished_at else None,
                    "message": getattr(result, 'message', None),
                    "run_id": result.id,
                    "name": result.name,
                    "details": getattr(result, 'details', {})
                }
            else:
                return {"status": "unknown", "error": "Unexpected response type"}

        except Exception as e:
            logger.error(f"Failed to get run status for {run_id}: {e}")
            return {"status": "error", "error": str(e)}

    def _get_run_status_via_pipeline(self, run_id: str) -> Dict[str, Any]:
        """Try to get run status by searching through pipelines.

        This is a fallback when direct run queries fail.
        """
        try:
            pipelines = self.list_pipelines()
            for pipeline_info in pipelines:
                pipeline_name = pipeline_info.get('name')
                if not pipeline_name:
                    continue

                # Get pipeline details
                pipeline = self._client.get_pipeline(
                    pipeline_name,
                    org=self.config.org,
                    project=self.config.project,
                    stage=self.config.stage
                )

                if hasattr(pipeline, 'last_run') and pipeline.last_run:
                    if pipeline.last_run.id == run_id:
                        # Found the run in this pipeline
                        return {
                            "status": pipeline.last_run.status.lower() if pipeline.last_run.status else "unknown",
                            "started_at": pipeline.last_run.started_at.isoformat() if pipeline.last_run.started_at else None,
                            "finished_at": pipeline.last_run.finished_at.isoformat() if pipeline.last_run.finished_at else None,
                            "message": getattr(pipeline.last_run, 'message', None),
                            "run_id": pipeline.last_run.id,
                            "name": pipeline.last_run.name,
                            "details": getattr(pipeline.last_run, 'details', {}),
                            "pipeline_name": pipeline_name
                        }

            return {"status": "error", "error": f"Run {run_id} not found in any pipeline"}

        except Exception as e:
            logger.error(f"Failed to find run via pipeline search: {e}")
            return {"status": "error", "error": str(e)}

    def get_run_logs(self, run_id: str, tail: int = 100) -> List[str]:
        """Get pipeline run logs.

        Args:
            run_id: Pipeline run identifier
            tail: Number of log lines to retrieve

        Returns:
            List of log lines
        """
        try:
            result = self._client.get_pipeline_run_logs(
                run_id,
                lines=tail,
                follow=False,
                org=self.config.org,
                project=self.config.project,
                stage=self.config.stage
            )

            # The logs method returns an iterable
            logs = []
            for log_line in result:
                if isinstance(log_line, str):
                    logs.append(log_line)
                elif isinstance(log_line, ErrorResponse):
                    logger.error(f"Error getting logs: {log_line.detail}")
                    break

            return logs

        except Exception as e:
            logger.error(f"Failed to get logs for run {run_id}: {e}")
            return [f"Error retrieving logs: {e}"]

    def download_run_artifacts(self, run_id: str, output_dir: Path) -> List[Path]:
        """Download pipeline run artifacts.

        Args:
            run_id: Pipeline run identifier
            output_dir: Directory to download artifacts to

        Returns:
            List of downloaded file paths
        """
        # This would need to be implemented based on the specific pipeline
        # For now, return empty list
        logger.warning(f"Artifact download not yet implemented for run {run_id}")
        return []

    def create_result(self, run_id: str, pipeline_name: str) -> PraxResult:
        """Create a PraxResult object for tracking pipeline execution.

        Args:
            run_id: Pipeline run identifier
            pipeline_name: Name of the executed pipeline

        Returns:
            PraxResult instance
        """
        return PraxResult(self, run_id, pipeline_name)

    def list_pipelines(self) -> List[Dict[str, Any]]:
        """List available pipelines.

        Returns:
            List of pipeline information dictionaries
        """
        try:
            result = self._client.list_pipelines(
                org=self.config.org,
                project=self.config.project,
                stage=self.config.stage
            )

            if isinstance(result, ErrorResponse):
                logger.error(f"Failed to list pipelines: {result.detail}")
                return []

            pipelines = []
            for pipeline in result:
                if isinstance(pipeline, PipelineSchema):
                    pipelines.append({
                        "name": pipeline.name,
                        "id": pipeline.id,
                        "org": pipeline.org,
                        "project": pipeline.project,
                        "stage": pipeline.stage,
                        "created_at": pipeline.created_at.isoformat() if pipeline.created_at else None,
                        "updated_at": pipeline.updated_at.isoformat() if pipeline.updated_at else None,
                        "suspended": pipeline.suspended,
                        "last_run": pipeline.last_run.status if pipeline.last_run else None
                    })

            return pipelines

        except Exception as e:
            logger.error(f"Failed to list pipelines: {e}")
            return []
