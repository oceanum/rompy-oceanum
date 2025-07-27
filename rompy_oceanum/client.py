"""Client interface for Oceanum Prax integration."""

import logging
import os
import time
from typing import Dict, Any, Optional, List

import requests
from .config import PraxConfig
from .prax_client import PraxClientWrapper

logger = logging.getLogger(__name__)


class PraxResult:
    """Result object for tracking Prax pipeline execution."""
    
    def __init__(self, run_id: str, pipeline_name: str, user: str, org: str, project: str, 
                 stage: str, status: str = "submitted", client=None):
        """Initialize the PraxResult.
        
        Args:
            run_id: Pipeline run identifier
            pipeline_name: Name of the pipeline
            user: User name
            org: Organization name
            project: Project name
            stage: Stage name
            status: Initial status
            client: PraxClient instance
        """
        self.run_id = run_id
        self.pipeline_name = pipeline_name
        self.user = user
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
            
        return self.client.get_run_status(
            run_id=self.run_id,
            pipeline_name=self.pipeline_name,
            user=self.user,
            org=self.org,
            project=self.project,
            stage=self.stage
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
            
        return self.client.get_run_logs(
            run_id=self.run_id,
            pipeline_name=self.pipeline_name,
            user=self.user,
            org=self.org,
            project=self.project,
            stage=self.stage,
            task_name=task_name
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
                
            logger.info(f"Pipeline {self.run_id} status: {status.get('status', 'unknown')}")
            time.sleep(check_interval)
            
        raise TimeoutError(f"Pipeline {self.run_id} did not complete within {timeout} seconds")
    
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
            
        return self.client.download_run_artifacts(
            run_id=self.run_id,
            pipeline_name=self.pipeline_name,
            user=self.user,
            org=self.org,
            project=self.project,
            stage=self.stage,
            target_dir=target_dir
        )


class PraxClient:
    """Client for interacting with Oceanum Prax API."""
    
    def __init__(self, prax_config: Optional[PraxConfig] = None, base_url: Optional[str] = None, 
                 token: Optional[str] = None):
        """Initialize the PraxClient.
        
        Args:
            prax_config: Prax configuration. If None, will try to load from environment.
            base_url: Base URL for Prax API (overrides prax_config)
            token: Authentication token (overrides prax_config)
        """
        if prax_config is None:
            try:
                prax_config = PraxConfig.from_env()
            except Exception as e:
                raise ValueError(f"Failed to load Prax configuration: {e}")
                
        self.prax_config = prax_config
        self.base_url = base_url or prax_config.base_url
        self.token = token or prax_config.token
        self.org = prax_config.org
        self.project = prax_config.project
        self.stage = prax_config.stage
    
    def _get_headers(self):
        """Get headers for API requests."""
        if not self.token:
            raise ValueError("No Prax token available")
        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
            "accept": "application/json",
        }
    
    def submit_pipeline(self, pipeline_name: str, user: str, org: Optional[str] = None, 
                        project: Optional[str] = None, stage: Optional[str] = None,
                        parameters: Optional[Dict[str, Any]] = None):
        """Submit a pipeline for execution.
        
        Args:
            pipeline_name: Name of the pipeline to execute
            user: User name
            org: Organization name (defaults to config)
            project: Project name (defaults to config)
            stage: Stage name (defaults to config)
            parameters: Pipeline parameters
            
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
        
        response = self._make_request("POST", url, params=params, json={"parameters": parameters or {}})
        
        return PraxResult(
            run_id=response.get("run_id", "unknown"),
            pipeline_name=pipeline_name,
            user=user,
            org=org,
            project=project,
            stage=stage,
            status="submitted",
            client=self
        )
    
    def get_run_status(self, run_id: str, pipeline_name: str, user: str,
                       org: Optional[str] = None, project: Optional[str] = None,
                       stage: Optional[str] = None):
        """Get pipeline run status.
        
        Args:
            run_id: Pipeline run identifier
            pipeline_name: Name of the pipeline
            user: User name
            org: Organization name (defaults to config)
            project: Project name (defaults to config)
            stage: Stage name (defaults to config)
            
        Returns:
            Status dictionary
        """
        org = org or self.org
        project = project or self.project
        stage = stage or self.stage
        
        url = f"{self.base_url}/api/pipelines/{pipeline_name}/runs/{run_id}"
        params = {
            "user": user,
            "org": org,
            "project": project,
            "stage": stage,
        }
        
        return self._make_request("GET", url, params=params)
    
    def get_run_logs(self, run_id: str, pipeline_name: str, user: str,
                     org: Optional[str] = None, project: Optional[str] = None,
                     stage: Optional[str] = None, task_name: Optional[str] = None):
        """Get pipeline run logs.
        
        Args:
            run_id: Pipeline run identifier
            pipeline_name: Name of the pipeline
            user: User name
            org: Organization name (defaults to config)
            project: Project name (defaults to config)
            stage: Stage name (defaults to config)
            task_name: Optional task name to get logs for specific task
            
        Returns:
            List of log lines
        """
        org = org or self.org
        project = project or self.project
        stage = stage or self.stage
        
        if task_name:
            url = f"{self.base_url}/api/pipelines/{pipeline_name}/runs/{run_id}/tasks/{task_name}/logs"
        else:
            url = f"{self.base_url}/api/pipelines/{pipeline_name}/runs/{run_id}/logs"
            
        params = {
            "user": user,
            "org": org,
            "project": project,
            "stage": stage,
        }
        
        return self._make_request("GET", url, params=params)
    
    def _get_headers(self):
        """Get headers for API requests."""
        if not self.token:
            raise ValueError("No Prax token available")
        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
            "accept": "application/json",
        }
    
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
    
    def submit_pipeline_template(self, template_data: Dict[str, Any]):
        """Submit a pipeline template to Prax.
        
        Args:
            template_data: Pipeline template data
            
        Returns:
            Response from the API
        """
        url = f"{self.base_url}/api/projects/{self.project}"
        return self._make_request("POST", url, json=template_data)
    
    def list_pipelines(self):
        """List all pipelines in the project.
        
        Returns:
            List of pipelines
        """
        url = f"{self.base_url}/api/projects/{self.project}/pipelines"
        response = self._make_request("GET", url)
        return response.get("resources", {}).get("pipelines", [])
    
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
                ops.append({
                    "op": "replace",
                    "path": f"/{key}",
                    "value": value
                })
        
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
        url = f"{self.base_url}/api/projects"
        response = self._make_request("POST", url, json=spec_data)
        
        if wait and "name" in response:
            # Wait for project deployment to complete
            project_name = response["name"]
            self._wait_for_project_deployment(project_name)
            
        return response
    
    def list_projects(self):
        """List all projects accessible to the user.
        
        Returns:
            List of projects
        """
        url = f"{self.base_url}/api/projects"
        response = self._make_request("GET", url)
        return response.get("projects", [])
    
    def get_project(self, project_name: str):
        """Get details of a specific project.
        
        Args:
            project_name: Name of the project
            
        Returns:
            Project details
        """
        url = f"{self.base_url}/api/projects/{project_name}"
        return self._make_request("GET", url)
    
    def delete_project(self, project_name: str):
        """Delete a project.
        
        Args:
            project_name: Name of the project
        """
        url = f"{self.base_url}/api/projects/{project_name}"
        self._make_request("DELETE", url)
    
    def _wait_for_project_deployment(self, project_name: str, timeout: int = 300):
        """Wait for project deployment to complete.
        
        Args:
            project_name: Name of the project
            timeout: Maximum time to wait (seconds)
        """
        url = f"{self._wrapper.prax_config.base_url}/api/projects/{project_name}"
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                response = self._make_request("GET", url)
                status = response.get("status", "unknown")
                if status in ["active", "ready"]:
                    return
                elif status in ["error", "failed"]:
                    raise Exception(f"Project deployment failed with status: {status}")
            except Exception:
                pass  # Continue waiting if there's an error checking status
                
            time.sleep(5)
            
        raise TimeoutError(f"Project {project_name} deployment did not complete within {timeout} seconds")
    
    def download_run_artifacts(self, run_id: str, pipeline_name: str, user: str,
                               org: str, project: str, stage: str, target_dir: str):
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
        
        downloaded_files = []
        
        # Download each artifact
        for artifact in artifacts:
            artifact_name = artifact.get("name")
            if not artifact_name:
                continue
                
            artifact_url = f"{url}/{artifact_name}"
            artifact_path = os.path.join(target_dir, artifact_name)
            
            try:
                response = requests.get(artifact_url, params=params, headers=self._get_headers(), stream=True)
                response.raise_for_status()
                
                with open(artifact_path, "wb") as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                        
                downloaded_files.append(artifact_path)
            except Exception as e:
                logger.warning(f"Failed to download artifact {artifact_name}: {e}")
                
        return downloaded_files