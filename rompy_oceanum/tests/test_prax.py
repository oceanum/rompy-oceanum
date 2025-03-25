"""
Tests for the Prax client functionality.
"""

import os
import unittest
from unittest.mock import patch, MagicMock

from rompy_oceanum.prax import PraxClient, PraxResult


class TestPraxClient(unittest.TestCase):
    """Test the PraxClient class."""
    
    def setUp(self):
        """Set up the test environment."""
        # Set up test environment variables
        os.environ["PRAX_TOKEN"] = "test_token"
        self.client = PraxClient()
    
    def test_init(self):
        """Test client initialization."""
        self.assertEqual(self.client.base_url, "https://prax.oceanum.io")
        self.assertEqual(self.client.token, "test_token")
        
        # Test custom base_url and token
        custom_client = PraxClient(base_url="https://custom.prax.io", token="custom_token")
        self.assertEqual(custom_client.base_url, "https://custom.prax.io")
        self.assertEqual(custom_client.token, "custom_token")
    
    def test_get_headers(self):
        """Test header generation."""
        headers = self.client._get_headers()
        self.assertEqual(headers["Authorization"], "test_token")
        self.assertEqual(headers["accept"], "application/json")
        self.assertEqual(headers["Content-Type"], "application/json")
        
        # Test missing token
        with patch.dict(os.environ, {}, clear=True):
            client_no_token = PraxClient()
            with self.assertRaises(ValueError):
                client_no_token._get_headers()
    
    @patch("requests.post")
    def test_submit_pipeline(self, mock_post):
        """Test pipeline submission."""
        # Set up mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "name": "test-run-id",
            "status": "Pending"
        }
        mock_post.return_value = mock_response
        
        # Submit pipeline
        result = self.client.submit_pipeline(
            pipeline_name="test-pipeline",
            user="test-user",
            org="test-org",
            project="test-project",
            stage="dev",
            parameters={"param1": "value1"}
        )
        
        # Check result
        self.assertIsInstance(result, PraxResult)
        self.assertEqual(result.run_id, "test-run-id")
        self.assertEqual(result.pipeline_name, "test-pipeline")
        self.assertEqual(result.user, "test-user")
        self.assertEqual(result.org, "test-org")
        self.assertEqual(result.project, "test-project")
        self.assertEqual(result.stage, "dev")
        self.assertEqual(result.status, "submitted")
        
        # Check API call
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        self.assertEqual(args[0], "https://prax.oceanum.io/api/pipelines/test-pipeline/submit")
        self.assertEqual(kwargs["params"], {
            "user": "test-user",
            "org": "test-org",
            "project": "test-project",
            "stage": "dev"
        })
        self.assertEqual(kwargs["json"], {"parameters": {"param1": "value1"}})
        
        # Test error response
        mock_response.status_code = 400
        mock_response.raise_for_status.side_effect = Exception("API error")
        with self.assertRaises(Exception):
            self.client.submit_pipeline(
                pipeline_name="test-pipeline",
                user="test-user",
                org="test-org",
                project="test-project",
                stage="dev",
                parameters={"param1": "value1"}
            )
            
    @patch("requests.get")
    def test_get_run_status(self, mock_get):
        """Test getting run status."""
        # Set up mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "name": "test-run-id",
            "status": "Running"
        }
        mock_get.return_value = mock_response
        
        # Get run status
        status = self.client.get_run_status(
            run_id="test-run-id",
            pipeline_name="test-pipeline",
            user="test-user",
            org="test-org",
            project="test-project",
            stage="dev"
        )
        
        # Check result
        self.assertEqual(status["name"], "test-run-id")
        self.assertEqual(status["status"], "Running")
        
        # Check API call
        mock_get.assert_called_once()
        args, kwargs = mock_get.call_args
        self.assertEqual(args[0], "https://prax.oceanum.io/api/pipelines/test-pipeline/runs/test-run-id")
        self.assertEqual(kwargs["params"], {
            "user": "test-user",
            "org": "test-org",
            "project": "test-project",
            "stage": "dev"
        })


class TestPraxResult(unittest.TestCase):
    """Test the PraxResult class."""
    
    def setUp(self):
        """Set up the test environment."""
        self.client = MagicMock()
        self.result = PraxResult(
            run_id="test-run-id",
            pipeline_name="test-pipeline",
            user="test-user",
            org="test-org",
            project="test-project",
            stage="dev",
            status="submitted",
            client=self.client
        )
    
    def test_get_status(self):
        """Test getting status from result."""
        # Set up mock client response
        self.client.get_run_status.return_value = {
            "name": "test-run-id",
            "status": "Running"
        }
        
        # Get status
        status = self.result.get_status()
        
        # Check result
        self.assertEqual(status["name"], "test-run-id")
        self.assertEqual(status["status"], "Running")
        
        # Check client call
        self.client.get_run_status.assert_called_once_with(
            run_id="test-run-id",
            pipeline_name="test-pipeline",
            user="test-user",
            org="test-org",
            project="test-project",
            stage="dev"
        )
        
        # Test with no client
        result_no_client = PraxResult(
            run_id="test-run-id",
            pipeline_name="test-pipeline",
            user="test-user",
            org="test-org",
            project="test-project",
            stage="dev",
            status="submitted",
            client=None
        )
        with self.assertRaises(ValueError):
            result_no_client.get_status()
    
    def test_get_logs(self):
        """Test getting logs from result."""
        # Set up mock client response
        self.client.get_run_logs.return_value = {
            "logs": "Test logs content"
        }
        
        # Get logs
        logs = self.result.get_logs()
        
        # Check result
        self.assertEqual(logs["logs"], "Test logs content")
        
        # Check client call
        self.client.get_run_logs.assert_called_once_with(
            run_id="test-run-id",
            pipeline_name="test-pipeline",
            user="test-user",
            org="test-org",
            project="test-project",
            stage="dev",
            task_name=None
        )
        
        # Test with task name
        self.result.get_logs(task_name="test-task")
        self.client.get_run_logs.assert_called_with(
            run_id="test-run-id",
            pipeline_name="test-pipeline",
            user="test-user",
            org="test-org",
            project="test-project",
            stage="dev",
            task_name="test-task"
        )


if __name__ == "__main__":
    unittest.main()
