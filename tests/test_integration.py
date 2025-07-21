"""
Integration tests for rompy-oceanum plugin-based backend architecture.
"""

import os
import sys
import pytest
from unittest.mock import MagicMock, patch

import rompy_oceanum


@pytest.mark.integration
class TestPluginIntegration:
    """Integration tests for rompy-oceanum plugin-based architecture."""

    @pytest.fixture
    def mock_prax_environment(self):
        """Set up a mock Prax environment for integration testing."""
        with patch.dict(os.environ, {
            "PRAX_TOKEN": "integration-test-token",
            "PRAX_BASE_URL": "https://prax.oceanum.io",
            "PRAX_ORG": "integration-test-org",
            "PRAX_PROJECT": "integration-test-project",
            "DATAMESH_TOKEN": "integration-test-datamesh-token"
        }):
            yield

    @pytest.fixture
    def sample_model_config(self):
        """Sample model configuration for testing."""
        return {
            "model_type": "swan",
            "run_id": "integration-test-run",
            "output_dir": "./outputs",
            "time": {
                "start": "2023-01-01T00:00:00",
                "end": "2023-01-02T00:00:00",
                "interval": "1H"
            },
            "config": {
                "grid": {"x": [0, 1000], "y": [0, 1000], "dx": 1000, "dy": 1000},
                "physics": {"generation": True, "breaking": True},
                "outputs": [
                    {"type": "grid", "parameters": ["hsig"], "filename": "grid.nc"},
                    {"type": "spectra", "parameters": ["energy"], "filename": "spec.nc"}
                ]
            }
        }

    def test_pipeline_backend_registration(self):
        """Test that the Prax pipeline backend is properly registered."""
        from rompy_oceanum.pipeline import PraxPipelineBackend

        # Check that the backend class exists and is importable
        assert PraxPipelineBackend is not None

        # Check that it has the required methods
        assert hasattr(PraxPipelineBackend, 'submit')
        assert hasattr(PraxPipelineBackend, 'get_status')
        assert hasattr(PraxPipelineBackend, 'get_logs')
        assert hasattr(PraxPipelineBackend, 'download_outputs')

    def test_postprocessor_registration(self):
        """Test that the DataMesh postprocessor is properly registered."""
        from rompy_oceanum.postprocess import DataMeshPostprocessor

        # Check that the postprocessor class exists and is importable
        assert DataMeshPostprocessor is not None

        # Check that it has the required methods
        assert hasattr(DataMeshPostprocessor, 'process')

    @patch('rompy_oceanum.client.PraxClient')
    def test_prax_backend_submission(self, mock_prax_client_class, mock_prax_environment, sample_model_config):
        """Test submitting a model run using the Prax pipeline backend."""
        from rompy_oceanum.pipeline import PraxPipelineBackend
        from rompy_oceanum.config import PraxConfig

        # Set up mock client
        mock_client = MagicMock()
        mock_prax_client_class.return_value = mock_client

        # Set up mock result
        mock_result = MagicMock()
        mock_result.run_id = "test-run-id"
        mock_result.pipeline_name = "test-pipeline"
        mock_result.status = "submitted"
        mock_client.submit_pipeline.return_value = mock_result

        # Create backend configuration
        prax_config = PraxConfig(
            pipeline_name="integration-test-pipeline",
            org="integration-test-org",
            project="integration-test-project",
            stage="dev"
        )

        # Create and use the backend
        backend = PraxPipelineBackend(config=prax_config)

        # Submit the model run
        result = backend.submit(
            model_config=sample_model_config,
            pipeline_name="integration-test-pipeline"
        )

        # Verify the result
        assert result is not None
        assert result.run_id == "test-run-id"
        assert result.pipeline_name == "test-pipeline"

        # Verify client was called correctly
        mock_client.submit_pipeline.assert_called_once()
        call_args = mock_client.submit_pipeline.call_args
        assert call_args.kwargs["pipeline_name"] == "integration-test-pipeline"
        assert call_args.kwargs["org"] == "integration-test-org"
        assert call_args.kwargs["project"] == "integration-test-project"
        assert call_args.kwargs["stage"] == "dev"

    @patch('rompy_oceanum.client.PraxClient')
    def test_backend_status_monitoring(self, mock_prax_client_class, mock_prax_environment):
        """Test monitoring pipeline status through the backend."""
        from rompy_oceanum.pipeline import PraxPipelineBackend
        from rompy_oceanum.config import PraxConfig
        from rompy_oceanum.client import PraxResult

        # Set up mock client
        mock_client = MagicMock()
        mock_prax_client_class.return_value = mock_client

        # Create backend configuration
        prax_config = PraxConfig(
            pipeline_name="test-pipeline",
            org="test-org",
            project="test-project",
            stage="dev"
        )

        # Create backend
        backend = PraxPipelineBackend(config=prax_config)

        # Create a result object
        result = PraxResult(
            run_id="test-run-id",
            pipeline_name="test-pipeline",
            user="test-user",
            org="test-org",
            project="test-project",
            stage="dev",
            status="running",
            client=mock_client
        )

        # Mock status response
        mock_client.get_run_status.return_value = {
            "run_id": "test-run-id",
            "status": "Running",
            "created_at": "2023-01-01T00:00:00Z"
        }

        # Get status through backend
        status = backend.get_status(result)

        # Verify status response
        assert status["run_id"] == "test-run-id"
        assert status["status"] == "Running"

        # Verify client was called
        mock_client.get_run_status.assert_called_once_with(
            run_id="test-run-id",
            pipeline_name="test-pipeline",
            user="test-user",
            org="test-org",
            project="test-project",
            stage="dev"
        )

    @patch('rompy_oceanum.client.PraxClient')
    def test_backend_log_retrieval(self, mock_prax_client_class, mock_prax_environment):
        """Test retrieving logs through the backend."""
        from rompy_oceanum.pipeline import PraxPipelineBackend
        from rompy_oceanum.config import PraxConfig
        from rompy_oceanum.client import PraxResult

        # Set up mock client
        mock_client = MagicMock()
        mock_prax_client_class.return_value = mock_client

        # Create backend configuration
        prax_config = PraxConfig(
            pipeline_name="test-pipeline",
            org="test-org",
            project="test-project",
            stage="dev"
        )

        # Create backend
        backend = PraxPipelineBackend(config=prax_config)

        # Create a result object
        result = PraxResult(
            run_id="test-run-id",
            pipeline_name="test-pipeline",
            user="test-user",
            org="test-org",
            project="test-project",
            stage="dev",
            status="running",
            client=mock_client
        )

        # Mock logs response
        mock_client.get_run_logs.return_value = {
            "logs": "Test integration logs\nStep 1: Starting\nStep 2: Running\nStep 3: Complete"
        }

        # Get logs through backend
        logs = backend.get_logs(result)

        # Verify logs response
        assert "Test integration logs" in logs["logs"]
        assert "Step 1: Starting" in logs["logs"]

        # Verify client was called
        mock_client.get_run_logs.assert_called_once()

    @patch('rompy_oceanum.client.PraxClient')
    @patch('os.makedirs')
    def test_backend_output_download(self, mock_makedirs, mock_prax_client_class, mock_prax_environment):
        """Test downloading outputs through the backend."""
        from rompy_oceanum.pipeline import PraxPipelineBackend
        from rompy_oceanum.config import PraxConfig
        from rompy_oceanum.client import PraxResult

        # Set up mock client
        mock_client = MagicMock()
        mock_prax_client_class.return_value = mock_client

        # Create backend configuration
        prax_config = PraxConfig(
            pipeline_name="test-pipeline",
            org="test-org",
            project="test-project",
            stage="dev"
        )

        # Create backend
        backend = PraxPipelineBackend(config=prax_config)

        # Create a result object
        result = PraxResult(
            run_id="test-run-id",
            pipeline_name="test-pipeline",
            user="test-user",
            org="test-org",
            project="test-project",
            stage="dev",
            status="succeeded",
            client=mock_client
        )

        # Mock download response
        mock_client.download_run_artifacts.return_value = [
            "/tmp/integration-test/grid.nc",
            "/tmp/integration-test/spec.nc"
        ]

        # Download outputs through backend
        downloaded_files = backend.download_outputs(result, target_dir="/tmp/integration-test")

        # Verify download response
        assert len(downloaded_files) == 2
        assert "/tmp/integration-test/grid.nc" in downloaded_files
        assert "/tmp/integration-test/spec.nc" in downloaded_files

        # Verify client was called
        mock_client.download_run_artifacts.assert_called_once_with(
            run_id="test-run-id",
            pipeline_name="test-pipeline",
            user="test-user",
            org="test-org",
            project="test-project",
            stage="dev",
            target_dir="/tmp/integration-test"
        )

        # Verify directory creation
        mock_makedirs.assert_called_once_with("/tmp/integration-test", exist_ok=True)

    def test_datamesh_postprocessor(self, mock_prax_environment):
        """Test DataMesh postprocessor functionality."""
        from rompy_oceanum.postprocess import DataMeshPostprocessor
        from rompy_oceanum.config import DataMeshConfig

        # Create postprocessor configuration
        datamesh_config = DataMeshConfig(
            output_patterns=["*.nc"],
            tags=["integration-test", "swan", "wave-model"]
        )

        # Create postprocessor
        postprocessor = DataMeshPostprocessor(config=datamesh_config)

        # Mock output files
        with patch("glob.glob", return_value=["/tmp/outputs/grid.nc", "/tmp/outputs/spec.nc"]), \
             patch("rompy_oceanum.postprocess.register_dataset") as mock_register:

            # Mock successful registration
            mock_register.return_value = {"dataset_id": "test-dataset-123"}

            # Process outputs
            result = postprocessor.process(
                output_dir="/tmp/outputs",
                run_id="integration-test-run"
            )

            # Verify processing result
            assert result is not None
            assert "registered_datasets" in result
            assert len(result["registered_datasets"]) == 2

            # Verify registration calls
            assert mock_register.call_count == 2

    def test_cli_integration(self, mock_prax_environment, sample_model_config, tmp_path):
        """Test CLI integration with plugin backend."""
        from rompy_oceanum.cli import main
        import tempfile
        import json

        # Create temporary config file
        config_file = tmp_path / "test_config.json"
        with open(config_file, 'w') as f:
            json.dump(sample_model_config, f)

        # Mock CLI arguments
        test_args = [
            "run", "swan",
            str(config_file),
            "--pipeline-backend", "prax",
            "--pipeline-name", "integration-test-cli",
            "--org", "test-org",
            "--project", "test-project"
        ]

        with patch("sys.argv", ["rompy-oceanum"] + test_args), \
             patch("rompy_oceanum.pipeline.PraxPipelineBackend") as mock_backend_class:

            # Set up mock backend
            mock_backend = MagicMock()
            mock_backend_class.return_value = mock_backend

            # Set up mock result
            mock_result = MagicMock()
            mock_result.run_id = "cli-test-run-id"
            mock_backend.submit.return_value = mock_result

            try:
                # Run CLI (this should not raise an exception)
                main()

                # Verify backend was created and used
                mock_backend_class.assert_called_once()
                mock_backend.submit.assert_called_once()

            except SystemExit:
                # CLI may exit normally, that's ok
                pass
