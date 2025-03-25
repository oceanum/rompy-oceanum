"""
Prax API client for rompy-oceanum.

This module provides a client for interacting with Oceanum's Prax API.
"""

import os
import json
import time
from typing import Dict, Any, List, Optional, Union
import logging
import requests
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

class PraxResult(BaseModel):
    """Result from a Prax pipeline submission."""
    
    run_id: str
    pipeline_name: str
    user: str
    org: str
    project: str
    stage: str
    status: str
    client: Any = Field(exclude=True)
    
    def get_status(self) -> Dict[str, Any]:
        """Get the current status of the pipeline run."""
        if self.client is None:
            raise ValueError("No client configured for this PraxResult")
        
        return self.client.get_run_status(
            run_id=self.run_id,
            pipeline_name=self.pipeline_name,
            user=self.user,
            org=self.org,
            project=self.project,
            stage=self.stage
        )
    
    def get_logs(self, task_name: Optional[str] = None) -> Dict[str, Any]:
        """Get logs from the pipeline run, optionally for a specific task."""
        if self.client is None:
            raise ValueError("No client configured for this PraxResult")
        
        return self.client.get_run_logs(
            run_id=self.run_id,
            pipeline_name=self.pipeline_name,
            user=self.user,
            org=self.org,
            project=self.project,
            stage=self.stage,
            task_name=task_name
        )
    
    def wait_for_completion(self, 
                           timeout: int = 3600, 
                           check_interval: int = 30) -> Dict[str, Any]:
        """
        Wait for the pipeline run to complete.
        
        Args:
            timeout: Maximum time to wait in seconds (default: 1 hour)
            check_interval: Time between status checks in seconds (default: 30s)
            
        Returns:
            The final status of the run
            
        Raises:
            TimeoutError: If the run does not complete within the timeout period
        """
        start_time = time.time()
        while True:
            status = self.get_status()
            current_status = status.get("status", "unknown")
            
            if current_status.lower() in ("succeeded", "failed", "error", "terminated"):
                return status
            
            if time.time() - start_time > timeout:
                raise TimeoutError(f"Pipeline run did not complete within {timeout} seconds")
            
            time.sleep(check_interval)
    
    def download_outputs(self, target_dir: str = "./outputs") -> List[str]:
        """
        Download output artifacts from the completed pipeline run.
        
        Args:
            target_dir: Directory to save the downloaded files
            
        Returns:
            List of paths to downloaded files
        """
        if self.client is None:
            raise ValueError("No client configured for this PraxResult")
        
        # Make sure target directory exists
        os.makedirs(target_dir, exist_ok=True)
        
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
    """Client for interacting with Oceanum's Prax API."""
    
    def __init__(self, base_url: str = "https://prax.oceanum.io", token: Optional[str] = None):
        """
        Initialize the Prax client.
        
        Args:
            base_url: Base URL for the Prax API
            token: Prax API token. If None, will look for PRAX_TOKEN environment variable
        """
        self.base_url = base_url.rstrip("/")
        self.token = token or os.environ.get("PRAX_TOKEN")
        
        if not self.token:
            logger.warning("No Prax token provided. Set the PRAX_TOKEN environment variable.")
    
    def _get_headers(self) -> Dict[str, str]:
        """Get HTTP headers with authentication for Prax API requests."""
        if not self.token:
            raise ValueError("No Prax token available. Set PRAX_TOKEN environment variable.")
        
        return {
            "accept": "application/json",
            "Authorization": self.token,
            "Content-Type": "application/json",
        }
    
    def submit_pipeline(self,
                       pipeline_name: str,
                       user: str,
                       org: str,
                       project: str,
                       stage: str,
                       parameters: Dict[str, Any]) -> PraxResult:
        """
        Submit a pipeline to Prax.
        
        Args:
            pipeline_name: Name of the pipeline to run
            user: Username
            org: Organization name
            project: Project name
            stage: Stage name (e.g., "dev", "prod")
            parameters: Pipeline parameters
            
        Returns:
            PraxResult object with information about the submitted run
        """
        url = f"{self.base_url}/api/pipelines/{pipeline_name}/submit"
        
        params = {
            "user": user,
            "org": org,
            "project": project,
            "stage": stage,
        }
        
        payload = {"parameters": parameters}
        
        response = requests.post(
            url, 
            params=params, 
            headers=self._get_headers(), 
            json=payload
        )
        
        if response.status_code >= 400:
            error_msg = f"Error submitting pipeline: {response.status_code} - {response.text}"
            logger.error(error_msg)
            response.raise_for_status()
            
        result_data = response.json()
        run_id = result_data.get("name")
        
        if not run_id:
            raise ValueError(f"No run ID in response: {result_data}")
        
        return PraxResult(
            run_id=run_id,
            pipeline_name=pipeline_name,
            user=user,
            org=org,
            project=project,
            stage=stage,
            status="submitted",
            client=self
        )
    
    def get_run_status(self,
                      run_id: str,
                      pipeline_name: str,
                      user: str,
                      org: str,
                      project: str,
                      stage: str) -> Dict[str, Any]:
        """
        Get the status of a pipeline run.
        
        Args:
            run_id: ID of the run to check
            pipeline_name: Name of the pipeline
            user: Username
            org: Organization name
            project: Project name
            stage: Stage name
            
        Returns:
            Dictionary with run status information
        """
        url = f"{self.base_url}/api/pipelines/{pipeline_name}/runs/{run_id}"
        
        params = {
            "user": user,
            "org": org,
            "project": project,
            "stage": stage,
        }
        
        response = requests.get(
            url, 
            params=params, 
            headers=self._get_headers()
        )
        
        if response.status_code >= 400:
            error_msg = f"Error getting run status: {response.status_code} - {response.text}"
            logger.error(error_msg)
            response.raise_for_status()
            
        return response.json()
    
    def get_run_logs(self,
                    run_id: str,
                    pipeline_name: str,
                    user: str,
                    org: str,
                    project: str,
                    stage: str,
                    task_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Get logs from a pipeline run.
        
        Args:
            run_id: ID of the run
            pipeline_name: Name of the pipeline
            user: Username
            org: Organization name
            project: Project name
            stage: Stage name
            task_name: Optional task name to get logs for a specific task
            
        Returns:
            Dictionary with logs information
        """
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
        
        response = requests.get(
            url, 
            params=params, 
            headers=self._get_headers()
        )
        
        if response.status_code >= 400:
            error_msg = f"Error getting run logs: {response.status_code} - {response.text}"
            logger.error(error_msg)
            response.raise_for_status()
            
        return response.json()
    
    def download_run_artifacts(self,
                              run_id: str,
                              pipeline_name: str,
                              user: str,
                              org: str,
                              project: str,
                              stage: str,
                              target_dir: str = "./outputs") -> List[str]:
        """
        Download artifacts from a completed pipeline run.
        
        Args:
            run_id: ID of the run
            pipeline_name: Name of the pipeline
            user: Username
            org: Organization name
            project: Project name
            stage: Stage name
            target_dir: Directory to save downloaded files
            
        Returns:
            List of paths to downloaded files
        """
        # First, get the list of available artifacts
        url = f"{self.base_url}/api/pipelines/{pipeline_name}/runs/{run_id}/artifacts"
        
        params = {
            "user": user,
            "org": org,
            "project": project,
            "stage": stage,
        }
        
        response = requests.get(
            url, 
            params=params, 
            headers=self._get_headers()
        )
        
        if response.status_code >= 400:
            error_msg = f"Error listing artifacts: {response.status_code} - {response.text}"
            logger.error(error_msg)
            response.raise_for_status()
            
        artifacts = response.json()
        downloaded_files = []
        
        # Download each artifact
        for artifact in artifacts:
            artifact_name = artifact.get("name")
            if not artifact_name:
                logger.warning(f"Artifact without name: {artifact}")
                continue
                
            # Download artifact
            download_url = f"{self.base_url}/api/pipelines/{pipeline_name}/runs/{run_id}/artifacts/{artifact_name}"
            download_response = requests.get(
                download_url,
                params=params,
                headers=self._get_headers(),
                stream=True
            )
            
            if download_response.status_code >= 400:
                logger.error(f"Error downloading artifact {artifact_name}: {download_response.status_code}")
                continue
                
            # Save to file
            target_path = os.path.join(target_dir, f"{artifact_name}")
            with open(target_path, "wb") as f:
                for chunk in download_response.iter_content(chunk_size=8192):
                    f.write(chunk)
                    
            downloaded_files.append(target_path)
            logger.info(f"Downloaded artifact {artifact_name} to {target_path}")
            
        return downloaded_files
