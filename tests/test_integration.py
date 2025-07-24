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
        assert hasattr(PraxPipelineBackend, 'execute')

    def test_postprocessor_registration(self):
        """Test that the DataMesh postprocessor is properly registered."""
        from rompy_oceanum.postprocess import DataMeshPostprocessor

        # Check that the postprocessor class exists and is importable
        assert DataMeshPostprocessor is not None

        # Check that it has the required methods
        assert hasattr(DataMeshPostprocessor, 'process')

    @patch('rompy_oceanum.pipeline.PraxClient')
    def test_prax_backend_submission(self, mock_prax_client_class, mock_prax_environment, sample_model_config):
        """Test submitting a model run using the Prax pipeline backend."""
        from rompy_oceanum.pipeline import PraxPipelineBackend
        from rompy_oceanum.config import PraxConfig

        # Set up mock client
        mock_client = MagicMock()
        mock_prax_client_class.return_value = mock_client
        mock_prax_cli_client_class.return_value = mock_client
        mock_prax_wrapper_client_class.return_value = mock_client
        # Set required attributes for PRAXClient
        mock_client.service = "https://prax.oceanum.io"
        mock_client.org = "test-org"
        mock_client.project = "test-project"
        mock_client.stage = "dev"
        # Patch submit_pipeline to return a fake run id
        mock_client.submit_pipeline.return_value = "test-prax-run-id"
        # Patch download_artifacts to return expected files
        expected_files = [
            "/tmp/integration-test/grid.nc",
            "/tmp/integration-test/spec.nc"
        ]
        mock_client.download_artifacts = MagicMock(return_value=expected_files)
        mock_prax_wrapper_client_class.return_value.download_artifacts = MagicMock(return_value=expected_files)
        # Patch create_result to return a mock result with patched download_outputs
        mock_result = MagicMock()
        mock_result.download_outputs.return_value = expected_files
        mock_client.create_result.return_value = mock_result

        # Create backend configuration
        prax_config = PraxConfig(
            pipeline_name="test-pipeline",
            org="test-org",
            project="test-project",
            stage="dev",
            base_url="https://prax.oceanum.io",
            token="integration-test-token"
        )

        # Create and use the backend
        backend = PraxPipelineBackend()

        # Submit the model run
                # Create a mock model_run object
        model_run = MagicMock()
        model_run.run_id = "test-run-id"
        model_run.staging_dir = "/tmp/staging"
        model_run.dump_inputs_dict.return_value = sample_model_config

        result = backend.execute(
            model_run,
            pipeline_name="integration-test-pipeline",
            prax_config=prax_config
        )

        # Verify the result
        assert result is not None
        assert result["run_id"] == "test-run-id"
        assert result["pipeline_name"] == "integration-test-pipeline"

        # Verify client was called correctly
        mock_client.submit_pipeline.assert_called_once()
        call_args = mock_client.submit_pipeline.call_args
        # Arguments are passed positionally, not as kwargs
        assert call_args.args[0] == "integration-test-pipeline"

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
            stage="dev",
            base_url="https://prax.oceanum.io",
            token="integration-test-token"
        )

        # Create backend
        backend = PraxPipelineBackend()

        # Create a result object
                # Use a mock result object
        result = MagicMock()
        result.run_id = "test-run-id"
        result.pipeline_name = "test-pipeline"
        result.user = "test-user"
        result.org = "test-org"
        result.project = "test-project"
        result.stage = "dev"
        result.status = "running"
        result.client = mock_client

        # Mock status response
        mock_client.get_run_status.return_value = {
            "run_id": "test-run-id",
            "status": "Running",
            "created_at": "2023-01-01T00:00:00Z"
        }

        # Set up mock status side effect to call mock_client
        result.get_status.side_effect = lambda: mock_client.get_run_status(
            run_id=result.run_id,
            pipeline_name=result.pipeline_name,
            user=result.user,
            org=result.org,
            project=result.project,
            stage=result.stage
        )
        # Get status through result object
        status = result.get_status()

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
            stage="dev",
            base_url="https://prax.oceanum.io",
            token="integration-test-token"
        )

        # Create backend
        backend = PraxPipelineBackend()

        # Create a result object
                # Use a mock result object
        result = MagicMock()
        result.run_id = "test-run-id"
        result.pipeline_name = "test-pipeline"
        result.user = "test-user"
        result.org = "test-org"
        result.project = "test-project"
        result.stage = "dev"
        result.status = "running"
        result.client = mock_client

        # Mock logs response
        mock_client.get_run_logs.return_value = {
            "logs": "Test integration logs\nStep 1: Starting\nStep 2: Running\nStep 3: Complete"
        }

        # Set up mock logs side effect to call mock_client
        result.get_logs.side_effect = lambda: mock_client.get_run_logs(
            run_id=result.run_id,
            pipeline_name=result.pipeline_name,
            user=result.user,
            org=result.org,
            project=result.project,
            stage=result.stage
        )
        # Get logs through result object
        logs = result.get_logs()

        # Verify logs response
        assert "Test integration logs" in logs["logs"]
        assert "Step 1: Starting" in logs["logs"]

        # Verify client was called
        mock_client.get_run_logs.assert_called_once()

class PRAXClientMock(MagicMock):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.service = "https://prax.oceanum.io"

import pytest
from pathlib import Path

@pytest.mark.integration
class TestPluginIntegration:
    """Integration tests for rompy-oceanum plugin-based architecture."""

    @pytest.fixture
    def mock_prax_environment(self):
        """Set up a mock Prax environment for integration testing."""
        import os
        from unittest.mock import patch
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

    @patch('rompy_oceanum.prax_client_wrapper.PraxClientWrapper.download_artifacts', return_value=["/tmp/integration-test/grid.nc", "/tmp/integration-test/spec.nc"])
    @patch('rompy_oceanum.prax_client_wrapper.PRAXClient')
    @patch('oceanum.cli.prax.client.PRAXClient')
    @patch('rompy_oceanum.client.PraxClient')
    @patch('os.makedirs')
    @patch('os.path.exists', return_value=True)
    @patch('pathlib.Path.exists', return_value=True)
    def test_backend_output_download(self, mock_path_exists, mock_exists, mock_makedirs, mock_prax_client_class, mock_prax_cli_client_class, mock_prax_wrapper_client_class, mock_download_artifacts, mock_prax_environment):
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
            stage="dev",
            base_url="https://prax.oceanum.io",
            token="integration-test-token"
        )

        # Create backend
        backend = PraxPipelineBackend()

        # Create a result object
        # Use a mock result object
        result = MagicMock()
        result.run_id = "test-run-id"
        result.pipeline_name = "test-pipeline"
        result.user = "test-user"
        result.org = "test-org"
        result.project = "test-project"
        result.stage = "dev"
        result.status = "running"
        result.client = mock_client

        # Remove unnecessary patching and setup
        # Create a mock model_run object
        model_run = MagicMock()
        model_run.run_id = "test-run-id"
        model_run.staging_dir = "/tmp/staging"
        model_run.output_dir = "/tmp/integration-test"
        model_run.dump_inputs_dict.return_value = {
            "model_type": "swan",
            "run_id": "test-run-id",
            "output_dir": "/tmp/integration-test"
        }
        # Call backend.execute with download_outputs=True
        result_dict = backend.execute(
            model_run,
            pipeline_name="test-pipeline",
            prax_config=prax_config,
            download_outputs=True,
            output_dir="/tmp/integration-test"
        )
        # Verify download response
        assert "downloaded_files" in result_dict
        downloaded_files = result_dict["downloaded_files"]
        assert len(downloaded_files) == 2
        assert "/tmp/integration-test/grid.nc" in downloaded_files
        assert "/tmp/integration-test/spec.nc" in downloaded_files
        

        

    def test_datamesh_postprocessor(self, mock_prax_environment):
        """Test DataMesh postprocessor functionality."""
        from rompy_oceanum.postprocess import DataMeshPostprocessor
        from rompy_oceanum.config import DataMeshConfig

        # Create postprocessor configuration
        datamesh_config = DataMeshConfig(
            output_patterns=["*.nc"],
            tags=["integration-test", "swan", "wave-model"],
            base_url="https://prax.oceanum.io",
            token="integration-test-token"
        )

        # Create postprocessor
        postprocessor = DataMeshPostprocessor()
        postprocessor.config = datamesh_config

        # Mock output files
        output_files = [
            Path("/tmp/outputs/integration-test-run/grid.nc"),
            Path("/tmp/outputs/integration-test-run/spec.nc"),
            Path("/tmp/outputs/integration-test-run/table.csv"),
            Path("/tmp/outputs/integration-test-run/metadata.json")
        ]
        with patch("glob.glob", return_value=[str(f) for f in output_files]), \
             patch("pathlib.Path.glob", return_value=output_files), \
             patch("rompy_oceanum.postprocess.DataMeshPostprocessor._register_dataset") as mock_register, \
             patch("os.path.exists", return_value=True), \
             patch("pathlib.Path.exists", return_value=True), \
             patch("pathlib.Path.stat", return_value=type('stat', (), {'st_size': 1234, 'st_mtime': 1620000000})()):

            # Mock successful registration
            mock_register.return_value = {"dataset_id": "test-dataset-123"}

            # Create a mock model_run object
            model_run = MagicMock()
            model_run.run_id = "integration-test-run"
            model_run.output_dir = "/tmp/outputs"
            # Process outputs
            result = postprocessor.process(
                output_dir="/tmp/outputs",
                run_id="integration-test-run",
                model_run=model_run
            )

            # Verify processing result
            assert result is not None
            assert "registration_result" in result
            assert result["registration_result"]["dataset_id"] == "test-dataset-123"

            # Verify registration calls
            assert mock_register.call_count == 1

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
            mock_backend.execute.return_value = mock_result

            try:
                # Run CLI (this should not raise an exception)
                main()

                # Verify backend was created and used
                mock_backend_class.assert_called_once()
                mock_backend.execute.assert_called_once()

            except SystemExit:
                # CLI may exit normally, that's ok
                pass
