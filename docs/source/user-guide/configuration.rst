Configuration
=============

This guide covers all aspects of configuring rompy-oceanum for your environment and use cases. Learn how to set up authentication, configure backends, and customize behavior for optimal performance.

Overview
--------

rompy-oceanum supports multiple configuration methods to provide flexibility for different deployment scenarios:

* **Environment Variables**: Secure authentication and default settings
* **Configuration Files**: Reusable settings and complex configurations
* **Programmatic Configuration**: Dynamic settings for automated workflows
* **Runtime Parameters**: Override settings for specific operations

Configuration Hierarchy
~~~~~~~~~~~~~~~~~~~~~~~~

Settings are applied in the following order (later sources override earlier ones):

1. Default values
2. Configuration files (``~/.rompy-oceanum/config.yaml``)
3. Environment variables
4. Command-line arguments
5. Programmatic parameters

Authentication Configuration
----------------------------

Prax Authentication
~~~~~~~~~~~~~~~~~~~

Configure authentication for Oceanum Prax services:

**Environment Variables (Recommended):**

.. code-block:: bash

   # Required authentication token
   export PRAX_TOKEN="your-authentication-token"

   # API endpoint
   export PRAX_BASE_URL="https://prax.oceanum.science"

   # Organization and project
   export PRAX_ORG="your-organization"
   export PRAX_PROJECT="your-project"

   # Deployment stage
   export PRAX_STAGE="dev"  # or "prod"

**Configuration File:**

.. code-block:: yaml

   # ~/.rompy-oceanum/config.yaml
   prax:
     token: "${PRAX_TOKEN}"  # Use environment variable
     base_url: "https://prax.oceanum.science"
     org: "my-organization"
     project: "wave-modeling"
     stage: "dev"

**Programmatic Configuration:**

.. code-block:: python

   from rompy_oceanum.config import PraxConfig

   config = PraxConfig(
       token="your-token",  # Better to use environment variable
       base_url="https://prax.oceanum.science",
       org="my-organization",
       project="wave-modeling",
       stage="dev"
   )

DataMesh Authentication
~~~~~~~~~~~~~~~~~~~~~~~

Configure DataMesh integration for output registration:

.. code-block:: bash

   # DataMesh API endpoint
   export DATAMESH_BASE_URL="https://datamesh.oceanum.science"

   # Authentication token (may be same as Prax)
   export DATAMESH_TOKEN="${PRAX_TOKEN}"

Backend Configuration
---------------------

Prax Pipeline Backend
~~~~~~~~~~~~~~~~~~~~~

Configure the Prax pipeline backend for remote execution:

**Basic Configuration:**

.. code-block:: yaml

   prax:
     # Connection settings
     base_url: "https://prax.oceanum.science"
     timeout: 3600  # 1 hour timeout
     retry_attempts: 3
     retry_delay: 5  # seconds

     # Default pipeline settings
     default_pipeline: "swan-from-rompy"
     default_stage: "dev"

     # Resource requirements
     cpu_limit: "2"
     memory_limit: "4Gi"
     storage_limit: "10Gi"

**Advanced Configuration:**

.. code-block:: yaml

   prax:
     # Pipeline-specific settings
     pipelines:
       swan-from-rompy:
         timeout: 7200  # 2 hours for SWAN models
         cpu_limit: "4"
         memory_limit: "8Gi"

       schism-from-rompy:
         timeout: 14400  # 4 hours for SCHISM models
         cpu_limit: "8"
         memory_limit: "16Gi"

     # Monitoring settings
     status_check_interval: 30  # seconds
     log_level: "INFO"

     # Output settings
     auto_download: true
     download_timeout: 600  # 10 minutes
     cleanup_on_success: false

DataMesh Configuration
~~~~~~~~~~~~~~~~~~~~~~

Configure output registration and data management:

.. code-block:: yaml

   datamesh:
     # Connection settings
     base_url: "https://datamesh.oceanum.science"
     register_outputs: true

     # Default metadata
     default_tags:
       - "wave-model"
       - "rompy"

     # Dataset configuration
     dataset_naming: "{model_type}_{run_id}_{timestamp}"
     description_template: "Wave model output from {model_type}"

     # File handling
     supported_formats:
       - "*.nc"
       - "*.zarr"
       - "*.txt"

     # Registration settings
     auto_register: true
     visibility: "private"  # or "public", "organization"

Configuration Files
-------------------

Global Configuration
~~~~~~~~~~~~~~~~~~~~~

Create a global configuration file at ``~/.rompy-oceanum/config.yaml``:

.. code-block:: yaml

   # Global rompy-oceanum configuration

   # Default backend settings
   default_backend: "prax"

   # Prax configuration
   prax:
     base_url: "https://prax.oceanum.science"
     org: "my-organization"
     project: "wave-modeling"
     stage: "dev"
     timeout: 3600

     # Default pipeline per model type
     model_pipelines:
       swan: "swan-from-rompy"
       schism: "schism-from-rompy"
       ww3: "ww3-from-rompy"

   # DataMesh configuration
   datamesh:
     base_url: "https://datamesh.oceanum.science"
     register_outputs: true
     default_tags:
       - "wave-model"
       - "{{model_type}}"
       - "{{org}}"

   # Logging configuration
   logging:
     level: "INFO"
     format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
     file: "~/.rompy-oceanum/logs/rompy-oceanum.log"

   # Default directories
   directories:
     output: "./outputs"
     config: "./configs"
     cache: "~/.rompy-oceanum/cache"

Project-Specific Configuration
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Create project-specific configurations:

.. code-block:: yaml

   # project-config.yaml

   # Project metadata
   project:
     name: "australia-wave-forecast"
     description: "Operational wave forecasting for Australian waters"
     version: "1.0.0"

   # Model configurations
   models:
     operational_swan:
       pipeline: "swan-operational"
       stage: "prod"
       timeout: 1800
       schedule: "0 */6 * * *"  # Every 6 hours

     research_swan:
       pipeline: "swan-research"
       stage: "dev"
       timeout: 3600

   # Output configuration
   outputs:
     register_in_datamesh: true
     tags:
       - "australia"
       - "operational"
       - "wave-forecast"
     retention_days: 30

Environment Variables
---------------------

Complete Environment Variable Reference
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Authentication:**

.. code-block:: bash

   # Prax authentication
   PRAX_TOKEN="your-prax-token"
   PRAX_BASE_URL="https://prax.oceanum.science"
   PRAX_ORG="your-organization"
   PRAX_PROJECT="your-project"
   PRAX_STAGE="dev"

   # DataMesh authentication
   DATAMESH_TOKEN="your-datamesh-token"
   DATAMESH_BASE_URL="https://datamesh.oceanum.science"

**Behavior Control:**

.. code-block:: bash

   # Logging
   ROMPY_OCEANUM_LOG_LEVEL="INFO"
   ROMPY_OCEANUM_LOG_FILE="/var/log/rompy-oceanum.log"

   # Timeouts
   PRAX_TIMEOUT="3600"
   PRAX_STATUS_CHECK_INTERVAL="30"

   # Directories
   ROMPY_OCEANUM_OUTPUT_DIR="./outputs"
   ROMPY_OCEANUM_CONFIG_DIR="./configs"
   ROMPY_OCEANUM_CACHE_DIR="~/.cache/rompy-oceanum"

**Development/Debug:**

.. code-block:: bash

   # Debug mode
   ROMPY_OCEANUM_DEBUG="true"

   # Skip SSL verification (development only)
   PRAX_VERIFY_SSL="false"

   # Mock mode for testing
   ROMPY_OCEANUM_MOCK_MODE="true"

Programmatic Configuration
--------------------------

Dynamic Configuration
~~~~~~~~~~~~~~~~~~~~~~

Configure settings programmatically for automated workflows:

.. code-block:: python

   from rompy_oceanum.config import PraxConfig, DataMeshConfig, RompyOceanumConfig

   # Create configuration objects
   prax_config = PraxConfig(
       base_url="https://prax.oceanum.science",
       org="my-organization",
       project="wave-modeling",
       stage="dev",
       timeout=3600
   )

   datamesh_config = DataMeshConfig(
       base_url="https://datamesh.oceanum.science",
       register_outputs=True,
       default_tags=["wave-model", "automated"]
   )

   # Combine into main configuration
   config = RompyOceanumConfig(
       prax=prax_config,
       datamesh=datamesh_config,
       default_backend="prax"
   )

   # Use configuration
   result = model_run.pipeline(
       pipeline_backend="prax",
       config=config
   )

Configuration Validation
~~~~~~~~~~~~~~~~~~~~~~~~~

Validate configurations before use:

.. code-block:: python

   from rompy_oceanum.config import validate_configuration

   # Validate configuration file
   config = validate_configuration("config.yaml")

   # Validate programmatic configuration
   try:
       prax_config = PraxConfig(
           base_url="invalid-url",
           org="test-org"
       )
   except ValidationError as e:
       print(f"Configuration error: {e}")

Runtime Configuration
---------------------

Command-Line Overrides
~~~~~~~~~~~~~~~~~~~~~~~

Override configuration values from the command line:

.. code-block:: bash

   # Override organization and project
   rompy-oceanum run \
       --config swan_config.yaml \
       --prax-org "different-org" \
       --prax-project "different-project" \
       --prax-stage "prod"

   # Override timeout and pipeline
   rompy-oceanum run \
       --config swan_config.yaml \
       --pipeline "custom-swan-pipeline" \
       --timeout 7200

Pipeline-Specific Parameters
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Pass parameters specific to individual pipeline runs:

.. code-block:: python

   # Runtime parameter override
   result = model_run.pipeline(
       pipeline_backend="prax",
       pipeline_name="swan-from-rompy",

       # Override default settings
       timeout=7200,
       cpu_limit="4",
       memory_limit="8Gi",

       # Pipeline-specific parameters
       custom_parameters={
           "use_gpu": True,
           "mpi_processes": 4,
           "debug_mode": False
       }
   )

Security Configuration
----------------------

Token Management
~~~~~~~~~~~~~~~~

Best practices for secure token management:

**1. Use Environment Variables:**

.. code-block:: bash

   # Store in secure environment
   export PRAX_TOKEN="$(cat /secure/path/prax-token)"

**2. Use Secret Management Systems:**

.. code-block:: python

   import os
   from rompy_oceanum.config import PraxConfig

   # AWS Secrets Manager example
   import boto3

   def get_secret(secret_name):
       client = boto3.client('secretsmanager')
       response = client.get_secret_value(SecretId=secret_name)
       return response['SecretString']

   # Use secret in configuration
   config = PraxConfig(
       token=get_secret("prax-token"),
       org=os.environ["PRAX_ORG"],
       project=os.environ["PRAX_PROJECT"]
   )

**3. File Permissions:**

.. code-block:: bash

   # Secure configuration files
   chmod 600 ~/.rompy-oceanum/config.yaml
   chown $USER:$USER ~/.rompy-oceanum/config.yaml

SSL/TLS Configuration
~~~~~~~~~~~~~~~~~~~~~

Configure SSL verification and certificates:

.. code-block:: yaml

   prax:
     base_url: "https://prax.oceanum.science"
     verify_ssl: true
     ca_bundle: "/path/to/ca-bundle.crt"
     client_cert: "/path/to/client.crt"
     client_key: "/path/to/client.key"

Configuration Validation
------------------------

Validation Schema
~~~~~~~~~~~~~~~~~

rompy-oceanum validates all configuration using Pydantic models:

.. code-block:: python

   from rompy_oceanum.config import PraxConfig
   from pydantic import ValidationError

   try:
       config = PraxConfig(
           base_url="https://prax.oceanum.science",
           org="my-org",
           timeout="invalid"  # Should be int
       )
   except ValidationError as e:
       print("Configuration errors:")
       for error in e.errors():
           print(f"  {error['loc']}: {error['msg']}")

Configuration Testing
~~~~~~~~~~~~~~~~~~~~~

Test your configuration before deployment:

.. code-block:: python

   from rompy_oceanum.client import PraxClient
   from rompy_oceanum.config import load_configuration

   # Load and test configuration
   config = load_configuration("config.yaml")

   # Test connection
   client = PraxClient(config.prax)
   try:
       status = client.health_check()
       print(f"Connection successful: {status}")
   except Exception as e:
       print(f"Connection failed: {e}")

CLI Configuration Commands
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Use CLI commands to validate and manage configuration:

.. code-block:: bash

   # Validate configuration file
   rompy-oceanum config validate config.yaml

   # Show current configuration
   rompy-oceanum config show

   # Test connection
   rompy-oceanum config test-connection

   # Initialize default configuration
   rompy-oceanum config init

Troubleshooting Configuration
-----------------------------

Common Issues
~~~~~~~~~~~~~

**1. Authentication Failures:**

.. code-block:: bash

   # Check token validity
   rompy-oceanum config test-connection

   # Verify environment variables
   echo $PRAX_TOKEN | head -c 20  # Show first 20 chars

**2. Configuration File Errors:**

.. code-block:: bash

   # Validate YAML syntax
   python -c "import yaml; yaml.safe_load(open('config.yaml'))"

   # Validate rompy-oceanum configuration
   rompy-oceanum config validate config.yaml

**3. Permission Issues:**

.. code-block:: bash

   # Check file permissions
   ls -la ~/.rompy-oceanum/config.yaml

   # Fix permissions
   chmod 600 ~/.rompy-oceanum/config.yaml

Debug Configuration Loading
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Enable debug mode to troubleshoot configuration issues:

.. code-block:: python

   import logging
   from rompy_oceanum.config import load_configuration

   # Enable debug logging
   logging.basicConfig(level=logging.DEBUG)

   # Load configuration with debug info
   config = load_configuration("config.yaml", debug=True)

Best Practices
--------------

Security Best Practices
~~~~~~~~~~~~~~~~~~~~~~~~

1. **Never hardcode tokens** in configuration files or code
2. **Use environment variables** for sensitive information
3. **Secure configuration files** with appropriate permissions
4. **Rotate tokens regularly** and update configurations
5. **Use least privilege** principle for service accounts

Performance Best Practices
~~~~~~~~~~~~~~~~~~~~~~~~~~~

1. **Set appropriate timeouts** based on model complexity
2. **Configure retry logic** for transient failures
3. **Use connection pooling** for high-frequency operations
4. **Cache configuration** to avoid repeated file reads
5. **Monitor resource usage** and adjust limits accordingly

Maintenance Best Practices
~~~~~~~~~~~~~~~~~~~~~~~~~~~

1. **Version control** configuration files
2. **Document configuration changes** and rationale
3. **Test configurations** in development before production
4. **Monitor configuration drift** in deployed systems
5. **Regularly review** and update configurations

Example Configurations
----------------------

Development Environment
~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: yaml

   # dev-config.yaml
   prax:
     base_url: "https://prax-dev.oceanum.science"
     org: "development"
     project: "wave-models-dev"
     stage: "dev"
     timeout: 1800
     debug: true

   datamesh:
     register_outputs: false  # Skip registration in dev

   logging:
     level: "DEBUG"

Production Environment
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: yaml

   # prod-config.yaml
   prax:
     base_url: "https://prax.oceanum.science"
     org: "production"
     project: "operational-forecasting"
     stage: "prod"
     timeout: 3600
     retry_attempts: 5

   datamesh:
     register_outputs: true
     default_tags:
       - "operational"
       - "production"

   logging:
     level: "INFO"
     file: "/var/log/rompy-oceanum/production.log"

Testing Environment
~~~~~~~~~~~~~~~~~~~

.. code-block:: yaml

   # test-config.yaml
   prax:
     base_url: "https://prax-test.oceanum.science"
     org: "testing"
     project: "automated-tests"
     stage: "test"
     timeout: 600  # Shorter timeout for tests
     mock_mode: true  # Use mocked responses

   datamesh:
     register_outputs: false

   logging:
     level: "DEBUG"
     file: "/tmp/rompy-oceanum-test.log"

Next Steps
----------

Now that you understand configuration:

* Review :doc:`pipeline-backends` for backend-specific settings
* Explore :doc:`cli-reference` for command-line configuration options
* Check :doc:`troubleshooting` for configuration-related issues
* See :doc:`../examples/advanced-configuration` for complex scenarios
