"""
Unit tests for rompy-oceanum configuration models.

This module tests the Pydantic configuration models for the backend
implementations, following rompy's testing patterns.
"""
import os
import pytest
from unittest.mock import patch
from pydantic import ValidationError

from rompy_oceanum.config import (
    PraxTaskResources,
    PraxResources,
    PraxConfig,
    DataMeshConfig,
    RunConfig,
    PraxPipelineConfig
)


class TestPraxTaskResources:
    """Test PraxTaskResources configuration model."""

    def test_valid_cpu_formats(self):
        """Test valid CPU resource formats."""
        valid_cpus = ["1", "2", "1000m", "500m", "1.5"]

        for cpu in valid_cpus:
            resources = PraxTaskResources(cpu=cpu)
            assert resources.cpu == cpu

    def test_valid_memory_formats(self):
        """Test valid memory resource formats."""
        valid_memories = ["1Gi", "2Gi", "1024Mi", "512Mi", "1G", "2M", "1024K"]

        for memory in valid_memories:
            resources = PraxTaskResources(memory=memory)
            assert resources.memory == memory

    def test_invalid_cpu_format(self):
        """Test invalid CPU resource format."""
        with pytest.raises(ValidationError):
            PraxTaskResources(cpu="invalid")

    def test_invalid_memory_format(self):
        """Test invalid memory resource format."""
        with pytest.raises(ValidationError):
            PraxTaskResources(memory="invalid")

    def test_optional_fields(self):
        """Test that all fields are optional."""
        resources = PraxTaskResources()
        assert resources.cpu is None
        assert resources.memory is None


class TestPraxResources:
    """Test PraxResources configuration model."""

    def test_get_cpu_with_requests(self):
        """Test getting CPU from requests."""
        requests = PraxTaskResources(cpu="1000m")
        resources = PraxResources(requests=requests)
        assert resources.get_cpu() == "1000m"

    def test_get_cpu_without_requests(self):
        """Test getting CPU without requests."""
        resources = PraxResources()
        assert resources.get_cpu() is None

    def test_get_memory_with_requests(self):
        """Test getting memory from requests."""
        requests = PraxTaskResources(memory="2Gi")
        resources = PraxResources(requests=requests)
        assert resources.get_memory() == "2Gi"

    def test_get_memory_without_requests(self):
        """Test getting memory without requests."""
        resources = PraxResources()
        assert resources.get_memory() is None


class TestPraxConfig:
    """Test PraxConfig configuration model."""

    def test_valid_config(self):
        """Test valid configuration."""
        config = PraxConfig(
            base_url="https://prax.oceanum.io",
            token="test_token",
            org="test_org",
            project="test_project",
            stage="dev"
        )
        assert config.base_url == "https://prax.oceanum.io"
        assert config.token == "test_token"
        assert config.org == "test_org"
        assert config.project == "test_project"
        assert config.stage == "dev"

    def test_url_validation(self):
        """Test URL validation."""
        # Valid URLs
        valid_urls = [
            "https://prax.oceanum.io",
            "http://localhost:8080",
            "https://api.example.com/"
        ]

        for url in valid_urls:
            config = PraxConfig(
                base_url=url,
                token="test_token",
                org="test_org",
                project="test_project"
            )
            assert config.base_url == url.rstrip('/')

        # Invalid URLs
        invalid_urls = ["not-a-url", "ftp://example.com", ""]

        for url in invalid_urls:
            with pytest.raises(ValidationError):
                PraxConfig(
                    base_url=url,
                    token="test_token",
                    org="test_org",
                    project="test_project"
                )

    def test_token_validation(self):
        """Test token validation."""
        # Valid token
        config = PraxConfig(
            base_url="https://prax.oceanum.io",
            token="valid_token",
            org="test_org",
            project="test_project"
        )
        assert config.token == "valid_token"

        # Invalid tokens
        invalid_tokens = ["", "   ", None]

        for token in invalid_tokens:
            with pytest.raises(ValidationError):
                PraxConfig(
                    base_url="https://prax.oceanum.io",
                    token=token,
                    org="test_org",
                    project="test_project"
                )

    def test_identifier_validation(self):
        """Test organization and project identifier validation."""
        # Valid identifiers
        valid_ids = ["test", "test-org", "test_project", "org123"]

        for identifier in valid_ids:
            config = PraxConfig(
                base_url="https://prax.oceanum.io",
                token="test_token",
                org=identifier,
                project=identifier
            )
            assert config.org == identifier
            assert config.project == identifier

        # Invalid identifiers
        invalid_ids = ["", "   ", "test@org", "test/project"]

        for identifier in invalid_ids:
            with pytest.raises(ValidationError):
                PraxConfig(
                    base_url="https://prax.oceanum.io",
                    token="test_token",
                    org=identifier,
                    project="test_project"
                )

    def test_stage_validation(self):
        """Test stage validation."""
        # Valid stages
        valid_stages = ["dev", "staging", "prod"]

        for stage in valid_stages:
            config = PraxConfig(
                base_url="https://prax.oceanum.io",
                token="test_token",
                org="test_org",
                project="test_project",
                stage=stage
            )
            assert config.stage == stage

        # Invalid stage
        with pytest.raises(ValidationError):
            PraxConfig(
                base_url="https://prax.oceanum.io",
                token="test_token",
                org="test_org",
                project="test_project",
                stage="invalid"
            )

    def test_from_env_complete(self):
        """Test creating config from environment variables."""
        env_vars = {
            "PRAX_BASE_URL": "https://prax.oceanum.io",
            "PRAX_TOKEN": "env_token",
            "PRAX_ORG": "env_org",
            "PRAX_PROJECT": "env_project",
            "PRAX_STAGE": "staging",
            "PRAX_TIMEOUT": "7200"
        }

        with patch.dict(os.environ, env_vars):
            config = PraxConfig.from_env()
            assert config.base_url == "https://prax.oceanum.io"
            assert config.token == "env_token"
            assert config.org == "env_org"
            assert config.project == "env_project"
            assert config.stage == "staging"
            assert config.timeout == 7200

    def test_from_env_missing_required(self):
        """Test from_env with missing required fields."""
        env_vars = {
            "PRAX_BASE_URL": "https://prax.oceanum.io",
            # Missing PRAX_TOKEN, PRAX_ORG, PRAX_PROJECT
        }

        with patch.dict(os.environ, env_vars, clear=True):
            with pytest.raises(ValueError, match="Missing required configuration"):
                PraxConfig.from_env()

    def test_from_env_with_overrides(self):
        """Test from_env with overrides."""
        env_vars = {
            "PRAX_BASE_URL": "https://prax.oceanum.io",
            "PRAX_TOKEN": "env_token",
            "PRAX_ORG": "env_org",
            "PRAX_PROJECT": "env_project"
        }

        with patch.dict(os.environ, env_vars):
            config = PraxConfig.from_env(stage="prod", timeout=1800)
            assert config.stage == "prod"
            assert config.timeout == 1800

    def test_from_dict(self):
        """Test creating config from dictionary."""
        config_dict = {
            "base_url": "https://prax.oceanum.io",
            "token": "dict_token",
            "org": "dict_org",
            "project": "dict_project",
            "stage": "dev"
        }

        config = PraxConfig.from_dict(config_dict)
        assert config.base_url == "https://prax.oceanum.io"
        assert config.token == "dict_token"
        assert config.org == "dict_org"
        assert config.project == "dict_project"
        assert config.stage == "dev"


class TestDataMeshConfig:
    """Test DataMeshConfig configuration model."""

    def test_valid_config(self):
        """Test valid configuration."""
        config = DataMeshConfig(
            base_url="https://datamesh.oceanum.io",
            token="dm_token",
            dataset_name="test_dataset"
        )
        assert config.base_url == "https://datamesh.oceanum.io"
        assert config.token == "dm_token"
        assert config.dataset_name == "test_dataset"

    def test_from_env(self):
        """Test creating config from environment variables."""
        env_vars = {
            "DATAMESH_BASE_URL": "https://datamesh.oceanum.io",
            "DATAMESH_TOKEN": "env_dm_token",
            "DATAMESH_DATASET_NAME": "env_dataset"
        }

        with patch.dict(os.environ, env_vars):
            config = DataMeshConfig.from_env()
            assert config.base_url == "https://datamesh.oceanum.io"
            assert config.token == "env_dm_token"
            assert config.dataset_name == "env_dataset"

    def test_from_env_defaults(self):
        """Test from_env with default values."""
        env_vars = {
            "DATAMESH_TOKEN": "env_dm_token"
        }

        with patch.dict(os.environ, env_vars, clear=True):
            config = DataMeshConfig.from_env()
            assert config.base_url == "https://datamesh.oceanum.io"
            assert config.token == "env_dm_token"
            assert config.dataset_name is None


class TestRunConfig:
    """Test RunConfig configuration model."""

    def test_defaults(self):
        """Test default configuration."""
        config = RunConfig()
        assert config.command is None
        assert config.working_dir is None
        assert config.env_vars == {}
        assert config.build_image is True
        assert config.image_tag is None

    def test_get_run_command_default(self):
        """Test get_run_command with default."""
        config = RunConfig()
        assert config.get_run_command() == "python -m rompy run"

    def test_get_run_command_custom(self):
        """Test get_run_command with custom command."""
        config = RunConfig(command="custom command")
        assert config.get_run_command() == "custom command"

    def test_should_build_image(self):
        """Test should_build_image."""
        config = RunConfig(build_image=True)
        assert config.should_build_image() is True

        config = RunConfig(build_image=False)
        assert config.should_build_image() is False

    def test_working_dir_validation(self):
        """Test working directory validation."""
        # Valid absolute path
        config = RunConfig(working_dir="/tmp/test")
        assert config.working_dir == "/tmp/test"

        # Invalid relative path
        with pytest.raises(ValidationError):
            RunConfig(working_dir="relative/path")


class TestPraxPipelineConfig:
    """Test PraxPipelineConfig configuration model."""

    def test_valid_config(self):
        """Test valid configuration."""
        prax_config = PraxConfig(
            base_url="https://prax.oceanum.io",
            token="test_token",
            org="test_org",
            project="test_project"
        )

        config = PraxPipelineConfig(
            prax=prax_config,
            pipeline_name="test_pipeline"
        )
        assert config.prax == prax_config
        assert config.pipeline_name == "test_pipeline"
        assert config.datamesh is None
        assert isinstance(config.run, RunConfig)

    def test_from_env(self):
        """Test creating config from environment variables."""
        env_vars = {
            "PRAX_BASE_URL": "https://prax.oceanum.io",
            "PRAX_TOKEN": "env_token",
            "PRAX_ORG": "env_org",
            "PRAX_PROJECT": "env_project",
            "DATAMESH_BASE_URL": "https://datamesh.oceanum.io",
            "DATAMESH_TOKEN": "dm_token"
        }

        with patch.dict(os.environ, env_vars):
            config = PraxPipelineConfig.from_env("test_pipeline")
            assert config.pipeline_name == "test_pipeline"
            assert config.prax.token == "env_token"
            assert config.datamesh.token == "dm_token"

    def test_from_env_without_datamesh(self):
        """Test from_env without DataMesh configuration."""
        env_vars = {
            "PRAX_BASE_URL": "https://prax.oceanum.io",
            "PRAX_TOKEN": "env_token",
            "PRAX_ORG": "env_org",
            "PRAX_PROJECT": "env_project"
        }

        with patch.dict(os.environ, env_vars, clear=True):
            config = PraxPipelineConfig.from_env("test_pipeline")
            assert config.pipeline_name == "test_pipeline"
            assert config.prax.token == "env_token"
            assert config.datamesh is None

    def test_pipeline_name_validation(self):
        """Test pipeline name validation."""
        prax_config = PraxConfig(
            base_url="https://prax.oceanum.io",
            token="test_token",
            org="test_org",
            project="test_project"
        )

        # Valid pipeline name
        config = PraxPipelineConfig(
            prax=prax_config,
            pipeline_name="valid_pipeline"
        )
        assert config.pipeline_name == "valid_pipeline"

        # Invalid pipeline names
        invalid_names = ["", "   ", None]

        for name in invalid_names:
            with pytest.raises(ValidationError):
                PraxPipelineConfig(
                    prax=prax_config,
                    pipeline_name=name
                )
