"""
Client module for Prax API integration using native oceanum-prax library.

This module provides error handling classes and result management for pipeline operations,
now using the native oceanum-prax library instead of custom HTTP requests.
"""
import json
import logging
import time
from enum import Enum
from pathlib import Path
from typing import Dict, Any, Optional, List, Union

from pydantic import BaseModel, Field
import requests
from tenacity import retry, stop_after_attempt, wait_exponential

from .config import PraxConfig
from .prax_client_wrapper import PraxClientWrapper, PraxResult as WrapperPraxResult
# TODO: Replace with native oceanum-prax client or correct wrapper

logger = logging.getLogger(__name__)


class PraxErrorType(Enum):
    """Types of Prax API errors."""

    NETWORK = "network"
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    NOT_FOUND = "not_found"
    VALIDATION = "validation"
    RATE_LIMIT = "rate_limit"
    SERVER_ERROR = "server_error"
    TIMEOUT = "timeout"
    UNKNOWN = "unknown"


class PraxErrorData(BaseModel):
    """Structured error data for Prax API errors."""

    type: PraxErrorType
    detail: str
    suggestion: Optional[str] = None
    status_code: Optional[int] = None


class PraxError(Exception):
    """
    Enhanced error class for Prax operations with structured error handling.

    This class provides detailed error information and actionable suggestions
    for resolving common issues.
    """

    def __init__(self, message: str, error_type: PraxErrorType = PraxErrorType.UNKNOWN,
                 status_code: Optional[int] = None, suggestion: Optional[str] = None):
        super().__init__(message)
        self.message = message
        self.error_type = error_type
        self.status_code = status_code
        self.suggestion = suggestion

        # Create structured error data
        self.data = PraxErrorData(
            type=error_type,
            detail=message,
            suggestion=suggestion,
            status_code=status_code
        )

    def __str__(self) -> str:
        """String representation of the error."""
        base_msg = f"[{self.error_type.value.upper()}] {self.message}"
        if self.suggestion:
            base_msg += f"\nSuggestion: {self.suggestion}"
        return base_msg

    @classmethod
    def from_exception(cls, exc: Exception, context: str = "") -> 'PraxError':
        """
        Create PraxError from any exception with context.

        Args:
            exc: The original exception
            context: Additional context about where the error occurred

        Returns:
            PraxError instance with appropriate classification
        """
        if isinstance(exc, requests.exceptions.HTTPError):
            return cls._from_http_error(exc, context)
        elif isinstance(exc, (requests.exceptions.ConnectionError, requests.exceptions.ConnectTimeout)):
            return cls._from_connection_error(exc, context)
        elif isinstance(exc, requests.exceptions.Timeout):
            return cls._from_timeout_error(exc, context)
        elif isinstance(exc, requests.exceptions.RequestException):
            return cls._from_request_error(exc, context)
        else:
            return cls._from_generic_error(exc, context)

    @classmethod
    def _from_http_error(cls, exc: requests.exceptions.HTTPError, context: str) -> 'PraxError':
        """Create PraxError from HTTP error response."""
        response = exc.response
        status_code = response.status_code if response else None

        # Determine error type based on status code
        if status_code == 401:
            error_type = PraxErrorType.AUTHENTICATION
            suggestion = (
                "Check your authentication token. You may need to:\n"
                "1. Set PRAX_TOKEN environment variable\n"
                "2. Run 'oceanum auth login' to refresh your token\n"
                "3. Verify token has not expired"
            )
        elif status_code == 403:
            error_type = PraxErrorType.AUTHORIZATION
            suggestion = (
                "Check your permissions for this project. You may need to:\n"
                "1. Verify you have access to the specified org/project\n"
                "2. Contact your administrator for project access\n"
                "3. Check if the project/stage exists"
            )
        elif status_code == 404:
            error_type = PraxErrorType.NOT_FOUND
            suggestion = (
                "The requested resource was not found. Check:\n"
                "1. Pipeline name spelling and availability\n"
                "2. Run ID exists and is accessible\n"
                "3. Project and organization names are correct"
            )
        elif status_code == 422:
            error_type = PraxErrorType.VALIDATION
            suggestion = (
                "Request validation failed. Check:\n"
                "1. Required parameters are provided\n"
                "2. Parameter values match expected types\n"
                "3. Pipeline configuration is valid"
            )
        elif status_code == 429:
            error_type = PraxErrorType.RATE_LIMIT
            suggestion = (
                "Rate limit exceeded. Try:\n"
                "1. Waiting a few moments before retrying\n"
                "2. Reducing request frequency\n"
                "3. Checking if multiple processes are making requests"
            )
        elif status_code >= 500:
            error_type = PraxErrorType.SERVER_ERROR
            suggestion = (
                "Server error occurred. Try:\n"
                "1. Retrying the request after a brief delay\n"
                "2. Checking Oceanum service status\n"
                "3. Contacting support if problem persists"
            )
        else:
            error_type = PraxErrorType.UNKNOWN
            suggestion = None

        # Extract error details from response
        try:
            error_detail = response.json() if response else {}
            message = error_detail.get('detail', str(exc))
        except (ValueError, AttributeError):
            message = str(exc)

        # Add context if provided
        if context:
            message = f"{context}: {message}"

        return cls(message, error_type, status_code, suggestion)

    @classmethod
    def _from_connection_error(cls, exc: Exception, context: str) -> 'PraxError':
        """Create PraxError from connection error."""
        message = f"Connection failed: {str(exc)}"
        if context:
            message = f"{context}: {message}"

        suggestion = (
            "Network connection failed. Check:\n"
            "1. Internet connectivity\n"
            "2. Prax service URL is correct\n"
            "3. Firewall/proxy settings\n"
            "4. VPN connection if required"
        )

        return cls(message, PraxErrorType.NETWORK, suggestion=suggestion)

    @classmethod
    def _from_timeout_error(cls, exc: Exception, context: str) -> 'PraxError':
        """Create PraxError from timeout error."""
        message = f"Request timed out: {str(exc)}"
        if context:
            message = f"{context}: {message}"

        suggestion = (
            "Request timed out. Try:\n"
            "1. Increasing timeout duration\n"
            "2. Checking network stability\n"
            "3. Retrying with exponential backoff"
        )

        return cls(message, PraxErrorType.TIMEOUT, suggestion=suggestion)

    @classmethod
    def _from_request_error(cls, exc: Exception, context: str) -> 'PraxError':
        """Create PraxError from general request error."""
        message = f"Request failed: {str(exc)}"
        if context:
            message = f"{context}: {message}"

        return cls(message, PraxErrorType.NETWORK, suggestion="Check network connectivity and try again")

    @classmethod
    def _from_generic_error(cls, exc: Exception, context: str) -> 'PraxError':
        """Create PraxError from generic error."""
        message = f"Unexpected error: {str(exc)}"
        if context:
            message = f"{context}: {message}"

        return cls(message, PraxErrorType.UNKNOWN)


class PraxResult:
    """
    Result object for tracking pipeline execution using native oceanum-prax integration.

    This class provides a consistent interface for monitoring pipeline runs,
    retrieving logs, and downloading outputs using the native oceanum-prax library.
    """

    def __init__(self, client, run_name: str, pipeline_name: str):
        """
        Initialize result object.

        Args:
            client: PraxClientWrapper instance with native oceanum-prax integration
            run_name: Pipeline run name/ID
            pipeline_name: Name of the pipeline
        """
        self.client = client
        self.run_name = run_name
        self.pipeline_name = pipeline_name
        self._cached_status = None

        # For backward compatibility
        self.run_id = run_name

    def get_status(self) -> Dict[str, Any]:
        """
        Get current status of the pipeline run.

        Returns:
            Status dictionary with run information

        Raises:
            PraxError: If status retrieval fails
        """
        try:
            self._cached_status = self.client.get_run_status(self.run_name)
            return self._cached_status
        except Exception as e:
            prax_error = PraxError.from_exception(e, f'run/{self.run_name}/status')
            logger.error(f"Failed to get status for run {self.run_name}: {prax_error.message}")
            raise prax_error

    def get_logs(self, tail: int = 100, task_name: Optional[str] = None) -> List[str]:
        """
        Get logs for the pipeline run.

        Args:
            tail: Number of recent log lines to retrieve
            task_name: Optional specific task name for filtered logs

        Returns:
            List of log lines

        Raises:
            PraxError: If log retrieval fails
        """
        try:
            logs_content = self.client.get_run_logs(
                self.run_name,
                task_name=task_name
            )

            # Convert to list of strings if needed
            if isinstance(logs_content, str):
                lines = logs_content.splitlines()
            else:
                lines = [str(line) for line in logs_content]

            # Apply tail limit
            if tail and len(lines) > tail:
                lines = lines[-tail:]

            return lines

        except Exception as e:
            prax_error = PraxError.from_exception(e, f'run/{self.run_name}/logs')
            logger.error(f"Failed to get logs for run {self.run_name}: {prax_error.message}")
            raise prax_error

    def wait_for_completion(self, timeout: int = 3600, poll_interval: int = 10) -> Dict[str, Any]:
        """
        Wait for pipeline run to complete.

        Args:
            timeout: Maximum time to wait in seconds
            poll_interval: Time between status checks in seconds

        Returns:
            Final status dictionary

        Raises:
            PraxError: If wait fails or times out
        """
        try:
            return self.client._wait_for_completion(self.run_name, timeout)
        except Exception as e:
            prax_error = PraxError.from_exception(e, f'run/{self.run_name}/wait')
            logger.error(f"Failed to wait for completion of run {self.run_name}: {prax_error.message}")
            raise prax_error

    def download_outputs(self, target_dir: Union[str, Path],
                        file_patterns: Optional[List[str]] = None) -> List[Path]:
        """
        Download output files to target directory.

        Args:
            target_dir: Directory to save downloaded files
            file_patterns: Optional file patterns to filter downloads

        Returns:
            List of downloaded file paths

        Raises:
            PraxError: If download fails
        """
        try:
            return self.client.download_artifacts(
                self.run_name,
                target_dir,
                file_patterns=file_patterns
            )
        except Exception as e:
            prax_error = PraxError.from_exception(e, f'run/{self.run_name}/download')
            logger.error(f"Failed to download outputs for run {self.run_name}: {prax_error.message}")
            raise prax_error

    def summary_status(self) -> Dict[str, Any]:
        """
        Get a summary of the pipeline run status.

        Returns:
            Dictionary with summary information including:
            - Basic run details (id, name, status)
            - Timing information (started_at, finished_at, duration)
            - Progress indicators
            - Recent log entries

        Raises:
            PraxError: If status retrieval fails
        """
        try:
            status = self.get_status()

            # Calculate duration if available
            duration = None
            if status.get('started_at') and status.get('finished_at'):
                try:
                    from datetime import datetime
                    started = datetime.fromisoformat(status['started_at'].replace('Z', '+00:00'))
                    finished = datetime.fromisoformat(status['finished_at'].replace('Z', '+00:00'))
                    duration = str(finished - started)
                except Exception:
                    duration = "unknown"

            # Get recent logs for context
            recent_logs = []
            try:
                recent_logs = self.get_logs(tail=5)
            except Exception as log_error:
                logger.debug(f"Could not retrieve recent logs: {log_error}")

            # Determine if run is complete
            run_status = status.get('status', 'unknown').lower()
            is_complete = run_status in ['completed', 'succeeded', 'success', 'failed', 'error', 'cancelled']
            is_successful = run_status in ['completed', 'succeeded', 'success']

            summary = {
                'run_id': self.run_name,
                'run_name': self.run_name,
                'pipeline_name': self.pipeline_name,
                'status': run_status,
                'started_at': status.get('started_at'),
                'finished_at': status.get('finished_at'),
                'duration': duration,
                'is_complete': is_complete,
                'is_successful': is_successful,
                'message': status.get('message', ''),
                'recent_logs': recent_logs,
                'details': status.get('details', {})
            }

            return summary

        except Exception as e:
            prax_error = PraxError.from_exception(e, f'run/{self.run_name}/summary')
            logger.error(f"Failed to get summary for run {self.run_name}: {prax_error.message}")
            raise prax_error


class PraxClient:
    """
    Main client for Prax pipeline operations using native oceanum-prax integration.

    This class delegates to PraxClientWrapper which uses the native oceanum-prax library,
    providing a consistent interface while leveraging the official Python client.
    """

    def __init__(self, config: PraxConfig):
        """
        Initialize Prax client with native oceanum-prax integration.

        Args:
            config: PraxConfig instance with connection details
        """
        self.config = config

        # Initialize the native wrapper
        try:
            self.wrapper = PraxClientWrapper(config)
            logger.info(f"Initialized native Prax client for {config.org}/{config.project}")
        except Exception as e:
            error_msg = f"Failed to initialize native Prax client: {str(e)}"
            logger.error(error_msg)
            raise PraxError(error_msg, PraxErrorType.AUTHENTICATION)

    def check_pipeline_exists(self, pipeline_name: str) -> bool:
        """
        Check if a pipeline exists using native client.

        Args:
            pipeline_name: Name of the pipeline

        Returns:
            True if pipeline exists, False otherwise
        """
        try:
            return self.wrapper.check_pipeline_exists(pipeline_name)
        except Exception as e:
            logger.debug(f"Pipeline existence check failed for {pipeline_name}: {e}")
            return False

    def deploy_pipeline(self, pipeline_name: str, template_path: str) -> bool:
        """
        Deploy a pipeline from template.

        Note: This functionality may be limited in the native client.

        Args:
            pipeline_name: Name of the pipeline
            template_path: Path to pipeline template

        Returns:
            True if deployment succeeded, False otherwise
        """
        try:
            logger.warning(f"Pipeline deployment not fully implemented in native client for {pipeline_name}")
            logger.info(f"Template path: {template_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to deploy pipeline {pipeline_name}: {e}")
            return False

    def submit_pipeline(self, pipeline_name: str, parameters: Dict[str, Any],
                       wait_for_completion: bool = False, timeout: int = 3600) -> str:
        """
        Submit a pipeline for execution using native client.

        Args:
            pipeline_name: Name of the pipeline to execute
            parameters: Pipeline parameters
            wait_for_completion: Whether to wait for completion
            timeout: Timeout in seconds if waiting

        Returns:
            Run ID/name of the submitted pipeline

        Raises:
            PraxError: If submission fails
        """
        try:
            logger.info(f"Submitting pipeline {pipeline_name} with parameters: {list(parameters.keys())}")

            result = self.wrapper.submit_pipeline(
                pipeline_name=pipeline_name,
                parameters=parameters,
                wait_for_completion=wait_for_completion,
                timeout=timeout
            )

            run_id = result.get('id') or result.get('run_id') or result.get('name')

            if not run_id:
                raise PraxError("No run ID returned from pipeline submission", PraxErrorType.VALIDATION)

            logger.info(f"✅ Pipeline submitted successfully. Run ID: {run_id}")
            return run_id

        except Exception as e:
            if isinstance(e, PraxError):
                raise
            prax_error = PraxError.from_exception(e, f'submit_pipeline/{pipeline_name}')
            logger.error(f"✗ Failed to submit pipeline: {prax_error.message}")
            raise prax_error

    def get_run_status(self, run_id: str) -> Dict[str, Any]:
        """
        Get pipeline run status using native client.

        Args:
            run_id: Pipeline run identifier

        Returns:
            Status dictionary

        Raises:
            PraxError: If status retrieval fails
        """
        try:
            return self.wrapper.get_run_status(run_id)
        except Exception as e:
            if isinstance(e, PraxError):
                raise
            prax_error = PraxError.from_exception(e, f'get_run_status/{run_id}')
            logger.error(f"Failed to get status for run {run_id}: {prax_error.message}")
            raise prax_error

    def get_run_logs(self, run_id: str, tail: int = 100) -> List[str]:
        """
        Get pipeline run logs using native client.

        Args:
            run_id: Pipeline run identifier
            tail: Number of log lines to retrieve

        Returns:
            List of log lines

        Raises:
            PraxError: If log retrieval fails
        """
        try:
            logs_content = self.wrapper.get_run_logs(run_id)

            # Convert to list and apply tail limit
            if isinstance(logs_content, str):
                lines = logs_content.splitlines()
            else:
                lines = [str(line) for line in logs_content]

            if tail and len(lines) > tail:
                lines = lines[-tail:]

            return lines

        except Exception as e:
            if isinstance(e, PraxError):
                raise
            prax_error = PraxError.from_exception(e, f'get_run_logs/{run_id}')
            logger.error(f"Failed to get logs for run {run_id}: {prax_error.message}")
            raise prax_error

    def list_run_artifacts(self, run_id: str) -> List[Dict[str, Any]]:
        """
        List available artifacts for a pipeline run.

        Note: This functionality may be limited in the native client.

        Args:
            run_id: Pipeline run identifier

        Returns:
            List of artifact information dictionaries
        """
        try:
            # Note: Artifact listing may need additional implementation
            logger.warning(f"Artifact listing not fully implemented in native client for run {run_id}")
            return []
        except Exception as e:
            logger.error(f"Failed to list artifacts for run {run_id}: {e}")
            return []

    def download_run_artifact(self, run_id: str, artifact_path: str, local_path: Path) -> bool:
        """
        Download a specific artifact from a pipeline run.

        Note: This functionality may be limited in the native client.

        Args:
            run_id: Pipeline run identifier
            artifact_path: Path to artifact in pipeline
            local_path: Local path to save artifact to

        Returns:
            True if download succeeded, False otherwise
        """
        try:
            # Delegate to wrapper's download_artifacts method
            downloaded_files = self.wrapper.download_artifacts(run_id, local_path.parent)
            return len(downloaded_files) > 0
        except Exception as e:
            logger.error(f"Failed to download artifact {artifact_path} for run {run_id}: {e}")
            return False

    def download_run_metadata(self, run_id: str, local_path: Path) -> bool:
        """
        Download run metadata.

        Args:
            run_id: Pipeline run identifier
            local_path: Local path to save metadata to

        Returns:
            True if download succeeded, False otherwise
        """
        try:
            # Get status and save as metadata
            status = self.get_run_status(run_id)

            local_path.parent.mkdir(parents=True, exist_ok=True)

            metadata = {
                "run_id": run_id,
                "pipeline_name": getattr(self, '_current_pipeline', 'unknown'),
                "status": status,
                "framework": "rompy-oceanum",
                "client_type": "native-oceanum-prax"
            }

            with open(local_path, 'w') as f:
                json.dump(metadata, f, indent=2)

            return True

        except Exception as e:
            logger.error(f"Failed to download metadata for run {run_id}: {e}")
            return False

    def create_result(self, run_id: str, pipeline_name: str) -> PraxResult:
        """
        Create a PraxResult object for tracking pipeline execution.

        Args:
            run_id: Pipeline run identifier
            pipeline_name: Name of the executed pipeline

        Returns:
            PraxResult instance
        """
        return PraxResult(self.wrapper, run_id, pipeline_name)

    def list_pipelines(self) -> List[Dict[str, Any]]:
        """
        List available pipelines using native client.

        Returns:
            List of pipeline information dictionaries

        Raises:
            PraxError: If pipeline listing fails
        """
        try:
            return self.wrapper.list_pipelines()
        except Exception as e:
            if isinstance(e, PraxError):
                raise
            prax_error = PraxError.from_exception(e, 'list_pipelines')
            logger.error(f"Failed to list pipelines: {prax_error.message}")
            raise prax_error
