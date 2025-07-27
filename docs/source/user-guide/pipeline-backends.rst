Pipeline Backends
=================

rompy-oceanum supports multiple pipeline execution backends, allowing you to choose the most appropriate execution environment for your wave modeling workflows. This guide covers the available backends, their configuration, and best practices for each.

Overview
--------

Pipeline backends determine where and how your rompy model configurations are executed. rompy-oceanum currently supports:

* **Prax Backend**: Cloud-native execution via Oceanum's Prax pipeline system
* **Local Backend**: Direct execution on your local machine (inherited from rompy)

Backend Selection
-----------------

You can specify the backend when running your model:

.. code-block:: python

   import rompy
   from rompy_oceanum import PraxPipelineBackend

   # Create your model configuration
   model_run = rompy.ModelRun(config=your_config)

   # Execute using Prax backend
   result = model_run.pipeline(
       backend="prax",
       pipeline_name="my-wave-model",
       **backend_config
   )

Or via the CLI:

.. code-block:: bash

   # Using Prax backend
   oceanum rompy run config.yml swan --pipeline-name my-model

   # Using local backend (standard rompy)
   rompy run config.yml

Prax Backend
------------

The Prax backend enables cloud-native execution of wave models through Oceanum's Prax pipeline system.

Features
~~~~~~~~

* **Scalable Execution**: Automatic resource allocation based on model requirements
* **Monitoring**: Real-time progress tracking and logging via oceanum prax CLI
* **Result Management**: Automatic output organization and DataMesh registration
* **Fault Tolerance**: Built-in retry mechanisms and error recovery
* **Authentication**: Seamless integration with Oceanum authentication
* **Project Management**: Organize pipelines into projects for better resource management

Configuration
~~~~~~~~~~~~~

The Prax backend requires several configuration parameters:

.. code-block:: python

   from rompy_oceanum import PraxConfig

   prax_config = PraxConfig(
       # Required parameters
       org="your-organization",
       project="your-project",
       stage="dev",  # or "prod"

       # Optional parameters
       description="Wave model run description",
       tags=["wave-modeling", "swan"],
       timeout=3600,  # 1 hour timeout

       # DataMesh configuration
       datamesh_enabled=True,
       datamesh_dataset_name="wave-model-outputs"
   )

   # Use with ModelRun
   result = model_run.pipeline(backend="prax", **prax_config.dict())

Environment Variables
~~~~~~~~~~~~~~~~~~~~~

Common configuration can be set via environment variables:

.. code-block:: bash

   export PRAX_TOKEN="your-authentication-token"
   export PRAX_ORG="your-organization"
   export PRAX_PROJECT="your-project"

Authentication
~~~~~~~~~~~~~~

The Prax backend uses Oceanum's authentication system:

.. code-block:: bash

   # Login via oceanum CLI
   oceanum auth login

   # Or set token directly
   export PRAX_TOKEN="your-token"

Project Management
~~~~~~~~~~~~~~~~~~

Organize your pipelines into projects for better resource management:

.. code-block:: bash

   # Create a project spec file
   cat > my-project.yaml << EOF
   name: wave-modeling
   description: Wave modeling project
   org: your-organization
   stages:
     - name: dev
       description: Development environment
     - name: prod
       description: Production environment
   EOF

   # Create the project
   oceanum rompy projects create my-project.yaml

   # Deploy the default pipeline template
   oceanum rompy pipelines --deploy-default --project-name wave-modeling

   # List projects
   oceanum rompy projects list

Resource Requirements
~~~~~~~~~~~~~~~~~~~~~

Specify computational resources for your models:

.. code-block:: python

   prax_config = PraxConfig(
       # ... other config ...
       resources={
           "cpu": "2000m",      # 2 CPU cores
           "memory": "4Gi",     # 4GB RAM
           "storage": "10Gi"    # 10GB storage
       }
   )

Model-Specific Backends
-----------------------

Different wave models may have optimized backend configurations:

SWAN Backend
~~~~~~~~~~~~

SWAN models benefit from specific optimizations:

.. code-block:: python

   swan_config = PraxConfig(
       model_type="swan",
       resources={
           "cpu": "4000m",
           "memory": "8Gi",
           "storage": "20Gi"
       },
       # SWAN-specific optimizations
       parallel_execution=True,
       mpi_processes=4
   )

WAVEWATCH III Backend
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   ww3_config = PraxConfig(
       model_type="wavewatch3",
       resources={
           "cpu": "8000m",
           "memory": "16Gi",
           "storage": "50Gi"
       },
       # WW3-specific optimizations
       grid_decomposition="auto"
   )

Best Practices
--------------

Backend Selection Guidelines
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Choose your backend based on:

**Use Prax Backend When:**

* Running production forecasts
* Processing large datasets
* Need scalable compute resources
* Require result archival and sharing
* Working in collaborative environments

**Use Local Backend When:**

* Developing and testing configurations
* Working with small test cases
* Have specific local dependencies
* Need immediate interactive access

Performance Optimization
~~~~~~~~~~~~~~~~~~~~~~~~

**Resource Sizing:**

* Start with conservative resource estimates
* Monitor actual usage and adjust
* Consider model grid size and complexity
* Account for input data processing overhead

**Pipeline Naming:**

* Use descriptive, unique pipeline names
* Include model type and purpose
* Follow organizational naming conventions
* Avoid special characters and spaces

Error Handling
~~~~~~~~~~~~~~

**Timeout Configuration:**

.. code-block:: python

   # Set appropriate timeouts based on model complexity
   prax_config = PraxConfig(
       timeout=7200,  # 2 hours for complex models
       retry_attempts=3,
       retry_delay=300  # 5 minutes between retries
   )

**Monitoring:**

.. code-block:: python

   # Monitor pipeline progress
   result = model_run.pipeline(backend="prax", **config)

   # Check status periodically
   while not result.is_complete():
       print(f"Status: {result.status}")
       print(f"Progress: {result.progress}%")
       time.sleep(30)

Advanced Configuration
----------------------

Custom Pipeline Templates
~~~~~~~~~~~~~~~~~~~~~~~~~

Create reusable pipeline configurations:

.. code-block:: python

   # templates/swan_operational.py
   SWAN_OPERATIONAL = PraxConfig(
       resources={"cpu": "4000m", "memory": "8Gi"},
       timeout=3600,
       datamesh_enabled=True,
       tags=["operational", "swan", "forecast"]
   )

   # Use template
   config = SWAN_OPERATIONAL.copy(update={
       "pipeline_name": "daily-forecast",
       "description": "Daily operational wave forecast"
   })

Multi-Stage Pipelines
~~~~~~~~~~~~~~~~~~~~~

Configure pipelines that run across multiple environments:

.. code-block:: python

   # Development stage
   dev_result = model_run.pipeline(
       backend="prax",
       stage="dev",
       pipeline_name="model-development"
   )

   # Promote to production after validation
   if dev_result.is_successful():
       prod_result = model_run.pipeline(
           backend="prax",
           stage="prod",
           pipeline_name="operational-forecast"
       )

Troubleshooting
---------------

Common Issues
~~~~~~~~~~~~~

**Authentication Failures:**

.. code-block:: bash

   # Refresh authentication
   oceanum auth login --refresh

   # Verify token
   oceanum auth status

**Resource Limitations:**

.. code-block:: python

   # Check resource quotas
   from rompy_oceanum.backends import PraxClient

   client = PraxClient()
   quotas = client.get_resource_quotas()
   print(f"Available CPU: {quotas['cpu']}")
   print(f"Available Memory: {quotas['memory']}")

**Pipeline Failures:**

.. code-block:: python

   # Get detailed error information
   if result.has_failed():
       print(f"Error: {result.error_message}")
       print(f"Logs: {result.get_logs()}")

Debug Mode
~~~~~~~~~~

Enable detailed logging for troubleshooting:

.. code-block:: python

   import logging
   logging.getLogger('rompy_oceanum').setLevel(logging.DEBUG)

   # Run with debug output
   result = model_run.pipeline(backend="prax", debug=True, **config)

See Also
--------

* :doc:`basic-usage` - Getting started with rompy-oceanum
* :doc:`configuration` - Environment and authentication setup
* :doc:`troubleshooting` - Debugging common issues
* :doc:`../api/index` - API reference documentation
