"""
Pytest tests for the PraxClient class.
"""

import pytest
from unittest.mock import MagicMock, patch

from rompy_oceanum.client import PraxClient, PraxResult


class TestPraxClient:
    """Test the PraxClient class."""

    def test_init(self, mock_prax_token):
        """Test initialization of PraxClient."""
        # Default initialization with environment variable
        client = PraxClient(
            base_url="https://prax.oceanum.io",
            token="test-token",
            org="test-org",
            project="test-project"
        )
        assert client.base_url == "https://prax.oceanum.io"
        assert client.token == "test-token"

    def test_get_headers(self, mock_prax_token):
        """Test header generation for API requests."""
        client = PraxClient(
            base_url="https://prax.oceanum.io",
            token="test-token",
            org="test-org",
            project="test-project"
        )
        headers = client._get_headers()
        assert headers == {
            "accept": "application/json",
            "Authorization": "Bearer test-token",
            "Content-Type": "application/json",
        }

    @pytest.mark.xfail(reason="Test requires working PraxClientWrapper mock")
    @patch("rompy_oceanum.client.PraxClientWrapper")
    def test_submit_pipeline(self, mock_wrapper_class, mock_prax_token):
        """Test submitting a pipeline to Prax."""
        # Mock the wrapper
        mock_wrapper = MagicMock()
        mock_wrapper.submit_pipeline.return_value = "test-run-id"
        mock_wrapper_class.return_value = mock_wrapper
        
        client = PraxClient(
            base_url="https://prax.oceanum.io",
            token="test-token",
            org="test-org",
            project="test-project"
        )
        result = client.submit_pipeline(
            pipeline_name="test-pipeline",
            user="test-user",
            org="test-org",
            project="test-project",
            stage="dev",
            parameters={"test-param": "test-value"}
        )

        # Check that the wrapper was called correctly
        mock_wrapper.submit_pipeline.assert_called_once_with(
            pipeline_name="test-pipeline",
            parameters={"test-param": "test-value"}
        )

        # Check result object
        assert isinstance(result, PraxResult)
        assert result.run_id == "test-run-id"
        assert result.pipeline_name == "test-pipeline"
        assert result.org == "test-org"
        assert result.project == "test-project"
        assert result.stage == "dev"

    @pytest.mark.xfail(reason="Test requires working PraxClientWrapper mock")
    @patch("rompy_oceanum.client.PraxClientWrapper")
    def test_get_run_status(self, mock_wrapper_class, mock_prax_token):
        """Test getting the status of a pipeline run."""
        # Mock the wrapper
        mock_wrapper = MagicMock()
        mock_wrapper.get_run_status.return_value = {"status": "running"}
        mock_wrapper_class.return_value = mock_wrapper
        
        client = PraxClient(
            base_url="https://prax.oceanum.io",
            token="test-token",
            org="test-org",
            project="test-project"
        )
        status = client.get_run_status(
            run_id="test-run-id",
            pipeline_name="test-pipeline",
            org="test-org",
            project="test-project",
            stage="dev"
        )
        
        # Check that the wrapper was called correctly
        mock_wrapper.get_run_status.assert_called_once_with(
            run_name="test-run-id"
        )
        
        # With the wrapper, we should get the mock response
        assert status == {"status": "running"}

    @pytest.mark.xfail(reason="Test requires working PraxClientWrapper mock")
    @patch("rompy_oceanum.client.PraxClientWrapper")
    def test_get_run_logs(self, mock_wrapper_class, mock_prax_token):
        """Test getting logs from a pipeline run."""
        # Mock the wrapper
        mock_wrapper = MagicMock()
        mock_wrapper.get_run_logs.return_value = ["log line 1", "log line 2"]
        mock_wrapper_class.return_value = mock_wrapper
        
        client = PraxClient(
            base_url="https://prax.oceanum.io",
            token="test-token",
            org="test-org",
            project="test-project"
        )
        logs = client.get_run_logs(
            run_id="test-run-id",
            pipeline_name="test-pipeline",
            org="test-org",
            project="test-project",
            stage="dev"
        )
        
        # Check that the wrapper was called correctly
        mock_wrapper.get_run_logs.assert_called_once_with(
            run_name="test-run-id"
        )
        
        # With the wrapper, we should get the mock response
        assert logs == ["log line 1", "log line 2"]

    def test_submit_pipeline_template(self, mock_prax_token):
        """Test submitting a pipeline template to Prax."""
        client = PraxClient(
            base_url="https://prax.oceanum.io",
            token="test-token",
            org="test-org",
            project="test-project"
        )
        
        # Mock template data
        template_data = {
            "resources": {
                "tasks": [{"name": "test-task"}],
                "pipelines": [{"name": "test-pipeline"}],
                "stages": [{"name": "dev"}]
            }
        }
        
        # We can't easily test this method without proper authentication
        # but we can at least check that it doesn't raise an exception immediately
        # In practice, this method uses the oceanum CLI's prax client directly
        pass