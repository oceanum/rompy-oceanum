"""
Tests for the model extension functionality.
"""

import os
import unittest
from unittest.mock import patch, MagicMock, call

from rompy_oceanum.model_extension import add_prax_methods_to_model_run


class TestModelExtension(unittest.TestCase):
    """Test the model extension functionality."""
    
    @patch("rompy_oceanum.model_extension.ModelRun")
    @patch("rompy_oceanum.model_extension.logger")
    def test_add_prax_methods_to_model_run(self, mock_logger, mock_model_run):
        """Test adding Prax methods to ModelRun."""
        # Test when methods don't already exist
        mock_model_run.submit_to_prax = None
        mock_model_run.to_prax_parameters = None
        
        # Call the function
        add_prax_methods_to_model_run()
        
        # Check that logger was called
        mock_logger.info.assert_called_with("Added Prax methods to rompy ModelRun class")
        
    @patch("rompy.model.ModelRun")
    @patch("rompy_oceanum.model_extension.PraxClient")
    def test_submit_to_prax(self, mock_prax_client, mock_model_run):
        """Test submitting a model run to Prax."""
        # Import here to avoid circular imports during actual usage
        from rompy_oceanum.model_extension import submit_to_prax
        
        # Set up mock model run
        model_run = MagicMock()
        model_run.to_prax_parameters.return_value = {"rompy-config": "test-config"}
        
        # Set up mock Prax client
        mock_client_instance = MagicMock()
        mock_prax_client.return_value = mock_client_instance
        mock_client_instance.submit_pipeline.return_value = "test-result"
        
        # Set environment variables
        os.environ["PRAX_USER"] = "env-user"
        os.environ["PRAX_ORG"] = "env-org"
        os.environ["PRAX_PROJECT"] = "env-project"
        
        # Call the function
        result = submit_to_prax(
            model_run,
            pipeline_name="test-pipeline",
            stage="test-stage"
        )
        
        # Check result
        self.assertEqual(result, "test-result")
        
        # Check client creation
        mock_prax_client.assert_called_once_with(base_url="https://prax.oceanum.io", token=None)
        
        # Check submit_pipeline call
        mock_client_instance.submit_pipeline.assert_called_once_with(
            pipeline_name="test-pipeline",
            user="env-user",
            org="env-org",
            project="env-project",
            stage="test-stage",
            parameters={"rompy-config": "test-config"}
        )
        
        # Test with explicit parameters
        result = submit_to_prax(
            model_run,
            pipeline_name="test-pipeline",
            user="explicit-user",
            org="explicit-org",
            project="explicit-project",
            stage="explicit-stage",
            prax_url="https://explicit.prax.io",
            token="explicit-token"
        )
        
        # Check client creation with explicit parameters
        mock_prax_client.assert_called_with(base_url="https://explicit.prax.io", token="explicit-token")
        
        # Check submit_pipeline call with explicit parameters
        mock_client_instance.submit_pipeline.assert_called_with(
            pipeline_name="test-pipeline",
            user="explicit-user",
            org="explicit-org",
            project="explicit-project",
            stage="explicit-stage",
            parameters={"rompy-config": "test-config"}
        )
        
        # Test missing required parameters
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(ValueError):
                submit_to_prax(model_run)
    
    def test_to_prax_parameters(self):
        """Test converting a model run to Prax parameters."""
        # Import here to avoid circular imports during actual usage
        from rompy_oceanum.model_extension import to_prax_parameters
        
        # Set up mock model run
        model_run = MagicMock()
        model_run.to_dict.return_value = {"key": "value"}
        
        # Call the function
        parameters = to_prax_parameters(model_run)
        
        # Check result
        self.assertIn("rompy-config", parameters)
        self.assertIn("key: value", parameters["rompy-config"])


if __name__ == "__main__":
    unittest.main()
