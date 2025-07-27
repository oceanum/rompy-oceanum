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
        # Default initialization with environment variable
        client = PraxClient()
        assert client.base_url == "https://prax.oceanum.io"
        assert client.token == "test-token"

        # Custom initialization
        client = PraxClient(base_url="https://custom.prax.io", token="custom-token")
        assert client.base_url == "https://custom.prax.io"
        assert client.token == "custom-token"

    def test_get_headers(self, mock_prax_token):
        """Test header generation for API requests."""
        client = PraxClient()
        headers = client._get_headers()
        assert headers == {
            "accept": "application/json",
            "Authorization": "Bearer test-token",
            "Content-Type": "application/json",
        }

    def test_get_headers_no_token(self):
        """Test header generation fails without token."""
        if "PRAX_TOKEN" in os.environ:
            del os.environ["PRAX_TOKEN"]

        with pytest.raises(ValueError, match="No Prax token available|Missing required configuration"):
            client = PraxClient(token=None)
            client._get_headers()

    def test_submit_pipeline(self, mock_prax_token, mock_requests):
        """Test submitting a pipeline to Prax."""
        # Mock the _make_request method to return a specific response for submit
        with patch("rompy_oceanum.client.PraxClient._make_request") as mock_make_request:
            mock_make_request.return_value = {"run_id": "test-run-id"}
            
            client = PraxClient()
            result = client.submit_pipeline(
                pipeline_name="test-pipeline",
                user="test-user",
                org="test-org",
                project="test-project",
                stage="dev",
                parameters={"test-param": "test-value"}
            )

            # Check result object
            assert isinstance(result, PraxResult)
            assert result.run_id == "test-run-id"
            assert result.pipeline_name == "test-pipeline"
            assert result.user == "test-user"
            assert result.org == "test-org"
            assert result.project == "test-project"
            assert result.stage == "dev"
            assert result.status == "submitted"

    def test_submit_pipeline_error(self, mock_prax_token, mock_requests):
        """Test error handling when submitting a pipeline."""
        # Mock the _make_request method to raise an exception
        with patch("rompy_oceanum.client.PraxClient._make_request") as mock_make_request:
            mock_make_request.side_effect = Exception("403 Client Error")
            
            client = PraxClient()
            with pytest.raises(Exception, match="403 Client Error"):
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

    @patch("os.path.join", return_value="/tmp/test-artifact")
    @patch("os.makedirs")
    @patch("builtins.open", new_callable=MagicMock)
    def test_download_run_artifacts(self, mock_open, mock_makedirs, mock_path_join,
                                   mock_prax_token, mock_requests):
        """Test downloading artifacts from a pipeline run."""
        # Mock the requests.get method directly for artifact download
        mock_download_response = MagicMock()
        mock_download_response.status_code = 200
        mock_download_response.iter_content.return_value = [b"test content"]
        
        with patch("rompy_oceanum.client.requests.get", return_value=mock_download_response):
            with patch("rompy_oceanum.client.PraxClient._make_request") as mock_make_request:
                # First call returns artifact list, second call returns status
                mock_make_request.side_effect = [
                    [{"name": "test-artifact"}],  # Artifact list
                    {"name": "test-run-id", "status": "Running"}  # Status response
                ]
                
                # Create a file handle mock for the context manager
                mock_file = MagicMock()
                mock_open.return_value.__enter__.return_value = mock_file

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
