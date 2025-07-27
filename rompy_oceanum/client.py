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
    
    def __init__(self, run_id: str, pipeline_name: str, org: str, project: str, 
                 stage: str, client=None):
        """Initialize the PraxResult.
        
        Args:
            run_id: Pipeline run identifier
            pipeline_name: Name of the pipeline
            org: Organization name
            project: Project name
            stage: Stage name
            client: PraxClient instance
        """
        self.run_id = run_id
        self.pipeline_name = pipeline_name
        self.org = org
        self.project = project
        self.stage = stage
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
            org=self.org,
            project=self.project,
            stage=self.stage
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
        
        # For now, we'll return an empty list as we don't have the actual download implementation
        # This would need to be implemented based on the actual oceanum-prax client API
        logger.warning("Output download not yet implemented in PraxClient")
        return []


class PraxClient:
    """Client for interacting with Oceanum Prax API."""
    
    def __init__(self, prax_config: Optional[PraxConfig] = None):
        """Initialize the PraxClient.
        
        Args:
            prax_config: Prax configuration. If None, will try to load from environment.
        """
        if prax_config is None:
            try:
                prax_config = PraxConfig.from_env()
            except Exception as e:
                raise ValueError(f"Failed to load Prax configuration: {e}")
                
        self._wrapper = PraxClientWrapper(prax_config)
        self.org = prax_config.org
        self.project = prax_config.project
        self.stage = prax_config.stage
    
    def submit_pipeline(self, pipeline_name: str, parameters: Optional[Dict[str, Any]] = None,
                        org: Optional[str] = None, project: Optional[str] = None, 
                        stage: Optional[str] = None):
        """Submit a pipeline for execution.
        
        Args:
            pipeline_name: Name of the pipeline to execute
            parameters: Pipeline parameters
            org: Organization name (defaults to config)
            project: Project name (defaults to config)
            stage: Stage name (defaults to config)
            
        Returns:
            PraxResult object for tracking the pipeline execution
        """
        org = org or self.org
        project = project or self.project
        stage = stage or self.stage
        
        run_id = self._wrapper.submit_pipeline(
            pipeline_name=pipeline_name,
            parameters=parameters or {}
        )
        
        return PraxResult(
            run_id=run_id,
            pipeline_name=pipeline_name,
            org=org,
            project=project,
            stage=stage,
            client=self
        )
    
    def get_run_status(self, run_id: str, pipeline_name: str, 
                       org: Optional[str] = None, project: Optional[str] = None,
                       stage: Optional[str] = None):
        """Get pipeline run status.
        
        Args:
            run_id: Pipeline run identifier
            pipeline_name: Name of the pipeline
            org: Organization name (defaults to config)
            project: Project name (defaults to config)
            stage: Stage name (defaults to config)
            
        Returns:
            Status dictionary
        """
        org = org or self.org
        project = project or self.project
        stage = stage or self.stage
        
        return self._wrapper.get_run_status(
            run_name=run_id,
            org=org,
            project=project,
            stage=stage
        )
    
    def get_run_logs(self, run_id: str, pipeline_name: str,
                     org: Optional[str] = None, project: Optional[str] = None,
                     stage: Optional[str] = None, task_name: Optional[str] = None):
        """Get pipeline run logs.
        
        Args:
            run_id: Pipeline run identifier
            pipeline_name: Name of the pipeline
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
        
        return self._wrapper.get_run_logs(
            run_name=run_id,
            org=org,
            project=project,
            stage=stage
        )
    
    def _get_headers(self):
        """Get headers for API requests."""
        return {
            "Authorization": f"Bearer {self._wrapper.prax_config.token}",
            "Content-Type": "application/json",
        }
    
    def _make_request(self, method, url, **kwargs):
        """Make an API request with proper headers."""
        headers = self._get_headers()
        if "headers" in kwargs:
            headers.update(kwargs["headers"])
        kwargs["headers"] = headers
        
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
        url = f"{self._wrapper.prax_config.base_url}/api/projects/{self.project}"
        return self._make_request("POST", url, json=template_data)
    
    def list_pipelines(self):
        """List all pipelines in the project.
        
        Returns:
            List of pipelines
        """
        url = f"{self._wrapper.prax_config.base_url}/api/projects/{self.project}/pipelines"
        response = self._make_request("GET", url)
        return response.get("resources", {}).get("pipelines", [])
    
    def get_pipeline(self, pipeline_name: str):
        """Get details of a specific pipeline.
        
        Args:
            pipeline_name: Name of the pipeline
            
        Returns:
            Pipeline details
        """
        url = f"{self._wrapper.prax_config.base_url}/api/projects/{self.project}/pipelines/{pipeline_name}"
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
        
        url = f"{self._wrapper.prax_config.base_url}/api/projects/{self.project}/pipelines/{pipeline_name}"
        return self._make_request("PATCH", url, json=ops)
    
    def delete_pipeline(self, pipeline_name: str):
        """Delete a pipeline from the project.
        
        Args:
            pipeline_name: Name of the pipeline
        """
        url = f"{self._wrapper.prax_config.base_url}/api/projects/{self.project}/pipelines/{pipeline_name}"
        self._make_request("DELETE", url)