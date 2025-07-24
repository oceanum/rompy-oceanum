"""
Pytest tests for the PraxClient class.
"""

import os
import pytest
from unittest.mock import MagicMock, patch

from rompy_oceanum.client import PraxClient, PraxResult


class TestPraxClient:
    """Test the PraxClient class."""

    def test_init(self, mock_prax_token):
        """Test initialization of PraxClient."""
        # Default initialization with config
        from rompy_oceanum.config import PraxConfig
        prax_config = PraxConfig(
            base_url="https://prax.oceanum.io",
            token="test-token",
            org="test-org",
            project="test-project",
            stage="dev",
            timeout=3600
        )
        client = PraxClient(config=prax_config)
        assert client.config.base_url == "https://prax.oceanum.io"
        assert client.config.token == "test-token"

        # Custom initialization
        custom_config = PraxConfig(
            base_url="https://custom.prax.io",
            token="custom-token",
            org="custom-org",
            project="custom-project",
            stage="dev",
            timeout=3600
        )
        client = PraxClient(config=custom_config)
        assert client.config.base_url == "https://custom.prax.io"
        assert client.config.token == "custom-token"

    def test_get_headers(self, mock_prax_token):
        """Test header generation for API requests."""
        from rompy_oceanum.config import PraxConfig
        prax_config = PraxConfig(
            base_url="https://prax.oceanum.io",
            token="test-token",
            org="test-org",
            project="test-project",
            stage="dev",
            timeout=3600
        )
        client = PraxClient(config=prax_config)
        headers = client.wrapper._get_headers()  # Assuming _get_headers is on the wrapper
        assert headers == {
            "accept": "application/json",
            "Authorization": "test-token",
            "Content-Type": "application/json",
        }

    def test_get_headers_no_token(self):
        """Test header generation fails without token."""
        from rompy_oceanum.config import PraxConfig
        prax_config = PraxConfig(
            base_url="https://prax.oceanum.io",
            token=None,
            org="test-org",
            project="test-project",
            stage="dev",
            timeout=3600
        )
        client = PraxClient(config=prax_config)
        with pytest.raises(ValueError, match="No Prax token available"):
            client.wrapper._get_headers()

    def test_submit_pipeline(self, mock_prax_token, mock_requests):
        """Test submitting a pipeline to Prax."""
        from rompy_oceanum.config import PraxConfig
        prax_config = PraxConfig(
            base_url="https://prax.oceanum.io",
            token="test-token",
            org="test-org",
            project="test-project",
            stage="dev",
            timeout=3600
        )
        client = PraxClient(config=prax_config)
        result_id = client.submit_pipeline(
            pipeline_name="test-pipeline",
            parameters={"test-param": "test-value"}
        )
        assert isinstance(result_id, str)
        # Additional assertions can be added if the wrapper is mocked

    def test_submit_pipeline_error(self, mock_prax_token, mock_requests):
        """Test error handling when submitting a pipeline."""
        mock_requests["response"].status_code = 400
        mock_requests["response"].raise_for_status.side_effect = Exception("API error")

        client = PraxClient()
        with pytest.raises(Exception, match="API error"):
            client.submit_pipeline(
                pipeline_name="test-pipeline",
                user="test-user",
                org="test-org",
                project="test-project",
                stage="dev",
                parameters={"test-param": "test-value"}
            )

    def test_get_run_status(self, mock_prax_token, mock_requests):
        """Test getting the status of a pipeline run."""
        client = PraxClient()
        status = client.get_run_status(
            run_id="test-run-id",
            pipeline_name="test-pipeline",
            user="test-user",
            org="test-org",
            project="test-project",
            stage="dev"
        )

        # Check status result
        assert status == {"name": "test-run-id", "status": "Running"}

        # Check API call
        mock_requests["get"].assert_called_once()
        args, kwargs = mock_requests["get"].call_args
        assert args[0] == "https://prax.oceanum.io/api/pipelines/test-pipeline/runs/test-run-id"
        assert kwargs["params"] == {
            "user": "test-user",
            "org": "test-org",
            "project": "test-project",
            "stage": "dev",
        }

    def test_get_run_logs(self, mock_prax_token, mock_requests):
        """Test getting logs from a pipeline run."""
        client = PraxClient()
        logs = client.get_run_logs(
            run_id="test-run-id",
            pipeline_name="test-pipeline",
            user="test-user",
            org="test-org",
            project="test-project",
            stage="dev"
        )

        # Check logs result
        assert logs == {"name": "test-run-id", "status": "Running"}

        # Check API call
        mock_requests["get"].assert_called_once()
        args, kwargs = mock_requests["get"].call_args
        assert args[0] == "https://prax.oceanum.io/api/pipelines/test-pipeline/runs/test-run-id/logs"

        # Test with task name
        mock_requests["get"].reset_mock()
        client.get_run_logs(
            run_id="test-run-id",
            pipeline_name="test-pipeline",
            user="test-user",
            org="test-org",
            project="test-project",
            stage="dev",
            task_name="test-task"
        )

        args, kwargs = mock_requests["get"].call_args
        assert args[0] == "https://prax.oceanum.io/api/pipelines/test-pipeline/runs/test-run-id/tasks/test-task/logs"

    @patch("os.path.join", return_value="/tmp/test-artifact")
    @patch("os.makedirs")
    @patch("builtins.open", new_callable=MagicMock)
    def test_download_run_artifacts(self, mock_open, mock_makedirs, mock_path_join,
                                   mock_prax_token, mock_requests):
        """Test downloading artifacts from a pipeline run."""
        # Set up mock response for artifacts list
        mock_requests["response"].json.return_value = [
            {"name": "test-artifact"}
        ]

        # Create a file handle mock for the context manager
        mock_file = MagicMock()
        mock_open.return_value.__enter__.return_value = mock_file

        # Set up mock response for artifact download
        mock_download_response = MagicMock()
        mock_download_response.status_code = 200
        mock_download_response.iter_content.return_value = [b"test content"]

        # Make sure get returns our download mock for the artifact download
        mock_requests["get"].side_effect = [
            mock_requests["response"],  # First call for listing artifacts
            mock_download_response      # Second call for downloading
        ]

        with patch("rompy_oceanum.client.os.makedirs") as patched_makedirs:
            # Download artifacts
            client = PraxClient()
            target_dir = "/tmp/artifacts"

            downloaded_files = client.download_run_artifacts(
                run_id="test-run-id",
                pipeline_name="test-pipeline",
                user="test-user",
                org="test-org",
                project="test-project",
                stage="dev",
                target_dir=target_dir
            )

            # Check result
            assert downloaded_files == ["/tmp/test-artifact"]

            # Check directory creation
            patched_makedirs.assert_called_once_with(target_dir, exist_ok=True)

        # Check file write
        mock_open.assert_called_once_with("/tmp/test-artifact", "wb")

        # Verify file content was written
        mock_file.write.assert_called_once_with(b"test content")
