"""
Unit tests for PraxPipelineBackend.

This module tests the Prax pipeline backend implementation, including
pipeline execution, configuration handling, and error scenarios.
"""
import os
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, PropertyMock
import pytest
import yaml

from rompy_oceanum.pipeline import PraxPipelineBackend
from rompy_oceanum.client import PraxClient, PraxResult
from rompy_oceanum.config import PraxConfig, DataMeshConfig


class TestPraxPipelineBackend:
    """Test PraxPipelineBackend implementation."""

    def setup_method(self):
        """Set up test fixtures."""
        self.backend = PraxPipelineBackend()

        # Create mock model run
        self.mock_model_run = Mock()
        self.mock_model_run.run_id = "test-run-123"
        self.mock_model_run.model_type = "swan"
        self.mock_model_run.output_dir = "/tmp/outputs"

        # Create mock config
        self.mock_config = Mock()
        self.mock_config.model_type = "swan"
        self.mock_config.model_dump.return_value = {"model_type": "swan", "grid": {}}
        self.mock_model_run.config = self.mock_config

        # Create mock period
        self.mock_period = Mock()
        self.mock_period.start = "2023-01-01T00:00:00Z"
        self.mock_period.end = "2023-01-02T00:00:00Z"
        self.mock_model_run.period = self.mock_period

    def test_execute_basic_success(self):
        """Test basic successful pipeline execution."""
        # Setup
        prax_config = PraxConfig(
            base_url="https://prax.oceanum.io",
            token="test_token",
            org="test_org",
            project="test_project"
        )

        # Mock generate method
        staging_dir = Path("/tmp/staging")
        self.mock_model_run.generate.return_value = staging_dir
        self.mock_model_run.dump_inputs_dict.return_value = {"test": "config"}

        # Mock client and result
        mock_client = Mock(spec=PraxClient)
        mock_result = Mock(spec=PraxResult)
        mock_result.run_id = "prax-run-456"
        mock_client.submit_pipeline.return_value = mock_result

        with patch('rompy_oceanum.pipeline.PraxClient') as mock_client_class:
            mock_client_class.return_value = mock_client

            # Execute
            result = self.backend.execute(
                self.mock_model_run,
                pipeline_name="test-pipeline",
                prax_config=prax_config,
                deploy_pipeline=False
            )

            # Verify
            assert result["success"] is True
            assert result["backend"] == "prax"
            assert result["run_id"] == "test-run-123"
            assert result["pipeline_name"] == "test-pipeline"
            assert result["prax_run_id"] == "prax-run-456"
            assert "generate" in result["stages_completed"]
            assert "submit" in result["stages_completed"]

    def test_execute_with_deployment(self):
        """Test pipeline execution with deployment."""
        # Setup
        prax_config = PraxConfig(
            base_url="https://prax.oceanum.io",
            token="test_token",
            org="test_org",
            project="test_project"
        )

        # Create temporary template file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump({"kind": "Pipeline", "metadata": {"name": "test-pipeline"}}, f)
            template_path = f.name

        try:
            # Mock generate method
            staging_dir = Path("/tmp/staging")
            self.mock_model_run.generate.return_value = staging_dir
            self.mock_model_run.dump_inputs_dict.return_value = {"test": "config"}

            # Mock client
            mock_client = Mock(spec=PraxClient)
            mock_result = Mock(spec=PraxResult)
            mock_result.run_id = "prax-run-456"
            mock_client.submit_pipeline.return_value = mock_result

            with patch('rompy_oceanum.pipeline.PraxClient') as mock_client_class:
                mock_client_class.return_value = mock_client

                # Execute
                result = self.backend.execute(
                    self.mock_model_run,
                    pipeline_name="test-pipeline",
                    prax_config=prax_config,
                    template_path=template_path,
                    deploy_pipeline=True
                )

                # Verify
                assert result["success"] is True
                assert "deploy" in result["stages_completed"]

        finally:
            # Cleanup
            Path(template_path).unlink(missing_ok=True)

    def test_execute_with_wait_for_completion(self):
        """Test pipeline execution with wait for completion."""
        # Setup
        prax_config = PraxConfig(
            base_url="https://prax.oceanum.io",
            token="test_token",
            org="test_org",
            project="test_project"
        )

        # Mock generate method
        staging_dir = Path("/tmp/staging")
        self.mock_model_run.generate.return_value = staging_dir
        self.mock_model_run.dump_inputs_dict.return_value = {"test": "config"}

        # Mock client and result
        mock_client = Mock(spec=PraxClient)
        mock_result = Mock(spec=PraxResult)
        mock_result.run_id = "prax-run-456"
        mock_client.submit_pipeline.return_value = mock_result
        mock_result.run_id = "prax-run-456"
        mock_client.submit_pipeline.return_value = mock_result
        mock_result.wait_for_completion.return_value = {"status": "completed"}

        with patch('rompy_oceanum.pipeline.PraxClient') as mock_client_class:
            mock_client_class.return_value = mock_client

            # Execute
            result = self.backend.execute(
                self.mock_model_run,
                pipeline_name="test-pipeline",
                prax_config=prax_config,
                deploy_pipeline=False,
                wait_for_completion=True,
                timeout=1800
            )

            # Verify
            assert result["success"] is True
            assert "wait" in result["stages_completed"]
            assert result["final_status"]["status"] == "completed"
            mock_result.wait_for_completion.assert_called_once_with(timeout=1800)

    def test_execute_with_download_outputs(self):
        """Test pipeline execution with output download."""
        # Setup
        prax_config = PraxConfig(
            base_url="https://prax.oceanum.io",
            token="test_token",
            org="test_org",
            project="test_project"
        )

        # Mock generate method
        staging_dir = Path("/tmp/staging")
        self.mock_model_run.generate.return_value = staging_dir
        self.mock_model_run.dump_inputs_dict.return_value = {"test": "config"}

        # Mock client and result
        mock_client = Mock(spec=PraxClient)
        mock_result = Mock(spec=PraxResult)
        mock_result.run_id = "prax-run-456"
        mock_client.submit_pipeline.return_value = mock_result

        downloaded_files = [Path("/tmp/output1.nc"), Path("/tmp/output2.csv")]
        mock_result.download_outputs.return_value = downloaded_files

        with patch('rompy_oceanum.pipeline.PraxClient') as mock_client_class:
            mock_client_class.return_value = mock_client

            # Execute
            result = self.backend.execute(
                self.mock_model_run,
                pipeline_name="test-pipeline",
                prax_config=prax_config,
                deploy_pipeline=False,
                download_outputs=True,
                output_dir="/tmp/custom_outputs"
            )

            # Verify
            assert result["success"] is True
            assert "download" in result["stages_completed"]
            assert result["downloaded_files"] == ["/tmp/output1.nc", "/tmp/output2.csv"]
            mock_result.download_outputs.assert_called_once_with("/tmp/custom_outputs")

    def test_execute_with_datamesh_config(self):
        """Test pipeline execution with DataMesh configuration."""
        # Setup
        prax_config = PraxConfig(
            base_url="https://prax.oceanum.io",
            token="test_token",
            org="test_org",
            project="test_project"
        )

        datamesh_config = DataMeshConfig(
            base_url="https://datamesh.oceanum.io",
            token="dm_token"
        )

        # Mock generate method
        staging_dir = Path("/tmp/staging")
        self.mock_model_run.generate.return_value = staging_dir
        self.mock_model_run.dump_inputs_dict.return_value = {"test": "config"}
        self.mock_model_run.dump_inputs_dict.return_value = {"test": "config"}

        # Mock client and result
        mock_client = Mock(spec=PraxClient)
        mock_result = Mock(spec=PraxResult)
        mock_result.run_id = "prax-run-456"
        mock_client.submit_pipeline.return_value = mock_result

        with patch('rompy_oceanum.pipeline.PraxClient') as mock_client_class:
            mock_client_class.return_value = mock_client

            # Execute
            result = self.backend.execute(
                self.mock_model_run,
                pipeline_name="test-pipeline",
                prax_config=prax_config,
                datamesh_config=datamesh_config,
                deploy_pipeline=False
            )

            # Verify
            assert result["success"] is True
            assert "datamesh" in result["stages_completed"]
            assert result["datamesh_result"]["status"] == "not_implemented"

    def test_execute_invalid_model_run(self):
        """Test execute with invalid model run."""
        # Test with None model_run
        with pytest.raises(ValueError, match="model_run cannot be None"):
            self.backend.execute(None, pipeline_name="test-pipeline")

        # Test with model_run without run_id
        mock_model_run = Mock()
        del mock_model_run.run_id

        with pytest.raises(ValueError, match="model_run must have a run_id attribute"):
            self.backend.execute(mock_model_run, pipeline_name="test-pipeline")

    def test_execute_invalid_pipeline_name(self):
        """Test execute with invalid pipeline name."""
        invalid_names = ["", "   ", None]

        for name in invalid_names:
            with pytest.raises(ValueError, match="pipeline_name cannot be empty"):
                self.backend.execute(self.mock_model_run, pipeline_name=name)

    def test_execute_config_from_env(self):
        """Test execute with configuration from environment."""
        env_vars = {
            "PRAX_BASE_URL": "https://prax.oceanum.io",
            "PRAX_TOKEN": "env_token",
            "PRAX_ORG": "env_org",
            "PRAX_PROJECT": "env_project"
        }

        with patch.dict('os.environ', env_vars):
            # Mock generate method
            staging_dir = Path("/tmp/staging")
            self.mock_model_run.generate.return_value = staging_dir
            self.mock_model_run.dump_inputs_dict.return_value = {"test": "config"}

            # Mock client
            mock_client = Mock(spec=PraxClient)
            mock_result = Mock(spec=PraxResult)
            mock_result.run_id = "prax-run-456"
            mock_client.submit_pipeline.return_value = mock_result

            with patch('rompy_oceanum.pipeline.PraxClient') as mock_client_class:
                mock_client_class.return_value = mock_client

                # Execute
                result = self.backend.execute(
                    self.mock_model_run,
                    pipeline_name="test-pipeline",
                    deploy_pipeline=False
                )

                # Verify
                assert result["success"] is True
                # Verify client was created with environment config
                created_config = mock_client_class.call_args[0][0]
                assert created_config.token == "env_token"
                assert created_config.org == "env_org"

    def test_execute_generate_failure(self):
        """Test execute with generate failure."""
        # Setup
        prax_config = PraxConfig(
            base_url="https://prax.oceanum.io",
            token="test_token",
            org="test_org",
            project="test_project"
        )

        # Mock dump_inputs_dict
        self.mock_model_run.dump_inputs_dict.return_value = {"test": "config"}
        
        # Mock staging_dir property to fail
        type(self.mock_model_run).staging_dir = PropertyMock(side_effect=Exception("Generate failed"))

        # Execute
        result = self.backend.execute(
            self.mock_model_run,
            pipeline_name="test-pipeline",
            prax_config=prax_config,
            deploy_pipeline=False
        )

        # Verify
        assert result["success"] is False
        assert result["stage"] == "generate"
        assert "Generate failed" in result["error"]

    def test_execute_submit_failure(self):
        """Test execute with submit failure."""
        # Setup
        prax_config = PraxConfig(
            base_url="https://prax.oceanum.io",
            token="test_token",
            org="test_org",
            project="test_project"
        )

        # Mock generate method
        staging_dir = Path("/tmp/staging")
        self.mock_model_run.generate.return_value = staging_dir
        self.mock_model_run.dump_inputs_dict.return_value = {"test": "config"}

        # Mock client to fail submit
        mock_client = Mock(spec=PraxClient)
        mock_client.submit_pipeline.side_effect = Exception("Submit failed")

        with patch('rompy_oceanum.pipeline.PraxClient') as mock_client_class:
            mock_client_class.return_value = mock_client

            # Execute
            result = self.backend.execute(
                self.mock_model_run,
                pipeline_name="test-pipeline",
                prax_config=prax_config,
                deploy_pipeline=False
            )

            # Verify
            assert result["success"] is False
            assert result["stage"] == "submit"
            assert "Submit failed" in result["error"]

    def test_execute_wait_timeout(self):
        """Test execute with wait timeout."""
        # Setup
        prax_config = PraxConfig(
            base_url="https://prax.oceanum.io",
            token="test_token",
            org="test_org",
            project="test_project"
        )

        # Mock generate method
        staging_dir = Path("/tmp/staging")
        self.mock_model_run.generate.return_value = staging_dir
        self.mock_model_run.dump_inputs_dict.return_value = {"test": "config"}

        # Mock client and result
        mock_client = Mock(spec=PraxClient)
        mock_result = Mock(spec=PraxResult)
        mock_result.run_id = "prax-run-456"
        mock_client.submit_pipeline.return_value = mock_result
        mock_result.wait_for_completion.return_value = {"status": "timeout"}

        with patch('rompy_oceanum.pipeline.PraxClient') as mock_client_class:
            mock_client_class.return_value = mock_client

            # Execute
            result = self.backend.execute(
                self.mock_model_run,
                pipeline_name="test-pipeline",
                prax_config=prax_config,
                deploy_pipeline=False,
                wait_for_completion=True
            )

            # Verify
            assert result["success"] is False
            assert result["stage"] == "wait"
            assert "timeout" in result["message"]

    def test_convert_model_to_prax_parameters(self):
        """Test _convert_model_to_prax_parameters method."""
        staging_dir = Path("/tmp/staging")
        additional_params = {"datamesh_token": "test-token"}
        
        # Mock dump_inputs_dict to return expected keys
        self.mock_model_run.dump_inputs_dict.return_value = {
            "run_id": "test-run-123",
            "model_type": "swan",
            "start_time": "2023-01-01T00:00:00Z",
            "end_time": "2023-01-02T00:00:00Z"
        }

        # Execute
        params = self.backend._convert_model_to_prax_parameters(
            self.mock_model_run, staging_dir, additional_params
        )

        # Verify
        assert "rompy-config" in params
        # Parse the JSON to check the contents
        import json
        rompy_config = json.loads(params["rompy-config"])
        assert rompy_config["run_id"] == "test-run-123"
        assert rompy_config["model_type"] == "swan"
        assert rompy_config["start_time"] == "2023-01-01T00:00:00Z"
        assert rompy_config["end_time"] == "2023-01-02T00:00:00Z"
        assert rompy_config["output_dir"] == "/tmp/rompy"
        assert rompy_config["run_id_subdir"] is False
        
        # Check that datamesh token is added to top-level parameters
        assert params["datamesh-token"] == "test-token"

    def test_get_default_template_path(self):
        """Test get_default_template_path method."""
        # Create mock template file
        template_dir = Path(self.backend.__class__.__module__).parent / "pipeline_templates"

        with patch('pathlib.Path.exists') as mock_exists:
            mock_exists.return_value = True

            # Test direct match
            result = self.backend.get_default_template_path("swan")
            assert result is not None
            assert "swan.yaml" in result

            # Test no match
            mock_exists.return_value = False
            result = self.backend.get_default_template_path("nonexistent")
            assert result is None

    def test_register_with_datamesh_placeholder(self):
        """Test _register_with_datamesh placeholder implementation."""
        datamesh_config = DataMeshConfig(
            base_url="https://datamesh.oceanum.io",
            token="dm_token"
        )

        mock_result = Mock(spec=PraxResult)

        # Execute
        result = self.backend._register_with_datamesh(
            self.mock_model_run, mock_result, datamesh_config, "/tmp/outputs"
        )

        # Verify
        assert result["status"] == "not_implemented"
        assert "not yet implemented" in result["message"]
