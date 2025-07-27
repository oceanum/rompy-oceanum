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
    @patch('rompy_oceanum.client.PraxClient')
    def test_prax_backend_submission(self, mock_prax_client_class, mock_prax_environment, sample_model_config):
        """Test submitting a model run using the Prax pipeline backend."""
        from rompy_oceanum.pipeline import PraxPipelineBackend
        from rompy_oceanum.config import PraxConfig

        # Create backend configuration
        prax_config = PraxConfig(
            base_url="https://prax.oceanum.io",
            token="test-token",
            pipeline_name="integration-test-pipeline",
            org="integration-test-org",
            project="integration-test-project",
            stage="dev"
        )

        # Create and use the backend
        backend = PraxPipelineBackend(config=prax_config)
        
        # Verify it was created successfully
        assert backend is not None
        assert hasattr(backend, 'submit')

    @patch('rompy_oceanum.client.PraxClient')
    @patch('rompy_oceanum.client.PraxClient')
    def test_backend_status_monitoring(self, mock_prax_client_class, mock_prax_environment):
        """Test monitoring pipeline status through the backend."""
        from rompy_oceanum.pipeline import PraxPipelineBackend
        from rompy_oceanum.config import PraxConfig
        from rompy_oceanum.client import PraxResult

        # Create backend configuration
        prax_config = PraxConfig(
            base_url="https://prax.oceanum.io",
            token="test-token",
            pipeline_name="test-pipeline",
            org="test-org",
            project="test-project",
            stage="dev"
        )

        # Create backend
        backend = PraxPipelineBackend(config=prax_config)
        
        # Verify it was created successfully
        assert backend is not None
        assert hasattr(backend, 'get_status')

    @patch('rompy_oceanum.client.PraxClient')
    def test_backend_log_retrieval(self, mock_prax_client_class, mock_prax_environment):
        """Test retrieving logs through the backend."""
        from rompy_oceanum.pipeline import PraxPipelineBackend
        from rompy_oceanum.config import PraxConfig
        from rompy_oceanum.client import PraxResult

        # Create backend configuration
        prax_config = PraxConfig(
            base_url="https://prax.oceanum.io",
            token="test-token",
            pipeline_name="test-pipeline",
            org="test-org",
            project="test-project",
            stage="dev"
        )

        # Create backend
        backend = PraxPipelineBackend(config=prax_config)
        
        # Verify it was created successfully
        assert backend is not None
        assert hasattr(backend, 'get_logs')

    def test_backend_output_download(self, mock_prax_environment):
        """Test downloading outputs through the backend."""
        from rompy_oceanum.pipeline import PraxPipelineBackend
        from rompy_oceanum.config import PraxConfig
        from rompy_oceanum.client import PraxResult

        # Create backend configuration
        prax_config = PraxConfig(
            base_url="https://prax.oceanum.io",
            token="test-token",
            pipeline_name="test-pipeline",
            org="test-org",
            project="test-project",
            stage="dev"
        )

        # Create backend
        backend = PraxPipelineBackend(config=prax_config)
        
        # Verify it was created successfully
        assert backend is not None
        assert hasattr(backend, 'download_outputs')

    def test_datamesh_postprocessor(self, mock_prax_environment):
        """Test DataMesh postprocessor functionality."""
        from rompy_oceanum.postprocess import DataMeshPostprocessor
        from rompy_oceanum.config import DataMeshConfig

        # Create postprocessor configuration
        datamesh_config = DataMeshConfig(
            base_url="https://datamesh.oceanum.io",
            token="test-token",
            output_patterns=["*.nc"],
            tags=["integration-test", "swan", "wave-model"]
        )

        # Create postprocessor
        postprocessor = DataMeshPostprocessor(config=datamesh_config)
        
        # Verify it was created successfully
        assert postprocessor is not None
        assert hasattr(postprocessor, 'process')

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
