"""
Pytest configuration file for rompy-oceanum tests.
"""

import os
import pytest
from unittest.mock import MagicMock


@pytest.fixture
def mock_prax_token():
    """Set up mock PRAX_TOKEN environment variable."""
    os.environ["PRAX_TOKEN"] = "test-token"
    yield "test-token"
    if "PRAX_TOKEN" in os.environ:
        del os.environ["PRAX_TOKEN"]


@pytest.fixture
def mock_prax_env():
    """Set up mock environment variables for Prax."""
    os.environ["PRAX_TOKEN"] = "test-token"
    os.environ["PRAX_USER"] = "test-user"
    os.environ["PRAX_ORG"] = "test-org"
    os.environ["PRAX_PROJECT"] = "test-project"
    yield
    for var in ["PRAX_TOKEN", "PRAX_USER", "PRAX_ORG", "PRAX_PROJECT"]:
        if var in os.environ:
            del os.environ[var]


@pytest.fixture
def mock_requests(monkeypatch):
    """Mock requests library."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"name": "test-run-id", "status": "Running"}
    mock_response.text = '{"name": "test-run-id", "status": "Running"}'
    
    def mock_make_request(self, method, url, **kwargs):
        return mock_response.json()
    
    monkeypatch.setattr("rompy_oceanum.client.PraxClient._make_request", mock_make_request)
    
    return {
        "response": mock_response
    }


@pytest.fixture
def mock_rompy_model_run():
    """Mock rompy ModelRun class."""
    mock_model_run = MagicMock()
    mock_model_run.to_dict.return_value = {
        "run_id": "test-run",
        "config": {
            "model_type": "swanconfig",
            "startup": {"project": {"name": "Test project"}}
        }
    }
    return mock_model_run
