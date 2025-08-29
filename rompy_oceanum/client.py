"""Client interface for Oceanum Prax integration."""

import logging
import os
import time
from typing import Any, Dict, List, Optional

import requests


from .prax_client import PraxClientWrapper

logger = logging.getLogger(__name__)


class PraxResult:
    """Result object for tracking Prax pipeline execution."""

    def __init__(
        self,
        run_id: str,
        run_name: str,
        pipeline_name: str,
        org: str,
        project: str,
        stage: str,
        status: str = "submitted",
        client=None,
    ):
        """Initialize the PraxResult.

        Args:
            run_id: Pipeline run identifier
            run_name: Pipeline run name
            pipeline_name: Name of the pipeline
            org: Organization name
            project: Project name
            stage: Stage name
            status: Initial status
            client: PraxClient instance
        """
        self.run_id = run_id
        self.run_name = run_name
        self.pipeline_name = pipeline_name
        self.org = org
        self.project = project
        self.stage = stage
        self.status = status
        self.client = client

    def get_status(self):
        """Get the current status of the pipeline run.

        Returns:
            Status dictionary
        """
        if not self.client:
            raise ValueError("No client configured")

        # Check if we're using the PraxClientWrapper or our custom client
        if hasattr(self.client, "get_run_status"):
            # Using PraxClientWrapper
            return self.client.get_run_status(run_name=self.run_id)
        else:
            # Using our custom client
            return self.client.get_run_status(
                run_id=self.run_id,
                pipeline_name=self.pipeline_name,
                org=self.org,
                project=self.project,
                stage=self.stage,
            )

    def get_logs(self, task_name: Optional[str] = None):
        """Get logs from the pipeline run.

        Args:
            task_name: Optional task name to get logs for specific task

        Returns:
            List of log lines
        """
        if not self.client:
            raise ValueError("No client configured")

        # Check if we're using the PraxClientWrapper or our custom client
        if hasattr(self.client, "get_run_logs"):
            # Using PraxClientWrapper
            return self.client.get_run_logs(run_name=self.run_id)
        else:
            # Using our custom client
            return self.client.get_run_logs(
                run_id=self.run_id,
                pipeline_name=self.pipeline_name,
                org=self.org,
                project=self.project,
                stage=self.stage,
                task_name=task_name,
            )

    def wait_for_completion(self, timeout: int = 3600, check_interval: int = 30):
        """Wait for the pipeline run to complete.

        Args:
            timeout: Maximum time to wait for completion (seconds)
            check_interval: Time between status checks (seconds)

        Returns:
            Final status dictionary

        Raises:
            TimeoutError: If pipeline doesn't complete within timeout
        """
        start_time = time.time()

        while time.time() - start_time < timeout:
            status = self.get_status()
            if status.get("status") in ["completed", "succeeded", "failed", "error"]:
                return status

            logger.info(
                f"Pipeline {self.run_id} status: {status.get('status', 'unknown')}"
            )
            time.sleep(check_interval)

        raise TimeoutError(
            f"Pipeline {self.run_id} did not complete within {timeout} seconds"
        )

    def download_outputs(self, target_dir: str):
        """Download outputs from the pipeline run.

        Args:
            target_dir: Directory to download outputs to

        Returns:
            List of downloaded file paths
        """
        # Create target directory if it doesn't exist
        os.makedirs(target_dir, exist_ok=True)

        if not self.client:
            raise ValueError("No client configured")

        # Check if we're using the PraxClientWrapper or our custom client
        if hasattr(self.client, "download_run_artifacts"):
            # Using PraxClientWrapper
            return self.client.download_run_artifacts(
                run_name=self.run_id, target_dir=target_dir
            )
        else:
            # Using our custom client
            return self.client.download_run_artifacts(
                run_id=self.run_id,
                pipeline_name=self.pipeline_name,
                org=self.org,
                project=self.project,
                stage=self.stage,
                target_dir=target_dir,
            )


class PraxClient:
    """Client for interacting with Oceanum Prax API."""

    def __init__(
        self,
        base_url: str,
        token: str,
        org: str,
        project: str,
        stage: str = "dev",
        user: Optional[str] = None,
    ):
        """Initialize the PraxClient.

        Args:
            base_url: Base URL for Prax API
            token: Authentication token
            org: Organization name
            project: Project name
            stage: Deployment stage (default: "dev")
            user: User email (optional)
        """
        self.base_url = base_url
        self.token = token
        self.org = org
        self.project = project
        self.stage = stage
        self.user = user

    def _get_headers(self):
        """Get headers for API requests."""
        if not self.token:
            raise ValueError("No Prax token available")
        # Add "Bearer" prefix here if not already present
        token = (
            self.token if self.token.startswith("Bearer ") else f"Bearer {self.token}"
        )
        return {
            "Authorization": token,
            "Content-Type": "application/json",
            "accept": "application/json",
        }

    def submit_pipeline(
        self,
        pipeline_name: str,
        user: Optional[str] = None,
        org: Optional[str] = None,
        project: Optional[str] = None,
        stage: Optional[str] = None,
        parameters: Optional[Dict[str, Any]] = None,
        ctx=None,
    ):
        """Submit a pipeline for execution.

        Args:
            pipeline_name: Name of the pipeline to execute
            user: User name
            org: Organization name (defaults to config)
            project: Project name (defaults to config)
            stage: Stage name (defaults to config)
            parameters: Pipeline parameters
            ctx: Click context (optional)

        Returns:
            PraxResult object for tracking the pipeline execution
        """
        org = org or self.org
        project = project or self.project
        stage = stage or self.stage

        url = f"{self.base_url}/api/pipelines/{pipeline_name}/submit"
        params = {
            "user": user,
            "org": org,
            "project": project,
            "stage": stage,
        }

        response = self._make_request(
            "POST", url, params=params, json={"parameters": parameters or {}}
        )

        run_id = response.get("run_id", "unknown") if response else "unknown"
        run_name = response.get("run_id", "unknown") if response else "unknown"
        return PraxResult(
            run_id=run_id,
            run_name=run_name,
            pipeline_name=pipeline_name,
            org=org,
            project=project,
            stage=stage,
            status="submitted",
            client=self,
        )

    def get_run_status(
        self,
        run_id: str,
        pipeline_name: str,
        org: Optional[str] = None,
        project: Optional[str] = None,
        stage: Optional[str] = None,
        ctx=None,
    ):
        """Get pipeline run status.

        Args:
            run_id: Pipeline run identifier
            pipeline_name: Name of the pipeline
            org: Organization name (defaults to config)
            project: Project name (defaults to config)
            stage: Stage name (defaults to config)
            ctx: Click context (optional)

        Returns:
            Status dictionary
        """
        org = org or self.org
        project = project or self.project
        stage = stage or self.stage

        url = f"{self.base_url}/api/pipeline-runs/{run_id}"
        params = {
            "org": org,
            "project": project,
            "stage": stage,
        }
        return self._make_request("GET", url, params=params)

    def get_run_logs(
        self,
        run_id: str,
        pipeline_name: str,
        org: Optional[str] = None,
        project: Optional[str] = None,
        stage: Optional[str] = None,
        task_name: Optional[str] = None,
        ctx=None,
    ):
        """Get pipeline run logs.

        Args:
            run_id: Pipeline run identifier
            pipeline_name: Name of the pipeline
            org: Organization name (defaults to config)
            project: Project name (defaults to config)
            stage: Stage name (defaults to config)
            task_name: Optional task name to get logs for specific task
            ctx: Click context (optional)

        Returns:
            List of log lines
        """
        org = org or self.org
        project = project or self.project
        stage = stage or self.stage

        if task_name:
            url = f"{self.base_url}/api/pipeline-runs/{run_id}/tasks/{task_name}/logs"
        else:
            url = f"{self.base_url}/api/pipeline-runs/{run_id}/logs"

        params = {
            "org": org,
            "project": project,
            "stage": stage,
        }

        return self._make_request("GET", url, params=params)


    def _make_request(self, method, url, params=None, **kwargs):
        """Make an API request with proper headers."""
        headers = self._get_headers()
        if "headers" in kwargs:
            headers.update(kwargs["headers"])
        kwargs["headers"] = headers

        if params:
            kwargs["params"] = params

        response = requests.request(method, url, **kwargs)
        response.raise_for_status()
        return response.json() if response.content else None

    def submit_pipeline_template(
        self, template_data: Dict[str, Any], wait: bool = True
    ):
        """Submit a pipeline template to Prax.

        Args:
            template_data: Pipeline template data
            wait: Whether to wait for deployment to complete

        Returns:
            Response from the API
        """
        # For deploying pipelines, we'll use the oceanum CLI's prax client directly
        # since it handles authentication properly
        try:
            import click
            import yaml
            from oceanum.cli.prax import models
            from oceanum.cli.prax.client import PRAXClient

            # Use the oceanum CLI's prax client to deploy the template
            # This avoids authentication issues with our custom client
            ctx = click.get_current_context()
            client = PRAXClient(ctx)

            # Convert template_data to ProjectSpec object
            spec = models.ProjectSpec(**template_data)

            # Deploy the template
            result = client.deploy_project(spec)

            if isinstance(result, models.ErrorResponse):
                raise Exception(f"Failed to deploy pipeline template: {result.detail}")

            if wait:
                # Wait for deployment to complete
                click.echo("⏳ Waiting for pipeline deployment to complete...")
                get_params = {
                    "project_name": result.name,
                    "org": self.org,
                }
                if self.user:
                    get_params["user"] = self.user

                client.wait_project_deployment(**get_params)
                click.echo("✅ Pipeline deployment completed successfully!")

            return result

        except Exception as e:
            logger.error(f"Failed to submit pipeline template: {e}")
            raise

    def list_pipelines(self, ctx=None):
        """List pipelines in the project.

        Args:
            ctx: Click context (optional)

        Returns:
            List of pipeline dictionaries
        """
        url = f"{self.base_url}/api/pipelines"
        params = {
            "org": self.org,
            "project": self.project,
            "stage": self.stage,
        }
        return self._make_request("GET", url, params=params)

    def get_pipeline(self, pipeline_name: str):
        """Get details of a specific pipeline.

        Args:
            pipeline_name: Name of the pipeline

        Returns:
            Pipeline details
        """
        url = f"{self.base_url}/api/projects/{self.project}/pipelines/{pipeline_name}"
        return self._make_request("GET", url)

    def update_pipeline(self, pipeline_name: str, template_data: Dict[str, Any]):
        """Update an existing pipeline.

        Args:
            pipeline_name: Name of the pipeline
            template_data: Updated pipeline template data

        Returns:
            Response from the API
        """
        # For updating, we need to use PATCH with JSON Patch operations
        # First, get the current pipeline
        current_pipeline = self.get_pipeline(pipeline_name)

        # Create a list of operations to update the pipeline
        ops = []
        for key, value in template_data.items():
            if key != "name":  # Don't update the name
                ops.append({"op": "replace", "path": f"/{key}", "value": value})

        url = f"{self.base_url}/api/projects/{self.project}/pipelines/{pipeline_name}"
        return self._make_request("PATCH", url, json=ops)

    def delete_pipeline(self, pipeline_name: str):
        """Delete a pipeline from the project.

        Args:
            pipeline_name: Name of the pipeline
        """
        url = f"{self.base_url}/api/projects/{self.project}/pipelines/{pipeline_name}"
        self._make_request("DELETE", url)

    def submit_project_spec(self, spec_data: Dict[str, Any], wait: bool = True):
        """Submit a project specification to Prax.

        Args:
            spec_data: Project specification data
            wait: Whether to wait for deployment to complete

        Returns:
            Response from the API
        """
        # For deploying projects, we'll use the oceanum CLI's prax client directly
        # since it handles authentication properly
        try:
            import click
            import yaml
            from oceanum.cli.prax import models
            from oceanum.cli.prax.client import PRAXClient

            # Use the oceanum CLI's prax client to deploy the template
            # This avoids authentication issues with our custom client
            ctx = click.get_current_context()
            client = PRAXClient(ctx)

            # Convert spec_data to ProjectSpec object
            spec = models.ProjectSpec(**spec_data)

            # Deploy the template
            result = client.deploy_project(spec)

            if isinstance(result, models.ErrorResponse):
                raise Exception(f"Failed to deploy project: {result.detail}")

            if wait:
                # Wait for deployment to complete
                click.echo("⏳ Waiting for project deployment to complete...")
                get_params = {
                    "project_name": result.name,
                    "org": self.org,
                }
                if self.user:
                    get_params["user"] = self.user

                client.wait_project_deployment(**get_params)
                click.echo("✅ Project deployment completed successfully!")

            return result

        except Exception as e:
            logger.error(f"Failed to submit pipeline template: {e}")
            raise

    def list_projects(self, search: Optional[str] = None, ctx=None):
        """List all projects accessible to the user.

        Args:
            search: Optional search filter for project names
            ctx: Click context (optional)

        Returns:
            List of projects
        """
        url = f"{self.base_url}/api/projects"
        params = {}
        if search:
            params["search"] = search
        response = self._make_request("GET", url, params=params)
        if response is None:
            return []
        if isinstance(response, list):
            return response
        projects = response.get("projects", []) if response else []
        return projects

    def get_project(self, project_name: str):
        """Get details of a specific project.

        Args:
            project_name: Name of the project

        Returns:
            Project details
        """
        url = f"{self.base_url}/api/projects/{project_name}"
        try:
            return self._make_request("GET", url)
        except Exception as e:
            # Return error response in the same format as prax client
            return {"detail": str(e)}

    def delete_project(self, project_name: str):
        """Delete a project.

        Args:
            project_name: Name of the project
        """
        url = f"{self.base_url}/api/projects/{project_name}"
        self._make_request("DELETE", url)

    def download_run_artifacts(
        self,
        run_id: str,
        pipeline_name: str,
        user: str,
        org: str,
        project: str,
        stage: str,
        target_dir: str,
    ):
        """Download artifacts from a pipeline run.

        Args:
            run_id: Pipeline run identifier
            pipeline_name: Name of the pipeline
            user: User name
            org: Organization name
            project: Project name
            stage: Stage name
            target_dir: Directory to download artifacts to

        Returns:
            List of downloaded file paths
        """
        # Create target directory if it doesn't exist
        os.makedirs(target_dir, exist_ok=True)

        # Get list of artifacts
        url = f"{self.base_url}/api/pipelines/{pipeline_name}/runs/{run_id}/artifacts"
        params = {
            "user": user,
            "org": org,
            "project": project,
            "stage": stage,
        }

        try:
            artifacts = self._make_request("GET", url, params=params)
        except Exception as e:
            logger.warning(f"Failed to get artifact list: {e}")
            return []

        if not artifacts:
            artifacts = []

        downloaded_files = []

        # Download each artifact
        for artifact in artifacts:
            artifact_name = artifact.get("name")
            if not artifact_name:
                continue

            artifact_url = f"{url}/{artifact_name}"
            artifact_path = os.path.join(target_dir, artifact_name)

            try:
                response = requests.get(
                    artifact_url,
                    params=params,
                    headers=self._get_headers(),
                    stream=True,
                )
                response.raise_for_status()

                with open(artifact_path, "wb") as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)

                downloaded_files.append(artifact_path)
            except Exception as e:
                logger.warning(f"Failed to download artifact {artifact_name}: {e}")

        return downloaded_files
