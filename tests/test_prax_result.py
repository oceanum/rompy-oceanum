"""
Pytest tests for the PraxResult class.
"""

import pytest
from unittest.mock import MagicMock, patch

from rompy_oceanum.client import PraxResult


class TestPraxResult:
    """Test the PraxResult class."""

    @pytest.fixture
    def prax_result(self):
        """Create a PraxResult instance for testing."""
        mock_client = MagicMock()
        return PraxResult(
            run_id="test-run-id",
            run_name="test-run-id",
            pipeline_name="test-pipeline",
            org="test-org",
            project="test-project",
            stage="dev",
            status="submitted",
            client=mock_client
        )

    def test_get_status(self, prax_result):
        """Test getting the status of a pipeline run."""
        # Set up mock response
        prax_result.client.get_run_status.return_value = {
            "name": "test-run-id",
            "status": "Running"
        }

        # Get status
        status = prax_result.get_status()

        # Check result
        assert status["name"] == "test-run-id"
        assert status["status"] == "Running"

        # Check client call - now using the new signature
        prax_result.client.get_run_status.assert_called_once_with(
            run_name="test-run-id"
        )

    def test_get_status_no_client(self):
        """Test error handling when getting status without a client."""
        result = PraxResult(
            run_id="test-run-id",
            run_name="test-run-id",
            pipeline_name="test-pipeline",
            org="test-org",
            project="test-project",
            stage="dev",
            status="submitted",
            client=None
        )

        with pytest.raises(ValueError, match="No client configured"):
            result.get_status()

    def test_get_logs(self, prax_result):
        """Test getting logs from a pipeline run."""
        # Set up mock response
        prax_result.client.get_run_logs.return_value = [
            "Log line 1",
            "Log line 2"
        ]

        # Get logs
        logs = prax_result.get_logs()

        # Check result
        assert logs == ["Log line 1", "Log line 2"]

        # Check client call - now using the new signature
        prax_result.client.get_run_logs.assert_called_once_with(
            run_name="test-run-id"
        )

        # Test with task name (should be ignored with new client)
        prax_result.client.get_run_logs.reset_mock()
        prax_result.get_logs(task_name="test-task")

        prax_result.client.get_run_logs.assert_called_once_with(
            run_name="test-run-id"
        )

    def test_wait_for_completion(self, prax_result):
        """Test waiting for a pipeline run to complete."""
        # Set up mock responses for different states
        completed_status = {"status": "completed"}

        prax_result.client.get_run_status.return_value = completed_status

        # Mock time.time and time.sleep
        with patch("time.time", side_effect=[0, 0.5]), \
             patch("time.sleep") as mock_sleep:

            # Wait for completion
            final_status = prax_result.wait_for_completion(
                timeout=1, check_interval=1
            )

            # Check result
            assert final_status == completed_status

            # Check sleep calls
            assert mock_sleep.call_count == 0

    def test_wait_for_completion_timeout(self, prax_result):
        """Test timeout when waiting for a pipeline run to complete."""
        # Set up mock response for running state
        prax_result.client.get_run_status.return_value = {"status": "Running"}

        # Mock time.time to simulate timeout
        with patch("time.time", side_effect=[0, 3600, 7200]), \
             patch("time.sleep"):

            # Wait for completion with timeout
            with pytest.raises(TimeoutError, match="did not complete within"):
                prax_result.wait_for_completion(timeout=3000, check_interval=5)

    def test_download_outputs(self, prax_result):
        """Test downloading outputs from a pipeline run."""
        # Set up mock response
        prax_result.client.download_run_artifacts.return_value = [
            "/tmp/test-artifact1",
            "/tmp/test-artifact2"
        ]

        # Mock makedirs
        with patch("os.makedirs") as mock_makedirs:
            # Download outputs
            downloaded_files = prax_result.download_outputs(target_dir="/tmp/outputs")

            # Check result
            assert downloaded_files == ["/tmp/test-artifact1", "/tmp/test-artifact2"]

            # Check client call - now using the new signature
            prax_result.client.download_run_artifacts.assert_called_once_with(
                run_name="test-run-id",
                target_dir="/tmp/outputs"
            )

            # Check directory creation
            mock_makedirs.assert_called_once_with("/tmp/outputs", exist_ok=True)

    def test_download_outputs_no_client(self):
        """Test error handling when downloading outputs without a client."""
        result = PraxResult(
            run_id="test-run-id",
            run_name="test-run-id",
            pipeline_name="test-pipeline",
            org="test-org",
            project="test-project",
            stage="dev",
            status="submitted",
            client=None
        )

        with pytest.raises(ValueError, match="No client configured"):
            result.download_outputs(target_dir="/tmp/outputs")
