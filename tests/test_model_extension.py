"""
Pytest tests for the model extension functionality.
"""

import os
***REMOVED***
import pytest
from unittest.mock import MagicMock, patch

from rompy_oceanum.model_extension import submit_to_prax, to_prax_parameters, add_prax_methods_to_model_run
from rompy_oceanum.prax import PraxResult


class TestModelExtension:
    """Test the model extension functionality."""
    
    def test_to_prax_parameters(self, mock_rompy_model_run):
        """Test converting a model run to Prax parameters."""
        # Call the function
        parameters = to_prax_parameters(mock_rompy_model_run)
        
        # Check result
        assert "rompy-config" in parameters
        assert "run_id: test-run" in parameters["rompy-config"]
        assert "model_type: swanconfig" in parameters["rompy-config"]
        mock_rompy_model_run.to_dict.assert_called_once()
    
    def test_submit_to_prax(self, mock_rompy_model_run, mock_prax_env):
        """Test submitting a model run to Prax."""
        # Set up mock client
        mock_client = MagicMock()
        mock_result = MagicMock()
        
        with patch("rompy_oceanum.model_extension.PraxClient", return_value=mock_client) as mock_client_class:
            # Set up mock response
            mock_client.submit_pipeline.return_value = mock_result
            
            # Call the function
            result = submit_to_prax(
                mock_rompy_model_run,
                pipeline_name="test-pipeline",
                stage="test-stage"
            )
            
            # Check result
            assert result == mock_result
            
            # Check client creation
            mock_client_class.assert_called_once_with(
                base_url="https://prax.oceanum.io", 
                token=None
            )
            
            # Check submit_pipeline call
            mock_client.submit_pipeline.assert_called_once()
            args, kwargs = mock_client.submit_pipeline.call_args
            assert kwargs["pipeline_name"] == "test-pipeline"
            assert kwargs["user"] == "test-user"
            assert kwargs["org"] == "test-org"
            assert kwargs["project"] == "test-project"
            assert kwargs["stage"] == "test-stage"
            assert "parameters" in kwargs
    
    def test_submit_to_prax_with_explicit_params(self, mock_rompy_model_run):
        """Test submitting a model run with explicit parameters."""
        # Set up mock client
        mock_client = MagicMock()
        mock_result = MagicMock()
        
        with patch("rompy_oceanum.model_extension.PraxClient", return_value=mock_client) as mock_client_class:
            # Set up mock response
            mock_client.submit_pipeline.return_value = mock_result
            
            # Call the function with explicit parameters
            result = submit_to_prax(
                mock_rompy_model_run,
                pipeline_name="test-pipeline",
                user="explicit-user",
                org="explicit-org",
                project="explicit-project",
                stage="explicit-stage",
                prax_url="https://explicit.prax.io",
                token="explicit-token"
            )
            
            # Check result
            assert result == mock_result
            
            # Check client creation with explicit parameters
            mock_client_class.assert_called_once_with(
                base_url="https://explicit.prax.io", 
                token="explicit-token"
            )
            
            # Check submit_pipeline call with explicit parameters
            mock_client.submit_pipeline.assert_called_once()
            args, kwargs = mock_client.submit_pipeline.call_args
            assert kwargs["pipeline_name"] == "test-pipeline"
            assert kwargs["user"] == "explicit-user"
            assert kwargs["org"] == "explicit-org"
            assert kwargs["project"] == "explicit-project"
            assert kwargs["stage"] == "explicit-stage"
            assert "parameters" in kwargs
    
    def test_submit_to_prax_missing_required_params(self, mock_rompy_model_run):
        """Test error handling for missing required parameters."""
        # Clear environment variables
        with patch.dict(os.environ, clear=True):
            # Should raise ValueError for missing user
            with pytest.raises(ValueError, match="User is required"):
                submit_to_prax(mock_rompy_model_run)
            
            # Should raise ValueError for missing org
            with pytest.raises(ValueError, match="Organization is required"):
                submit_to_prax(mock_rompy_model_run, user="test-user")
            
            # Should raise ValueError for missing project
            with pytest.raises(ValueError, match="Project is required"):
                submit_to_prax(
                    mock_rompy_model_run, 
                    user="test-user", 
                    org="test-org"
                )
    
    @patch("rompy_oceanum.model_extension.logger")
    def test_add_prax_methods_to_model_run(self, mock_logger):
        """Test adding Prax methods to rompy ModelRun class."""
        # Mock the rompy module structure
        mock_model_run_class = MagicMock()
        mock_model_module = MagicMock()
        mock_model_module.ModelRun = mock_model_run_class
        
        # Store the original modules and ModelRun if they exist
        original_modules = {}
        for module_name in ['rompy', 'rompy.model']:
            if module_name in sys.modules:
                original_modules[module_name] = sys.modules[module_name]
        
        # Store original ModelRun
        from rompy_oceanum.model_extension import ModelRun as orig_model_run
        
        # Add mock modules to sys.modules
        sys.modules['rompy.model'] = mock_model_module
        if 'rompy' not in sys.modules:
            sys.modules['rompy'] = MagicMock()
        sys.modules['rompy'].model = mock_model_module
        
        try:
            # Clear module-level ModelRun to force reimport
            import rompy_oceanum.model_extension
            rompy_oceanum.model_extension.ModelRun = None
            
            # Call function when ModelRun doesn't have submit_to_prax
            mock_model_run_class.submit_to_prax = None
            mock_model_run_class.to_prax_parameters = None
            
            add_prax_methods_to_model_run()
            
            # After the call, check that the module's ModelRun variable is assigned our mock class
            assert rompy_oceanum.model_extension.ModelRun == mock_model_run_class
            
            # Check that methods were added
            assert mock_model_run_class.submit_to_prax == submit_to_prax
            assert mock_model_run_class.to_prax_parameters == to_prax_parameters
            mock_logger.info.assert_called_with("Added Prax methods to rompy ModelRun class")
            
            # Reset and test when methods already exist
            mock_logger.reset_mock()
            mock_model_run_class.submit_to_prax = MagicMock()
            
            add_prax_methods_to_model_run()
            
            # Check that logger was called with already added message
            mock_logger.info.assert_called_with("Prax methods already added to rompy ModelRun class")
        finally:
            # Restore the original ModelRun
            rompy_oceanum.model_extension.ModelRun = orig_model_run
            
            # Restore the original modules
            for module_name, module in original_modules.items():
                sys.modules[module_name] = module
                
            # If we added modules that weren't there before, remove them
            if 'rompy.model' not in original_modules and 'rompy.model' in sys.modules:
                del sys.modules['rompy.model']
    
    @patch("rompy_oceanum.model_extension.logger")
    def test_add_prax_methods_import_error(self, mock_logger):
        """Test handling of import error when adding methods."""
        # Store the original modules if they exist
        original_modules = {}
        for module_name in ['rompy', 'rompy.model']:
            if module_name in sys.modules:
                original_modules[module_name] = sys.modules[module_name]
        
        # Set up import error
        if 'rompy' in sys.modules:
            del sys.modules['rompy']
        if 'rompy.model' in sys.modules:
            del sys.modules['rompy.model']
        
        try:
            # Patch the ModelRun to be None
            with patch("rompy_oceanum.model_extension.ModelRun", None), \
                patch("importlib.import_module", side_effect=ImportError("Module not found")):
                
                # Call function
                add_prax_methods_to_model_run()
                
                # Check warning was logged
                mock_logger.warning.assert_called_with("Could not import rompy. Make sure it's installed.")
        finally:
            # Restore the original modules
            for module_name, module in original_modules.items():
                sys.modules[module_name] = module
