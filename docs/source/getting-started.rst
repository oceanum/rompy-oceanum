Getting Started
===============

This guide will help you get started with rompy-oceanum quickly and efficiently.

Prerequisites
-------------

Before installing rompy-oceanum, ensure you have:

* Python 3.8 or higher
* Access to Oceanum platform (for authentication and remote execution)
* Basic familiarity with rompy wave modeling framework
* oceanum CLI installed and configured

Installation
------------

Install rompy-oceanum and oceanum CLI using pip:

.. code-block:: bash

   pip install rompy-oceanum oceanum

Verify the integration works:

.. code-block:: bash

   oceanum rompy --help

For development installation:

.. code-block:: bash

   git clone https://github.com/rom-py/rompy-oceanum
   cd rompy-oceanum
   pip install -e ".[dev,docs]"
   pip install oceanum

Authentication Setup
--------------------

rompy-oceanum uses oceanum's built-in authentication system. Set up authentication once:

.. code-block:: bash

   # Login to oceanum platform
   oceanum auth login

This will authenticate you with all oceanum services, including Prax. No manual token management is required.

.. tip::
   The authentication session persists across terminal sessions. You only need to login once
   or when your session expires.

Quick Start Example
-------------------

Here's a minimal example using the oceanum CLI integration:

.. code-block:: bash

   # 1. Authenticate with oceanum
   oceanum auth login

   # 2. Deploy default SWAN pipeline
   oceanum rompy create pipeline 

   # 3. Create optimized rompy configuration
   oceanum rompy init swan --template basic --domain "my_domain"

   # 4. Execute model via Prax pipeline (and follow logs)
   oceanum rompy run rompy_config_swan_basic.yml swan --pipeline-name swan-from-rompy --project rompy-oceanum --follow

   # 5. Check for dataset registration in datamesh
   oceanum datamesh list datasources --search "rompy"

For programmatic usage:

.. code-block:: python

   import rompy
   from rompy.swan import SwanConfig

   # Create a basic SWAN configuration
   config = SwanConfig(
       # Your SWAN model configuration here
       # See rompy documentation for details
   )

   # Create a ModelRun instance
   model_run = rompy.ModelRun(
       config=config,
       output_dir="./outputs"
   )

   # Execute using Prax pipeline backend
   result = model_run.pipeline(
       pipeline_backend="prax",
       pipeline_name="swan-from-rompy"
   )

   print(f"Pipeline submitted with Run ID: {result.run_id}")

Using the CLI
-------------

rompy-oceanum is integrated with the oceanum CLI as the ``oceanum rompy`` command group:

.. code-block:: bash

   # Create optimized configuration templates
   oceanum rompy init swan --template basic --domain "my_domain"

   # Submit a pipeline from a rompy configuration file
   oceanum rompy run config.yml swan --pipeline-name my-pipeline

   # Check pipeline status
   oceanum rompy status <run-id>

   # View pipeline logs with filtering
   oceanum rompy logs <run-id> --follow

   # Download organized pipeline outputs
   oceanum rompy sync <run-id> ./outputs --organize

Monitoring Your Pipeline
------------------------

Once submitted, you can monitor your pipeline execution:

.. code-block:: python

   # Check status
   status = result.get_status()
   print(f"Pipeline status: {status}")

   # Wait for completion
   result.wait_for_completion(timeout=3600)  # 1 hour timeout

   # Download outputs when complete
   if result.is_complete():
       outputs = result.download_outputs("./outputs")
       print(f"Downloaded outputs to: {outputs}")

Configuration Options
---------------------

rompy-oceanum leverages oceanum's configuration system and supports:

1. **Oceanum Authentication** (via ``oceanum auth login``)
2. **Template-based Configuration** (via ``oceanum rompy init``)
3. **Command-line Parameters** (for pipeline execution)
4. **Programmatic Configuration** (for advanced usage)

Generate optimized configuration templates:

.. code-block:: bash

   # Basic SWAN configuration
   oceanum rompy init swan --template basic --domain "my_domain"

   # Advanced configuration with validation
   oceanum rompy init schism --template advanced --interactive

   # WaveWatch III configuration
   oceanum rompy init ww3 --bbox "-180,-90,180,90" --grid-resolution 0.1

Available template types:
* ``basic``: Essential model physics and standard outputs
* ``advanced``: Additional physics, validation, and diagnostics
* ``research``: Comprehensive analysis and statistics
* ``operational``: Optimized for speed and monitoring

Common Workflow
---------------

A typical rompy-oceanum workflow using the oceanum CLI:

1. **Authentication**: Login to oceanum platform once
2. **Configuration**: Generate optimized rompy configuration from templates
3. **Execution**: Submit model to Prax for remote execution
4. **Monitoring**: Track pipeline progress and view logs
5. **Result Management**: Download organized outputs and metadata

**Workflow Steps:**

::

   oceanum auth login ──► oceanum rompy init ──► oceanum rompy run
                                                        │
                                                        ▼
   oceanum rompy sync ◄── oceanum rompy logs ◄── oceanum rompy status

**Complete Example:**

.. code-block:: bash

   # One-time authentication setup
   oceanum auth login

   # Create optimized configuration
   oceanum rompy init swan --template basic --domain "perth_coast"

   # Execute model
   oceanum rompy run config.yml swan --pipeline-name swan-operational

   # Monitor execution (get run-id from previous command)
   oceanum rompy status <run-id>
   oceanum rompy logs <run-id> --follow

   # Download organized results
   oceanum rompy sync <run-id> ./outputs --organize

Next Steps
----------

Now that you have rompy-oceanum up and running:

* Read the :doc:`user-guide/basic-usage` for detailed usage patterns
* Explore :doc:`examples/swan-workflow` for a complete SWAN modeling example
* Check the :doc:`user-guide/configuration` guide for advanced configuration options
* Review the :doc:`api/index` for complete API documentation

Troubleshooting
---------------

If you encounter issues:

1. **Authentication Errors**: Run ``oceanum auth login`` to refresh your session
2. **Plugin Loading Issues**: Ensure oceanum CLI can find the plugin with ``oceanum rompy --help``
3. **Pipeline Failures**: Check logs using ``oceanum rompy logs <run-id> --follow``
4. **Network Issues**: Ensure you have internet connectivity and access to Oceanum services
5. **Configuration Problems**: Use ``oceanum rompy init`` to generate valid templates

Common solutions:

.. code-block:: bash

   # Refresh authentication
   oceanum auth logout
   oceanum auth login

   # Verify plugin integration
   oceanum rompy --help

   # Test with basic configuration
   oceanum rompy init swan --template basic --domain "test"

For more detailed troubleshooting, see :doc:`user-guide/troubleshooting`.

Getting Help
------------

* `GitHub Issues <https://github.com/rom-py/rompy-oceanum/issues>`_ - Report bugs or request features
* `rompy Documentation <https://rompy.readthedocs.io/>`_ - Learn about the underlying framework
* `Oceanum Platform <https://oceanum.science/>`_ - Platform documentation and support
