"""
Prax API client for rompy-oceanum.

This module provides a client for interacting with Oceanum's Prax API.
"""

import json
import logging
import os
import re
import time
from typing import Any, Dict, List, Optional, Union

import requests
import yaml
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

    def deploy_if_needed(self, template_path: str) -> bool:
        """
        Deploy the pipeline if it doesn't already exist.

        Args:
            template_path: Path to the YAML template file for the pipeline

        Returns:
            True if deployment was performed, False if the pipeline already exists
        """
        if self.client is None:
            raise ValueError("No client configured for this PraxResult")

        # Check if the pipeline exists
        exists = self.client.check_pipeline_exists(
            pipeline_name=self.pipeline_name,
            user=self.user,
            org=self.org,
            project=self.project,
            stage=self.stage,
        )

        # If the pipeline doesn't exist, deploy it
        if not exists:
            logger.info(
                f"Pipeline {self.pipeline_name} does not exist, deploying from {template_path}"
            )
            self.client.deploy_pipeline(
                template_path=template_path,
                user=self.user,
                org=self.org,
                project=self.project,
                stage=self.stage,
            )
            return True

        logger.info(
            f"Pipeline {self.pipeline_name} already exists, skipping deployment"
        )
        return False

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
            stage=self.stage,
        )

    def get_logs(
        self,
        task_name: Optional[str] = None,
        follow: bool = False,
        tail: int = 1000,
        stream_to_stdout: bool = False,
        format_logs: bool = True,
    ) -> Dict[str, Any]:
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
            task_name=task_name,
            follow=follow,
            tail=tail,
            stream_to_stdout=stream_to_stdout,
            format_logs=format_logs,
        )

    def wait_for_completion(
        self, timeout: int = 3600, check_interval: int = 30
    ) -> Dict[str, Any]:
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
                raise TimeoutError(
                    f"Pipeline run did not complete within {timeout} seconds"
                )

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
            target_dir=target_dir,
        )

    def summary_status(self, status=None):
        """Display a formatted summary of the pipeline run status.

        Args:
            status: Status dictionary from get_status(). If None, calls get_status() automatically.
        """
        if status is None:
            status = self.get_status()

        # Check if status is available
        if not status:
            print("No status information available")
            return

        # Extract basic run information
        run_id = status.get("name", "N/A")
        overall_status = status.get("status", "Unknown")
        started_at = status.get("started_at", "N/A")
        updated_at = status.get("updated_at", "N/A")

        # Extract organization and project details
        org = status.get("org", "N/A")
        project = status.get("project", "N/A")
        stage = status.get("stage", "N/A")

        # Extract pipeline details
        details = status.get("details", {})
        tasks = []

        # Process task details
        for node_id, node_info in details.items():
            # Skip the parent nodes to avoid duplication
            if node_info.get("displayName", "").endswith("(0)"):
                continue

            task_type = node_info.get("type", "Unknown")
            task_name = node_info.get("displayName", node_id)
            task_status = node_info.get("phase", "Unknown")
            task_started = node_info.get("startedAt", "N/A")
            task_finished = node_info.get("finishedAt", "N/A")
            task_progress = node_info.get("progress", "N/A")

            # Only add real tasks (not parent groups)
            if task_type not in ["Retry", "DAG"]:
                tasks.append(
                    {
                        "name": task_name,
                        "type": task_type,
                        "status": task_status,
                        "progress": task_progress,
                        "started": task_started,
                        "finished": task_finished,
                    }
                )

        # Format and print the summary
        print("\n" + "=" * 80)
        print(f"{'PIPELINE RUN SUMMARY':^80}")
        print("=" * 80)

        print(f"\n{'Run ID:':<20}{run_id}")
        print(f"{'Organization:':<20}{org}")
        print(f"{'Project:':<20}{project}")
        print(f"{'Stage:':<20}{stage}")
        print(f"{'Status:':<20}{overall_status}")
        print(f"{'Started:':<20}{started_at}")
        print(f"{'Last Updated:':<20}{updated_at}")

        # Print task details
        if tasks:
            print("\n" + "-" * 80)
            print(f"{'TASKS':^80}")
            print("-" * 80)

            # Format header
            print(f"{'TASK NAME':<30}{'TYPE':<15}{'STATUS':<15}{'PROGRESS':<15}")
            print("-" * 80)

            # Print each task
            for task in tasks:
                print(
                    f"{task['name']:<30}{task['type']:<15}{task['status']:<15}{task['progress']:<15}"
                )

        print("\n" + "=" * 80 + "\n")


class PraxClient:
    """Client for interacting with Oceanum's Prax API."""

    def check_pipeline_exists(
        self, pipeline_name: str, user: str, org: str, project: str, stage: str
    ) -> bool:
        """
        Check if a pipeline with the given name exists.

        Args:
            pipeline_name: Name of the pipeline to check
            user: Username
            org: Organization name
            project: Project name
            stage: Stage name

        Returns:
            True if the pipeline exists, False otherwise
        """
        # Try to get the pipeline configuration to see if it exists
        url = f"{self.base_url}/api/pipelines/{pipeline_name}"

        params = {
            "user": user,
            "org": org,
            "project": project,
            "stage": stage,
        }

        logger.debug(f"Checking if pipeline exists: {url} with params {params}")

        try:
            response = requests.get(
                url, params=params, headers=self._get_headers(), timeout=30
            )

            # If we get a 200 response, the pipeline exists
            if response.status_code == 200:
                logger.info(f"Pipeline {pipeline_name} exists")
                return True

            # If we get a 404, it doesn't exist
            if response.status_code == 404:
                logger.info(f"Pipeline {pipeline_name} does not exist")
                return False

            # For other status codes, raise an error
            response.raise_for_status()

        except requests.exceptions.RequestException as e:
            logger.warning(f"Error checking if pipeline exists: {str(e)}")
            # If we're not sure, we'll assume it doesn't exist
            return False

    def deploy_pipeline(
        self, template_path: str, user: str, org: str, project: str, stage: str
    ) -> Dict[str, Any]:
        """
        Deploy a pipeline from a YAML template file.

        Args:
            template_path: Path to the YAML template file
            user: Username
            org: Organization name
            project: Project name
            stage: Stage name

        Returns:
            Response from the API containing the deployment status
        """
        if not os.path.exists(template_path):
            raise ValueError(f"Template file not found: {template_path}")

        # Read the template file
        try:
            with open(template_path, "r") as f:
                template_content = f.read()
        except Exception as e:
            raise ValueError(f"Error reading template file: {str(e)}")

        # Deploy the pipeline using the Prax API
        url = f"{self.base_url}/api/projects"

        params = {
            "user": user,
            "org": org,
            "project": project,
            "stage": stage,
        }

        # The API expects a project_spec object with a name field
        # Extract project name from the template if possible, or use a default name
        try:
            template_yaml = yaml.safe_load(template_content)
            project_name = template_yaml.get("name", f"pipeline-{project}")
        except Exception:
            project_name = f"pipeline-{project}"

        # Create the project spec with the required fields
        payload = {
            "name": project_name,
            "description": f"Pipeline deployed from {os.path.basename(template_path)}",
            "version": "v1",
            # Don't include content directly, we'll use the original template structure
            "resources": template_yaml.get("resources", {}),
        }

        logger.debug(f"Deploying pipeline from template {template_path}")

        try:
            response = requests.post(
                url,
                params=params,
                json=payload,
                headers=self._get_headers(),
                timeout=60,  # Longer timeout for deployment
            )

            response.raise_for_status()
            result = response.json()

            logger.info(f"Successfully deployed pipeline from {template_path}")
            return result

        except requests.exceptions.RequestException as e:
            error_msg = f"Error deploying pipeline: {str(e)}"
            logger.error(error_msg)

            # Provide more detailed error information if available
            if hasattr(e, "response") and e.response is not None:
                try:
                    error_detail = e.response.json()
                    logger.error(f"API error response: {error_detail}")
                except:
                    pass

            # In development mode, return a simulated response
            if os.environ.get("ROMPY_DEV_MODE") == "1":
                logger.warning(
                    "Development mode enabled - returning simulated deployment response"
                )
                return {
                    "status": "success",
                    "message": "Pipeline deployed successfully (simulated)",
                }

            # In production, raise the error
            raise

    def __init__(
        self, base_url: str = "https://prax.oceanum.io", token: Optional[str] = None
    ):
        """
        Initialize the Prax client.

        Args:
            base_url: Base URL for the Prax API
            token: Prax API token. If None, will look for PRAX_TOKEN environment variable
        """
        self.base_url = base_url.rstrip("/")
        self.token = token or os.environ.get("PRAX_TOKEN")

        if not self.token:
            logger.warning(
                "No Prax token provided. Set the PRAX_TOKEN environment variable."
            )

    def _get_headers(self) -> Dict[str, str]:
        """Get HTTP headers with authentication for Prax API requests."""
        if not self.token:
            raise ValueError(
                "No Prax token available. Set PRAX_TOKEN environment variable."
            )

        return {
            "accept": "application/json",
            "Authorization": self.token,
            "Content-Type": "application/json",
        }

    def submit_pipeline(
        self,
        pipeline_name: str,
        user: str,
        org: str,
        project: str,
        stage: str,
        parameters: Dict[str, Any],
    ) -> PraxResult:
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
            url, params=params, headers=self._get_headers(), json=payload
        )

        if response.status_code >= 400:
            error_msg = (
                f"Error submitting pipeline: {response.status_code} - {response.text}"
            )
            logger.error(error_msg)
            response.raise_for_status()

        result_data = response.json()
        logger.debug(f"Pipeline submission response: {result_data}")

        # Add debug logging to see exact structure of the API response
        logger.debug(
            f"Pipeline submission response structure: {json.dumps(result_data, indent=2)}"
        )

        # Based on the Prax API response structure, the run ID is in the last_run.name field
        if "last_run" in result_data and isinstance(result_data["last_run"], dict):
            run_id = result_data["last_run"].get("name")
            if run_id:
                logger.info(f"Found run ID in last_run.name: {run_id}")
        else:
            run_id = None

        # If we couldn't find it in the expected location, use fallback methods
        if not run_id:
            logger.warning(
                "Could not find run_id in last_run.name, trying alternative locations"
            )
            # Check for common fields
            run_id = (
                result_data.get("id")
                or result_data.get("run_id")
                or result_data.get("name")
                or result_data.get("object_ref")
            )

        # Ensure we have the full pipeline name format (pipeline-{name}-{suffix})
        # This prevents 404 errors when the run_id is just the pipeline name without the prefix
        if run_id and not run_id.startswith("pipeline-"):
            # Check if we can get the full name from the object_ref
            if "object_ref" in result_data and isinstance(
                result_data["object_ref"], str
            ):
                if result_data["object_ref"].startswith("pipeline-"):
                    # Use the object_ref as it has the correct format
                    run_id = result_data["object_ref"]
                    logger.info(f"Using object_ref as run_id: {run_id}")
            # If last_run contains object_ref with pipeline prefix
            elif "last_run" in result_data and isinstance(
                result_data["last_run"], dict
            ):
                if "object_ref" in result_data["last_run"] and result_data["last_run"][
                    "object_ref"
                ].startswith("pipeline-"):
                    run_id = result_data["last_run"]["object_ref"]
                    logger.info(f"Using last_run.object_ref as run_id: {run_id}")

        if not run_id:
            # If we still don't have a run ID, raise an error
            raise ValueError(
                f"Could not extract run ID from API response: {result_data}"
            )

        logger.info(f"Using run ID from API response: {run_id}")

        return PraxResult(
            run_id=run_id,
            pipeline_name=pipeline_name,
            user=user,
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
        user: str,
        org: str,
        project: str,
        stage: str,
    ) -> Dict[str, Any]:
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
        # According to the OpenAPI spec, the correct endpoint is /api/pipeline-runs/{run_name}
        url = f"{self.base_url}/api/pipeline-runs/{run_id}"

        params = {
            "user": user,
            "org": org,
            "project": project,
            "stage": stage,
        }

        logger.debug(f"Getting run status from: {url} with params {params}")

        try:
            response = requests.get(
                url, params=params, headers=self._get_headers(), timeout=30
            )

            # Check if we got a successful response
            response.raise_for_status()
            result = response.json()
            logger.info(f"Successfully retrieved run status from {url}")
            return result
        except requests.exceptions.RequestException as e:
            error_msg = f"Error getting run status: {str(e)}"
            logger.error(error_msg)

            # Provide a fallback option for development purposes
            if os.environ.get("ROMPY_DEV_MODE") == "1":
                logger.warning("Development mode enabled - returning simulated status")
                return {
                    "status": "Running",
                    "message": "Simulated status for development",
                    "run_id": run_id,
                    "pipeline": pipeline_name,
                }

            # In production, raise the error
            raise

    def get_run_logs(
        self,
        run_id: str,
        pipeline_name: str,
        user: str,
        org: str,
        project: str,
        stage: str,
        task_name: Optional[str] = None,
        follow: bool = False,
        tail: int = 1000,
        stream_to_stdout: bool = False,
        format_logs: bool = True,
        filter_wait_logs: bool = True,
    ) -> Union[Dict[str, Any], str]:
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
            follow: Whether to follow/stream the logs (default: False)
            tail: Number of lines to show from the end of the logs (default: 1000)
            stream_to_stdout: Whether to stream logs directly to stdout (default: False)
            format_logs: Whether to format and clean up log lines by removing pipeline prefixes (default: True)
            filter_wait_logs: Whether to filter out logs from [wait] containers (default: True)

        Returns:
            Dictionary with logs information or string with logs text
            If follow=True and stream_to_stdout=True, prints logs to stdout and returns None
        """
        # According to the OpenAPI spec, the correct endpoint is /api/pipeline-runs/{run_name}/logs
        url = f"{self.base_url}/api/pipeline-runs/{run_id}/logs"

        params = {
            "user": user,
            "org": org,
            "project": project,
            "stage": stage,
            "follow": follow,
            "tail": tail,
        }

        # Add optional parameters
        if task_name:
            params["task"] = task_name

        logger.debug(f"Getting logs from: {url} with params {params}")

        try:
            # Handle streaming logs if follow=True
            if follow and stream_to_stdout:
                logger.info(f"Streaming logs from: {url} with follow=True")
                with requests.get(
                    url,
                    params=params,
                    headers=self._get_headers(),
                    stream=True,
                    timeout=None,
                ) as response:
                    response.raise_for_status()

                    # Process and print the streaming response line by line
                    try:
                        for line in response.iter_lines(decode_unicode=True):
                            if line:
                                if format_logs and "[" in line and "]" in line:
                                    try:
                                        # Extract task info from prefix like [pipeline-name-task/main]
                                        task_info = line.split("[", 1)[1].split("]", 1)[
                                            0
                                        ]
                                        # Get the actual log message (everything after the timestamp)
                                        log_message = line.split("]", 1)[1]

                                        # Extract the subtask name (after the last slash if present)
                                        subtask_name = "unknown"
                                        if "/" in task_info:
                                            subtask_name = task_info.split("/")[-1]

                                        # Extract the main task name from the pipeline ID
                                        # Format is typically: pipeline-name-task-id-run-id/subtask
                                        task_name = "unknown"
                                        if "-" in task_info:
                                            # Try to extract the task name from the pipeline ID
                                            parts = task_info.split("-")
                                            if len(parts) > 1:
                                                for i, part in enumerate(parts):
                                                    # Look for potential task identifiers
                                                    if part in [
                                                        "run",
                                                        "main",
                                                        "prepare",
                                                        "wait",
                                                        "register",
                                                    ]:
                                                        task_name = part
                                                        break

                                        # Skip infrastructure logs if filter_wait_logs is enabled
                                        # This filters out both wait logs and other infrastructure logs
                                        if filter_wait_logs:
                                            # Skip if it's a wait log
                                            re.search(r"\[wait\]", line) is not None
                                            if (
                                                "[wait]" in line
                                                or "[wait]:" in line
                                                or "Task wait [" in line
                                                or "Task run [wait]" in line
                                                or "register [wait]" in line
                                                or "/wait" in line
                                            ):
                                                continue

                                            # Skip task register logs (infrastructure logs)
                                            if "Task register [" in line and (
                                                ": time=" in line or ": 20" in line
                                            ):
                                                continue

                                        # Format and print the filtered log
                                        formatted_line = f"Task {task_name} [{subtask_name}]:{log_message}"
                                        print(formatted_line)
                                    except IndexError:
                                        # If parsing fails, just print the original line
                                        print(line)
                                else:
                                    # Either format_logs is False or no pipeline prefix pattern found
                                    print(line)
                        return None  # Return None as we've printed everything to stdout
                    except KeyboardInterrupt:
                        logger.info("Log streaming stopped by user")
                        return None
            else:
                # Regular non-streaming request
                response = requests.get(
                    url, params=params, headers=self._get_headers(), timeout=30
                )

                response.raise_for_status()

                # Check if the response is JSON or plain text
                content_type = response.headers.get("Content-Type", "")

                if "application/json" in content_type:
                    # Parse as JSON
                    result = response.json()
                    logger.info(f"Successfully retrieved logs as JSON from {url}")

                    # If filter_wait_logs is True, filter out logs from [wait] containers
                    if (
                        filter_wait_logs
                        and "logs" in result
                        and isinstance(result["logs"], str)
                    ):
                        # Simple filtering of wait logs for JSON response
                        filtered_logs = []
                        for line in result["logs"].splitlines():
                            # Check for wait patterns and infrastructure logs
                            skip_line = False

                            # Check if it's a wait log
                            if (
                                "[wait]" in line
                                or "[wait]:" in line
                                or "Task wait [" in line
                                or "Task run [wait]" in line
                                or "register [wait]" in line
                            ):
                                skip_line = True

                            # Check if it's a task register log (infrastructure logs)
                            if "Task register [" in line and (
                                ": time=" in line or ": 20" in line
                            ):
                                skip_line = True

                            if not skip_line:
                                filtered_logs.append(line)
                        result["logs"] = "\n".join(filtered_logs)

                    return result
                else:
                    # Handle as plain text
                    result = response.text
                    logger.info(f"Successfully retrieved logs as text from {url}")

                    # Filter out logs from [wait] containers if enabled
                    if filter_wait_logs:
                        filtered_lines = []
                        for line in result.splitlines():
                            # Skip infrastructure logs - check for both wait and task register logs
                            # Include the line only if it doesn't match our filter patterns
                            skip_line = False

                            # Check if it's a wait log
                            if (
                                "[wait]" in line
                                or "[wait]:" in line
                                or "Task wait [" in line
                                or "Task run [wait]" in line
                                or "register [wait]" in line
                            ):
                                skip_line = True

                            # Check if it's a task register log (infrastructure logs)
                            if "Task register [" in line and (
                                ": time=" in line or ": 20" in line
                            ):
                                skip_line = True

                            if not skip_line:
                                filtered_lines.append(line)
                        result = "\n".join(filtered_lines)

                    return {
                        "logs": result,
                        "run_id": run_id,
                        "pipeline": pipeline_name,
                        "task": task_name if task_name else "main",
                        "content_type": content_type,
                    }

        except requests.exceptions.RequestException as e:
            error_msg = f"Error getting run logs: {str(e)}"
            logger.error(error_msg)

            # Provide a fallback option for development purposes
            if os.environ.get("ROMPY_DEV_MODE") == "1":
                logger.warning("Development mode enabled - returning simulated logs")
                return {
                    "logs": "Simulated logs for development. This would contain the actual logs from the run.",
                    "run_id": run_id,
                    "pipeline": pipeline_name,
                    "task": task_name if task_name else "main",
                }

            # In production, raise the error
            raise

    def download_run_artifacts(
        self,
        run_id: str,
        pipeline_name: str,
        user: str,
        org: str,
        project: str,
        stage: str,
        target_dir: str = "./outputs",
    ) -> List[str]:
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
        # First, check the run status to see if it's completed
        # Artifacts may not be available if the run is still in progress
        try:
            run_status = self.get_run_status(
                run_id=run_id,
                pipeline_name=pipeline_name,
                user=user,
                org=org,
                project=project,
                stage=stage,
            )

            status = run_status.get("status", "")
            logger.info(f"Run status: {status}")

            # If the run isn't completed yet, artifacts may not be available
            if status.lower() not in [
                "completed",
                "succeeded",
                "success",
                "done",
                "finished",
            ]:
                logger.warning(
                    f"Run is not completed (status: {status}). Artifacts may not be available yet."
                )

                # Create the target directory
                os.makedirs(target_dir, exist_ok=True)

                # In development mode or when run is not complete, provide placeholder files
                # If not in development mode, we still want to give an empty response rather than error
                if os.environ.get("ROMPY_DEV_MODE") == "1":
                    logger.warning(
                        "Development mode enabled - creating placeholder artifacts"
                    )
                    # Create placeholder files for development
                    placeholder_paths = [
                        os.path.join(target_dir, f"placeholder_output_{i}.nc")
                        for i in range(1, 3)
                    ]
                    for path in placeholder_paths:
                        with open(path, "w") as f:
                            f.write(
                                f"# Placeholder file for development\n# Real data would be downloaded here for run: {run_id} when status: {status} becomes 'Completed'"
                            )
                    logger.info(f"Created placeholder artifact files in {target_dir}")
                    return placeholder_paths
                else:
                    # Return empty list when not in dev mode and run not complete
                    # This prevents errors for runs that are still in progress
                    logger.info(
                        f"Returning empty artifact list for incomplete run (status: {status})"
                    )
                    return []
        except Exception as e:
            logger.warning(
                f"Could not check run status before downloading artifacts: {str(e)}"
            )

        # Try multiple potential artifact endpoints since it's not clearly defined in the OpenAPI spec
        artifact_endpoints = [
            f"{self.base_url}/api/pipeline-runs/{run_id}/artifacts",  # Following the pattern from logs endpoint
            f"{self.base_url}/api/pipelines/{pipeline_name}/runs/{run_id}/artifacts",  # Traditional pattern
            f"{self.base_url}/api/runs/{run_id}/artifacts",  # Simplified pattern
        ]

        params = {
            "user": user,
            "org": org,
            "project": project,
            "stage": stage,
        }

        artifacts = []
        last_error = None

        # Try each potential endpoint
        for url in artifact_endpoints:
            try:
                logger.debug(f"Getting artifacts list from: {url}")
                response = requests.get(
                    url, params=params, headers=self._get_headers(), timeout=30
                )

                response.raise_for_status()
                artifacts = response.json()
                logger.info(f"Successfully retrieved artifacts list from {url}")
                break  # Found working endpoint, exit the loop
            except requests.exceptions.RequestException as e:
                logger.debug(f"Endpoint {url} failed: {str(e)}")
                last_error = e

        # If no artifacts were found
        if not artifacts:
            error_msg = "No artifacts found or available yet"
            if last_error:
                error_msg = f"Error listing artifacts: {str(last_error)}"
            logger.error(error_msg)

            # Provide a fallback option for development purposes
            if os.environ.get("ROMPY_DEV_MODE") == "1":
                logger.warning(
                    "Development mode enabled - returning simulated artifact paths"
                )
                # Create the target directory
                os.makedirs(target_dir, exist_ok=True)
                # Create empty placeholder files for development
                placeholder_paths = [
                    os.path.join(target_dir, f"placeholder_output_{i}.nc")
                    for i in range(1, 3)
                ]
                for path in placeholder_paths:
                    with open(path, "w") as f:
                        f.write(
                            f"# Placeholder file for development\n# Real data would be downloaded here for run: {run_id}"
                        )

                logger.info(f"Created placeholder artifact files in {target_dir}")
                return placeholder_paths

            # In production, raise the error
            if last_error:
                raise last_error
            else:
                raise ValueError("No artifacts found or available for this run")

        downloaded_files = []

        # Create the target directory if it doesn't exist
        os.makedirs(target_dir, exist_ok=True)

        # Download each artifact
        for artifact in artifacts:
            artifact_name = artifact.get("name")
            if not artifact_name:
                logger.warning(f"Artifact without name: {artifact}")
                continue

            # Try multiple potential download URLs
            download_urls = [
                f"{self.base_url}/api/pipeline-runs/{run_id}/artifacts/{artifact_name}",
                f"{self.base_url}/api/pipelines/{pipeline_name}/runs/{run_id}/artifacts/{artifact_name}",
                f"{self.base_url}/api/runs/{run_id}/artifacts/{artifact_name}",
            ]

            download_success = False
            for download_url in download_urls:
                try:
                    logger.debug(f"Downloading artifact from {download_url}")
                    download_response = requests.get(
                        download_url,
                        params=params,
                        headers=self._get_headers(),
                        stream=True,
                        timeout=30,  # Longer timeout for downloads
                    )

                    download_response.raise_for_status()

                    # Save to file
                    target_path = os.path.join(target_dir, f"{artifact_name}")
                    with open(target_path, "wb") as f:
                        for chunk in download_response.iter_content(chunk_size=8192):
                            f.write(chunk)

                    downloaded_files.append(target_path)
                    logger.info(f"Downloaded artifact {artifact_name} to {target_path}")
                    download_success = True
                    break  # Found working download URL, exit the loop
                except requests.exceptions.RequestException as e:
                    logger.debug(f"Download from {download_url} failed: {str(e)}")

            if not download_success:
                error_msg = (
                    f"Failed to download artifact {artifact_name} from any endpoint"
                )
                logger.error(error_msg)

                # Provide a fallback option for development purposes
                if os.environ.get("ROMPY_DEV_MODE") == "1":
                    logger.warning(
                        f"Development mode enabled - skipping failed artifact download for {artifact_name}"
                    )
                    continue

                # In production, raise the error
                raise ValueError(f"Could not download artifact {artifact_name}")

        return downloaded_files
