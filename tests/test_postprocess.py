import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import tempfile
import os

from rompy_oceanum.postprocess import DataMeshPostprocessor
from rompy_oceanum.config import DataMeshConfig


class TestDatameshPostprocessor:
    """Test the DataMeshPostprocessor class."""

    def test_init(self):
        """Test initialization of DataMeshPostprocessor."""
        # Test with no config
        processor = DataMeshPostprocessor()
        assert processor.config is None

        # Test with config dict
        config_dict = {
            "base_url": "https://datamesh.example.com",
            "token": "test-token"
        }
        processor = DataMeshPostprocessor(config_dict)
        # The config is not converted to DataMeshConfig in __init__, only when used in process()
        assert processor.config == config_dict

    @patch('rompy_oceanum.postprocess.DataMeshConfig.from_env')
    def test_process_with_env_config(self, mock_from_env):
        """Test process method with environment config."""
        # Setup mock
        mock_config = Mock()
        mock_config.base_url = "https://datamesh.example.com"
        mock_config.token = "test-token"
        mock_from_env.return_value = mock_config

        # Create processor and mock model_run
        processor = DataMeshPostprocessor()
        model_run = Mock()
        model_run.run_id = "test-run-123"
        model_run.output_dir = "/tmp/rompy"
        
        config_dict = Mock()
        config_dict.dict.return_value = {"run_id_subdir": False}
        model_run.config = config_dict

        # Create temporary directory structure
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir) / "test-run-123"
            output_dir.mkdir()
            
            # Create mock output files
            grid_file = output_dir / "swangrid.nc"
            grid_file.touch()
            
            spectra_file = output_dir / "swanspec.nc"
            spectra_file.touch()
            
            model_run.output_dir = str(temp_dir)
            
            # Mock DatameshWriter methods
            with patch('rompy_oceanum.postprocess.DatameshWriter') as mock_writer_class:
                mock_writer = Mock()
                mock_writer_class.return_value = mock_writer
                
                # Run process method
                result = processor.process(model_run)
                
                # Assertions
                assert result["success"] is True
                assert result["run_id"] == "test-run-123"
                assert "register_grid" in result["stages_completed"]
                assert "register_spectra" in result["stages_completed"]
                
                # Verify DatameshWriter was called
                mock_writer_class.assert_called_once()
                assert mock_writer.write_grid.called
                assert mock_writer.write_spectra.called

    def test_process_with_provided_config(self):
        """Test process method with provided config."""
        # Create processor with config
        config_dict = {
            "base_url": "https://datamesh.example.com",
            "token": "test-token"
        }
        processor = DataMeshPostprocessor(config_dict)
        
        # Create mock model_run
        model_run = Mock()
        model_run.run_id = "test-run-456"
        model_run.output_dir = "/tmp/rompy"
        
        config_dict_mock = Mock()
        config_dict_mock.dict.return_value = {"run_id_subdir": False}
        model_run.config = config_dict_mock

        # Create temporary directory structure
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir) / "test-run-456"
            output_dir.mkdir()
            
            # Create mock output files
            grid_file = output_dir / "swangrid.nc"
            grid_file.touch()
            
            model_run.output_dir = str(temp_dir)
            
            # Mock DatameshWriter methods
            with patch('rompy_oceanum.postprocess.DatameshWriter') as mock_writer_class:
                mock_writer = Mock()
                mock_writer_class.return_value = mock_writer
                
                # Run process method
                result = processor.process(model_run, dataset_name="test-dataset")
                
                # Assertions
                assert result["success"] is True
                assert result["run_id"] == "test-run-456"
                assert result["dataset_name"] == "test-dataset"
                assert "register_grid" in result["stages_completed"]
                
                # Verify DatameshWriter was called
                mock_writer_class.assert_called_once()
                assert mock_writer.write_grid.called

    def test_process_missing_output_dir(self):
        """Test process method with missing output directory."""
        # Create processor
        processor = DataMeshPostprocessor()
        
        # Create mock model_run
        model_run = Mock()
        model_run.run_id = "test-run-789"
        model_run.output_dir = "/tmp/rompy"
        
        config_dict = Mock()
        config_dict.dict.return_value = {"run_id_subdir": False}
        model_run.config = config_dict

        # Test with non-existent directory
        with tempfile.TemporaryDirectory() as temp_dir:
            model_run.output_dir = str(Path(temp_dir) / "non-existent")
            
            # Run process method
            result = processor.process(model_run)
            
            # Assertions
            assert result["success"] is False
            assert "Output directory does not exist" in result["message"]

    def test_process_no_output_files(self):
        """Test process method with no output files."""
        # Create processor
        processor = DataMeshPostprocessor()
        
        # Create mock model_run
        model_run = Mock()
        model_run.run_id = "test-run-999"
        model_run.output_dir = "/tmp/rompy"
        
        config_dict = Mock()
        config_dict.dict.return_value = {"run_id_subdir": False}
        model_run.config = config_dict

        # Create empty output directory
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir) / "test-run-999"
            output_dir.mkdir()
            
            model_run.output_dir = str(temp_dir)
            
            # Mock DatameshWriter methods
            with patch('rompy_oceanum.postprocess.DatameshWriter') as mock_writer_class:
                mock_writer = Mock()
                mock_writer_class.return_value = mock_writer
                
                # Run process method
                result = processor.process(model_run)
                
                # Assertions
                assert result["success"] is True
                # No stages should be completed since there are no files
                assert len(result["stages_completed"]) == 0
                
                # Verify DatameshWriter was called but no write methods were called
                mock_writer_class.assert_called_once()
                assert not mock_writer.write_grid.called
                assert not mock_writer.write_spectra.called