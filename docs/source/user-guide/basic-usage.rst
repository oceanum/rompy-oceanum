Basic Usage
===========

This guide covers the fundamental concepts and usage patterns for rompy-oceanum through the oceanum CLI integration. You'll learn how to generate configurations, submit wave models to the Oceanum Prax pipeline, monitor execution, and retrieve results using the unified ``oceanum rompy`` command interface.

Core Concepts
-------------

Oceanum CLI Integration
~~~~~~~~~~~~~~~~~~~~~~~

rompy-oceanum integrates with the oceanum CLI as a plugin, providing:

* **Unified Interface**: All rompy operations available through ``oceanum rompy`` commands
* **Seamless Authentication**: Uses oceanum's built-in authentication system
* **Enhanced User Experience**: Rich terminal output with progress indicators and file organization
* **Template-Based Configuration**: Generate optimized rompy configurations automatically
* **Complete Workflow Support**: From configuration creation to result management

The integration provides both CLI and programmatic interfaces:

.. code-block:: bash

   # CLI workflow
   oceanum auth login
   oceanum rompy init swan --template basic
   oceanum rompy run config.yml swan --pipeline-name my-pipeline
   oceanum rompy status <run-id>
   oceanum rompy sync <run-id> ./outputs

.. code-block:: python

   # Programmatic usage (unchanged)
   model_run = rompy.ModelRun(config=swan_config, output_dir="./outputs")
   result = model_run.pipeline(pipeline_backend="prax", ...)

Prax Pipeline Integration
~~~~~~~~~~~~~~~~~~~~~~~~~

rompy-oceanum provides seamless integration with Oceanum's Prax pipeline system:

* **Remote Execution**: Models run on Oceanum's high-performance computing resources
* **Scalability**: Handle large models and batch processing
* **Monitoring**: Real-time status tracking and log access
* **Integration**: Automatic registration of outputs in DataMesh catalog

Basic Workflow
--------------

A typical rompy-oceanum workflow using the oceanum CLI follows these steps:

1. **Authenticate**: Login to oceanum platform (one-time setup)
2. **Generate Configuration**: Create optimized rompy configuration from templates
3. **Submit Pipeline**: Send model to Prax for remote execution
4. **Monitor Progress**: Track execution status and view logs in real-time
5. **Retrieve Results**: Download organized outputs with metadata

Step 1: Authentication Setup
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

First, authenticate with the oceanum platform:

.. code-block:: bash

   # One-time authentication setup
   oceanum auth login

This provides access to all oceanum services, including Prax. No manual token management is required.

Step 2: Generate Configuration
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Use the ``oceanum rompy init`` command to generate optimized configurations:

.. code-block:: bash

   # Create basic SWAN configuration
   oceanum rompy init swan --template basic --domain "my_domain"

   # Create advanced configuration with validation
   oceanum rompy init schism --template advanced --interactive

   # Create WW3 configuration with custom parameters
   oceanum rompy init ww3 --bbox "-180,-90,180,90" --grid-resolution 0.1

Available templates:
* ``basic``: Essential model physics and standard outputs
* ``advanced``: Additional physics, validation, and diagnostics
* ``research``: Comprehensive analysis and statistics
* ``operational``: Optimized for speed and monitoring

Step 3: Configure Your Model (Alternative)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Alternatively, you can create rompy configurations programmatically:

.. code-block:: python

   import rompy
   from rompy.swan import SwanConfig, SwanGrid, SwanWind
   from datetime import datetime, timedelta

   # Define model grid
   grid = SwanGrid(
       x0=115.0, y0=-35.0,
       dx=0.05, dy=0.05,
       nx=100, ny=80
   )

   # Define wind forcing
   wind = SwanWind(
       speed=10.0,
       direction=270.0,
       time=datetime.now()
   )

   # Create SWAN configuration
   config = SwanConfig(
       grid=grid,
       winds=[wind],
       physics={"whitecapping": True, "breaking": True},
       outputs={"significant_wave_height": True, "mean_wave_period": True}
   )

   # Create ModelRun instance
   model_run = rompy.ModelRun(
       config=config,
       output_dir="./outputs",
       run_id="swan_basic_example"
   )

Step 4: Submit to Prax Pipeline
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Submit your model using the oceanum CLI:

.. code-block:: bash

   # Execute model via Prax pipeline
   oceanum rompy run config.yml swan --pipeline-name my-pipeline

   # Execute with custom options
   oceanum rompy run config.yml swan \
       --pipeline-name swan-research \
       --project wave-forecasting \
       --wait \
       --timeout 3600

For programmatic submission:

.. code-block:: python

   # Submit to Prax pipeline (authentication handled automatically)
   result = model_run.pipeline(
       pipeline_backend="prax",
       pipeline_name="swan-from-rompy"
   )

   print(f"Pipeline submitted successfully!")
   print(f"Run ID: {result.run_id}")
   print(f"Status: {result.get_status()}")

.. note::
   The ``pipeline_name`` must correspond to a pipeline template deployed in your Prax organization.
   Contact your Prax administrator for available pipeline templates.

Step 5: Monitor Execution
~~~~~~~~~~~~~~~~~~~~~~~~~

Monitor execution using the oceanum CLI:

.. code-block:: bash

   # Check current status
   oceanum rompy status <run-id>

   # Monitor with real-time updates
   oceanum rompy status <run-id> --watch

   # View logs in real-time
   oceanum rompy logs <run-id> --follow

For programmatic monitoring:

.. code-block:: python

   # Check current status
   status = result.get_status()
   print(f"Current status: {status}")

   # Wait for completion (with timeout)
   try:
       result.wait_for_completion(timeout=3600)  # 1 hour timeout
       print("Pipeline completed successfully!")
   except TimeoutError:
       print("Pipeline is still running after timeout")

   # Get detailed status information
   detailed_status = result.get_detailed_status()
   print(f"Execution time: {detailed_status.get('execution_time')}")
   print(f"Resource usage: {detailed_status.get('resources')}")

Step 6: Retrieve Results
~~~~~~~~~~~~~~~~~~~~~~~~

Download organized results using the oceanum CLI:

.. code-block:: bash

   # Download all outputs with organization
   oceanum rompy sync <run-id> ./outputs --organize

   # Download specific file types
   oceanum rompy sync <run-id> ./netcdf_data --include "*.nc"

   # Download from specific pipeline stage
   oceanum rompy sync <run-id> ./model_outputs --stage postprocess

For programmatic downloads:

.. code-block:: python

   # Download all outputs
   if result.is_complete() and result.is_successful():
       output_paths = result.download_outputs("./results")
       print(f"Downloaded outputs to: {output_paths}")

       # Access specific output files
       for file_path in output_paths:
           print(f"Output file: {file_path}")

   # Access DataMesh registered datasets (if enabled)
   datasets = result.get_registered_datasets()
   for dataset in datasets:
       print(f"Dataset: {dataset['name']} - {dataset['url']}")

Using the Oceanum CLI Integration
---------------------------------

The oceanum rompy CLI integration provides enhanced commands for all operations:

Complete Workflow Example
~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # 1. Authenticate (one-time setup)
   oceanum auth login

   # 2. Generate optimized configuration
   oceanum rompy init swan --template operational --domain "perth_coast"

   # 3. Execute model
   oceanum rompy run config.yml swan --pipeline-name swan-operational

   # 4. Monitor execution (use run-id from previous command)
   oceanum rompy status <run-id> --watch

   # 5. View logs
   oceanum rompy logs <run-id> --follow

   # 6. Download organized results
   oceanum rompy sync <run-id> ./outputs --organize

Individual Commands
~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Generate configuration from template
   oceanum rompy init swan --template basic --domain "my_domain"

   # Submit pipeline execution
   oceanum rompy run config.yml swan --pipeline-name my-pipeline

   # Check pipeline status
   oceanum rompy status <run-id>

   # Monitor logs in real-time
   oceanum rompy logs <run-id> --follow

   # Download organized outputs
   oceanum rompy sync <run-id> ./outputs --organize

Enhanced Output Organization
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The sync command automatically organizes files:

.. code-block:: bash

   # Organized download creates structured directories
   oceanum rompy sync <run-id> ./outputs --organize

   # Results in structure like:
   # outputs/
   # ├── postprocess/
   # │   ├── netcdf/
   # │   │   └── wave_height.nc
   # │   └── plots/
   # │       └── wave_field.png
   # ├── run/
   # │   └── logs/
   # │       └── model.log
   # └── run_metadata.json

Configuration Patterns
-----------------------

Authentication
~~~~~~~~~~~~~~

Use oceanum's unified authentication system:

.. code-block:: bash

   # Authenticate once (session persists)
   oceanum auth login

   # Check authentication status
   oceanum auth status

   # Logout when needed
   oceanum auth logout

Template-Based Configuration
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Generate configurations using templates:

.. code-block:: bash

   # Basic configuration for operational use
   oceanum rompy init swan --template operational --domain "perth_coast"

   # Research configuration with comprehensive outputs
   oceanum rompy init swan --template research --domain "great_barrier_reef"

   # Interactive configuration setup
   oceanum rompy init schism --template advanced --interactive

   # Custom grid specification
   oceanum rompy init ww3 \
       --template basic \
       --bbox "110,-35,120,-25" \
       --grid-resolution 0.05 \
       --output custom_config.yml

Environment Variables
~~~~~~~~~~~~~~~~~~~~~

Optional environment variables for defaults:

.. code-block:: bash

   export ROMPY_CONFIG="./configs/default.yml"
   export ROMPY_MODEL="swan"
   export PRAX_PROJECT="wave-forecasting"
   export PRAX_STAGE="dev"

Programmatic Configuration
~~~~~~~~~~~~~~~~~~~~~~~~~~

The programmatic interface remains unchanged and benefits from oceanum authentication:

.. code-block:: python

   # No manual token management needed - oceanum handles authentication
   result = model_run.pipeline(
       pipeline_backend="prax",
       pipeline_name="swan-from-rompy",
       project="wave-modeling",
       stage="dev"
   )

Error Handling
--------------

CLI Error Handling
~~~~~~~~~~~~~~~~~~

The oceanum CLI provides clear error messages:

.. code-block:: bash

   # Authentication errors provide helpful guidance
   $ oceanum rompy run config.yml swan --pipeline-name test
   ❌ Authentication error: Invalid or expired token
   💡 Try: oceanum auth login

   # Configuration errors show validation details
   $ oceanum rompy run invalid_config.yml swan --pipeline-name test
   ❌ Configuration error: Invalid grid specification
   🔧 Fix: Check grid parameters in configuration file

   # Pipeline errors include troubleshooting steps
   $ oceanum rompy run config.yml swan --pipeline-name missing-pipeline
   ❌ Pipeline error: Pipeline template 'missing-pipeline' not found
   📋 Available pipelines: swan-operational, swan-research, swan-forecast

Programmatic Error Handling
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from rompy_oceanum.exceptions import PraxError, AuthenticationError

   try:
       # Submit pipeline (authentication handled automatically)
       result = model_run.pipeline(
           pipeline_backend="prax",
           pipeline_name="swan-from-rompy"
       )

       # Wait for completion
       result.wait_for_completion(timeout=3600)

       # Check for success
       if result.is_successful():
           outputs = result.download_outputs("./results")
           print(f"Pipeline completed: {outputs}")
       else:
           print(f"Pipeline failed: {result.get_error_message()}")

   except AuthenticationError as e:
       print(f"Authentication failed: {e}")
       print("Run 'oceanum auth login' to authenticate")

   except PraxError as e:
       print(f"Prax API error: {e}")
       print("Check network connection and service status")

   except TimeoutError:
       print("Pipeline execution timed out")
       print(f"Current status: {result.get_status()}")

Best Practices
--------------

Configuration Management
~~~~~~~~~~~~~~~~~~~~~~~~

* **Use template-based generation** instead of manual configuration
* **Version control** generated configurations for reproducibility
* **Use meaningful domain names** for organization and tracking
* **Validate configurations** before submission

Authentication and Security
~~~~~~~~~~~~~~~~~~~~~~~~~~~

* **Use oceanum auth login** instead of manual token management
* **Check authentication status** before automated workflows
* **Logout when switching between accounts** or organizations
* **Keep authentication sessions active** for continuous operations

Pipeline Management
~~~~~~~~~~~~~~~~~~~

* **Set appropriate timeouts** for model complexity
* **Use descriptive pipeline names** that match your workflow
* **Monitor execution** with real-time status and logs
* **Implement retry logic** for transient failures

Output Management
~~~~~~~~~~~~~~~~~

* **Use organized downloads** to maintain file structure automatically
* **Download outputs promptly** to avoid storage limits
* **Include metadata files** for provenance tracking
* **Clean up local files** when no longer needed

Workflow Automation
~~~~~~~~~~~~~~~~~~~

* **Check authentication status** before starting batch operations
* **Use meaningful file organization** for output management
* **Implement proper error handling** with clear recovery paths
* **Monitor long-running operations** with watch modes

Common Patterns
---------------

Automated Workflow Script
~~~~~~~~~~~~~~~~~~~~~~~~~~

Complete workflow automation using the oceanum CLI:

.. code-block:: bash

   #!/bin/bash
   # automated_modeling.sh

   set -e  # Exit on error

   DOMAIN="perth_coast"
   MODEL="swan"
   TEMPLATE="operational"
   PIPELINE="swan-operational"
   OUTPUT_DIR="./results/$(date +%Y%m%d_%H%M%S)"

   echo "🚀 Starting automated modeling workflow"

   # Ensure authentication
   if ! oceanum auth status &>/dev/null; then
       echo "❌ Not authenticated. Please run: oceanum auth login"
       exit 1
   fi

   # Generate configuration
   echo "📝 Generating ${MODEL} configuration..."
   oceanum rompy init ${MODEL} --template ${TEMPLATE} --domain ${DOMAIN}

   # Execute model
   echo "🎯 Executing model..."
   RUN_OUTPUT=$(oceanum rompy run config.yml ${MODEL} --pipeline-name ${PIPELINE} --wait)
   RUN_ID=$(echo "$RUN_OUTPUT" | grep "🆔 Prax run ID:" | cut -d' ' -f4)

   # Download results
   echo "📁 Downloading results..."
   mkdir -p ${OUTPUT_DIR}
   oceanum rompy sync ${RUN_ID} ${OUTPUT_DIR} --organize

   echo "🎉 Workflow completed successfully!"

Batch Processing with CLI
~~~~~~~~~~~~~~~~~~~~~~~~~

Process multiple configurations:

.. code-block:: bash

   #!/bin/bash
   # batch_modeling.sh

   DOMAINS=("perth" "sydney" "melbourne")
   PIPELINE="swan-operational"

   for domain in "${DOMAINS[@]}"; do
       echo "🔄 Processing domain: ${domain}"

       # Generate configuration
       oceanum rompy init swan --template operational --domain "${domain}" --output "${domain}_config.yml"

       # Submit pipeline
       oceanum rompy run "${domain}_config.yml" swan --pipeline-name ${PIPELINE} &
   done

   # Wait for all background jobs
   wait
   echo "✅ All models submitted"

Programmatic Batch Processing
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Process multiple configurations programmatically:

.. code-block:: python

   import subprocess
   from pathlib import Path

   def run_model_batch(domains, model="swan", template="operational"):
       """Run batch modeling for multiple domains."""
       results = []

       for domain in domains:
           # Generate configuration
           config_file = f"{domain}_config.yml"
           subprocess.run([
               "oceanum", "rompy", "init", model,
               "--template", template,
               "--domain", domain,
               "--output", config_file
           ], check=True)

           # Submit pipeline
           result = subprocess.run([
               "oceanum", "rompy", "run", config_file, model,
               "--pipeline-name", f"{model}-operational"
           ], capture_output=True, text=True, check=True)

           # Extract run ID
           for line in result.stdout.split('\n'):
               if '🆔 Prax run ID:' in line:
                   run_id = line.split()[-1]
                   results.append((domain, run_id))
                   break

       return results

   # Run batch
   domains = ["perth_coast", "sydney_harbor", "melbourne_bay"]
   batch_results = run_model_batch(domains)

   # Monitor all executions
   for domain, run_id in batch_results:
       print(f"Domain {domain}: {run_id}")
       # Use oceanum rompy status <run_id> --watch to monitor

Next Steps
----------

Now that you understand the oceanum CLI integration:

* Review the :doc:`cli-reference` for complete command documentation
* Explore :doc:`configuration` for advanced template and model options
* Try the :doc:`../examples/swan-workflow` for a comprehensive example
* Learn about automation patterns in the CLI reference scripting section

For troubleshooting common issues, see :doc:`troubleshooting`.
