CLI Reference
=============

This guide provides comprehensive documentation for the rompy-oceanum integration with the oceanum CLI. The integration is available as the ``oceanum rompy`` command group, providing seamless ocean model execution through the Oceanum Prax platform.

Overview
--------

The oceanum rompy CLI integration provides the following capabilities:

* **Configuration Management**: Generate optimized rompy configurations from templates
* **Project Management**: Create and manage Prax projects for rompy pipelines
* **Pipeline Management**: Create, list, get, update, and delete pipeline templates
* **Pipeline Execution**: Submit models to Prax for remote execution with enhanced monitoring
* **Status Monitoring**: Real-time pipeline status tracking with rich terminal output
* **Log Management**: View and filter pipeline logs with rompy-specific enhancements
* **Result Management**: Download and organize pipeline outputs automatically
* **Authentication Integration**: Seamless integration with oceanum's unified authentication

Installation and Setup
----------------------

The CLI is installed automatically with rompy-oceanum and oceanum:

.. code-block:: bash

   pip install rompy-oceanum oceanum

Verify installation:

.. code-block:: bash

   oceanum rompy --help

Authentication:

.. code-block:: bash

   oceanum auth login

Global Options
--------------

The oceanum rompy commands inherit global options from the oceanum CLI:

.. code-block:: bash

   oceanum [GLOBAL_OPTIONS] rompy COMMAND [COMMAND_OPTIONS]

**Global Options:**

* ``--help``: Show help message and exit
* ``--version``: Show oceanum CLI version information
* ``--verbose, -v``: Enable verbose output
* ``--quiet, -q``: Suppress non-essential output

Commands Reference
------------------

init
~~~~

Generate optimized rompy configuration files from templates.

**Syntax:**

.. code-block:: bash

   oceanum rompy init MODEL [OPTIONS]

**Required Arguments:**

* ``MODEL``: Model type (``swan``, ``schism``, ``ww3``)

**Options:**

* ``--template {basic,advanced,research,operational}``: Configuration template type (default: basic)
* ``--domain TEXT``: Domain identifier for the configuration
* ``--bbox TEXT``: Bounding box as "west,south,east,north" coordinates
* ``--grid-resolution FLOAT``: Grid resolution for spatial discretization
* ``--output PATH``: Output configuration file path (default: config.yml)
* ``--interactive``: Interactive configuration setup
* ``--overwrite``: Overwrite existing configuration file

**Template Types:**

* ``basic``: Essential model physics and standard outputs
* ``advanced``: Additional physics, validation, and diagnostics
* ``research``: Comprehensive analysis and statistics
* ``operational``: Optimized for speed and monitoring

**Examples:**

.. code-block:: bash

   # Create basic SWAN configuration
   oceanum rompy init swan --template basic --domain "perth_coast"

   # Create advanced SCHISM configuration interactively
   oceanum rompy init schism --template advanced --interactive

   # Create WW3 configuration with custom grid
   oceanum rompy init ww3 \
       --template operational \
       --bbox "110,-35,120,-25" \
       --grid-resolution 0.05 \
       --output ww3_config.yml

   # Create research configuration with custom domain
   oceanum rompy init swan \
       --template research \
       --domain "great_barrier_reef" \
       --output research_config.yml

**Complete Workflow:**

.. code-block:: bash

   # 1. Create a project for your pipelines
   oceanum rompy create project my-project.yaml

   # 2. Deploy the default pipeline template
   oceanum rompy create pipeline --project my-project

   # 3. Generate configuration
   oceanum rompy init swan --template operational --domain "perth_coast"

   # 4. Execute model
   oceanum rompy run config.yml swan --pipeline-name swan-from-rompy --project my-project

run
~~~

Initialize rompy configurations for Oceanum Prax pipeline execution or run locally with Docker.

**Syntax:**

.. code-block:: bash

   oceanum rompy run CONFIG MODEL [OPTIONS]

**Required Arguments:**

* ``CONFIG``: Path to rompy configuration file
* ``MODEL``: Model type (``swan``, ``schism``, ``ww3``)

**Required Options (when not using --local):**

* ``--pipeline-name TEXT``: Name of the Prax pipeline template

**Optional Options:**

* ``--project TEXT``: Prax project name (overrides oceanum context)
* ``--stage {dev,prod}``: Deployment stage (default: dev)
* ``--wait/--no-wait``: Wait for pipeline completion (default: --no-wait)
* ``--timeout INTEGER``: Execution timeout in seconds
* ``--local``: Run the model locally using Docker instead of submitting to Prax
* ``--follow``: Stream logs in real time after submission (mutually exclusive with ``--watch``)
* ``--watch``: Watch and print pipeline task statuses in a live-updating table after submission (mutually exclusive with ``--follow``)

**Examples:**

.. code-block:: bash

   # Basic execution
   oceanum rompy run config.yml swan --pipeline-name swan-operational

   # Execute with custom project and wait for completion
   oceanum rompy run config.yml swan \
       --pipeline-name swan-research \
       --project wave-forecasting \
       --wait \
       --timeout 3600

   # Execute in production
   oceanum rompy run config.yml schism \
       --pipeline-name schism-operational \
       --stage prod

   # Run locally with Docker
   oceanum rompy run config.yml swan --local

**Log Streaming and Task Monitoring:**

* ``--follow``:
  Stream logs in real time after submission. The CLI will display live log output from the pipeline as soon as it becomes available, matching the behavior of the official Prax CLI. This is useful for debugging and monitoring detailed model execution.

* ``--watch``:
  Watch and print pipeline task statuses in a live-updating table after submission. The CLI will show a table of logical pipeline tasks (such as ``generate``, ``run``, ``register``) and their current status (e.g., Pending, Running, Succeeded, Failed). This provides a high-level overview of pipeline progress without streaming all logs.

.. note::
   ``--follow`` and ``--watch`` are mutually exclusive. Only one may be used at a time.

**Output Examples:**

*With ``--follow``:*

.. code-block:: text

   📋 Pipeline logs (streaming):
   2025-08-01 14:16:22 [INFO] rompy.swan.config   : ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   2025-08-01 14:16:23 [INFO] rompy.swan.config   : Model configuration generated.
   ...

*With ``--watch``:*

.. code-block:: text

   👀 Watching tasks for latest run of pipeline swan-from-rompy (matches official client):

   ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
   ┃ Pipeline Run: pipeline-swan-from-rompy-d891-dev-8tcrc       ┃
   ┡━━━━━━━━━━━━━━━┯━━━━━━━━━━━━━━┯━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
   │ Task          │ Status       │ Message                      │
   ├───────────────┼──────────────┼──────────────────────────────┤
   │ generate      │ Succeeded    │                              │
   │ run           │ Running      │                              │
   │ register      │ Pending      │                              │
   └───────────────┴──────────────┴──────────────────────────────┘

   ✅ Pipeline run completed. Final task statuses above.

**Local Execution:**

When using the ``--local`` option, the model is run locally using Docker:

.. code-block:: text

   🔄 Processing rompy configuration...
   ✅ ModelRun created successfully: perth_coast_swan_basic
   🔄 Running model locally with Docker...
   🐳 Using Docker image: us-central1-docker.pkg.dev/oceanum-prod/oceanum-public/swan:latest
   🔄 Generating model configuration...
   📁 Staging directory: /tmp/rompy/perth_coast_swan_basic
   🚀 Running model locally with Docker...
   ✅ Model run completed successfully!
   📁 Results are in: /tmp/rompy/perth_coast_swan_basic

**Project Workflow:**

Before running pipelines, you need to create a project and deploy a pipeline template:

.. code-block:: bash

   # Create a project for your pipelines
   oceanum rompy create project my-project.yaml

   # Deploy the default pipeline template
   oceanum rompy create pipeline --project my-project

   # Execute model
   oceanum rompy run config.yml swan --pipeline-name swan-from-rompy --project my-project


status
~~~~~~

Monitor pipeline execution status with real-time updates using the oceanum prax CLI.

**Syntax:**

.. code-block:: bash

   oceanum prax --project PROJECT logs pipeline-runs RUN_ID [OPTIONS]

**Required Arguments:**

* ``PROJECT``: Prax project name
* ``RUN_ID``: Prax run identifier

**Options:**

* ``--follow, -f``: Follow log output in real-time
* ``--tail INTEGER``: Show last N lines (default: 100)

**Examples:**

.. code-block:: bash

   # Check current status
   oceanum prax --project wave-forecasting describe pipeline-runs pipeline-swan-operational-run-id-dev-xyz123

   # Monitor status with real-time updates
   oceanum prax --project wave-forecasting logs pipeline-runs pipeline-swan-operational-run-id-dev-xyz123 -f

**Output Examples:**

Basic status output:

.. code-block:: text

   NAME: pipeline-swan-operational-run-id-dev-xyz123
   STATUS: Running
   STARTED: 2024-01-15T10:30:45Z
   DURATION: 15m23s
   PROGRESS: Stage 2/4 (Executing model)

Watch mode output:

.. code-block:: text

   NAME: pipeline-swan-operational-run-id-dev-xyz123
   STATUS: Running → Completed
   STARTED: 2024-01-15T10:30:45Z
   DURATION: 23m15s
   OUTPUTS: 15 files

logs
~~~~

View and filter pipeline execution logs using the oceanum prax CLI.

**Syntax:**

.. code-block:: bash

   oceanum prax --project PROJECT logs pipeline-runs RUN_ID [OPTIONS]

**Required Arguments:**

* ``PROJECT``: Prax project name
* ``RUN_ID``: Prax run identifier

**Options:**

* ``--follow, -f``: Follow log output in real-time
* ``--tail INTEGER``: Show last N lines (default: 100)
* ``--since TEXT``: Show logs since timestamp (ISO format)

**Examples:**

.. code-block:: bash

   # View recent logs
   oceanum prax --project wave-forecasting logs pipeline-runs pipeline-swan-operational-run-id-dev-xyz123

   # Follow logs in real-time
   oceanum prax --project wave-forecasting logs pipeline-runs pipeline-swan-operational-run-id-dev-xyz123 -f

   # Show logs since specific time
   oceanum prax --project wave-forecasting logs pipeline-runs pipeline-swan-operational-run-id-dev-xyz123 \
       --since "2024-01-15T10:30:00Z"

**Output:**

Logs are displayed with timestamps:

.. code-block:: text

   NAME: pipeline-swan-operational-run-id-dev-xyz123
   STATUS: Running
   STARTED: 2024-01-15T10:30:45Z
   DURATION: 15m23s
   OUTPUTS: 15 files

   2024-01-15T10:30:45Z [INFO] Starting SWAN model execution
   2024-01-15T10:30:46Z [INFO] Grid: 100x80, Resolution: 0.05°
   2024-01-15T10:31:15Z [INFO] Model initialization complete
   2024-01-15T10:31:16Z [INFO] Processing wave conditions...
   2024-01-15T10:35:22Z [WARN] High wave heights detected in domain
   2024-01-15T10:42:18Z [INFO] Model execution completed successfully

projects
~~~~~~~~

Manage Prax projects for rompy pipelines.

**Syntax:**

.. code-block:: bash

   oceanum rompy [OPTIONS] {create|list|describe|delete} project [ARGS]...

**Commands:**

* ``create SPEC_FILE``: Create a new project from a spec file
* ``list``: List all projects accessible to the user
* ``describe PROJECT_NAME``: Describe a project
* ``delete PROJECT_NAME``: Delete a project

**Options for all commands:**

* ``--org TEXT``: Prax organization name (overrides oceanum context)
* ``--user TEXT``: Prax user email (overrides oceanum context)

**Examples:**

.. code-block:: bash

   # Create a new project
   oceanum rompy create project my-project.yaml

   # List all projects
   oceanum rompy list projects

   # Describe a project
   oceanum rompy describe project my-project

   # Delete a project
   oceanum rompy delete project my-project


pipelines
~~~~~~~~~

Manage pipeline templates and deployments for rompy execution.

**Syntax:**

.. code-block:: bash

   oceanum rompy [OPTIONS] {create|list|describe|delete} pipeline [ARGS]...

**Commands:**

* ``create [TEMPLATE_FILE]``: Create/deploy a pipeline template to a project. If TEMPLATE_FILE is omitted, deploys the default SWAN pipeline template.
* ``list``: List pipelines in a project
* ``describe PIPELINE_NAME``: Describe a pipeline
* ``delete PIPELINE_NAME``: Delete a pipeline from a project

**Options for all commands:**

* ``--project TEXT``: Prax project name (default: rompy-pipelines)
* ``--org TEXT``: Prax organization name (overrides oceanum context)
* ``--user TEXT``: Prax user email (overrides oceanum context)
* ``--stage TEXT``: Prax stage name (default: dev)
* ``--name TEXT``: Resource name (defaults to filename without extension)

**Examples:**

.. code-block:: bash

   # Deploy the default pipeline template
   oceanum rompy create pipeline --project rompy-oceanum

   # Create a pipeline from a template
   oceanum rompy create pipeline my-pipeline.yaml --project rompy-oceanum

   # List all pipelines in a project
   oceanum rompy list pipelines --project rompy-oceanum

   # Describe a pipeline
   oceanum rompy describe pipeline my-pipeline --project rompy-oceanum

   # Delete a pipeline
   oceanum rompy delete pipeline my-pipeline --project rompy-oceanum


Output Formats
--------------

JSON Output
~~~~~~~~~~~

Several commands support JSON output for programmatic use:

.. code-block:: bash

   # Get status as JSON
   oceanum rompy status <run-id> --json

Example JSON output:

.. code-block:: json

   {
     "run_id": "prax-perth_coast_swan_basic",
     "status": "COMPLETED",
     "pipeline": "swan-operational",
     "model": "swan",
     "user": "researcher",
     "org": "oceanum",
     "project": "wave-forecasting",
     "stage": "dev",
     "created_at": "2024-01-15T10:30:45Z",
     "completed_at": "2024-01-15T10:53:58Z",
     "execution_time": "0:23:13",
     "outputs": {
       "count": 15,
       "total_size": "245.7 MB",
       "stages": ["postprocess", "run"]
     },
     "metadata": {
       "domain": "perth_coast",
       "grid_resolution": 0.05,
       "template": "basic"
     }
   }

Environment Variables
---------------------

The oceanum rompy commands use oceanum's authentication system and don't require manual environment variable configuration. Authentication is handled via:

.. code-block:: bash

   oceanum auth login

However, some optional environment variables can be used:

* ``ROMPY_CONFIG``: Default configuration file path
* ``ROMPY_MODEL``: Default model type
* ``PRAX_PROJECT``: Default project name
* ``PRAX_STAGE``: Default deployment stage

Exit Codes
----------

All commands return standard exit codes:

* ``0``: Success
* ``1``: General error (authentication, network, validation)
* ``2``: Command usage error (missing arguments, invalid options)
* ``3``: Pipeline execution error
* ``4``: File operation error (download, upload, organization)

Scripting and Automation
-------------------------

The oceanum rompy CLI is designed for automation and scripting. Here are common patterns:

Bash Script Example
~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   #!/bin/bash
   # automated_modeling.sh - Automated rompy modeling workflow

   set -e  # Exit on any error

   # Configuration
   DOMAIN="perth_coast"
   MODEL="swan"
   TEMPLATE="operational"
   PIPELINE="swan-from-rompy"
   PROJECT="wave-forecasting"
   OUTPUT_DIR="./results/$(date +%Y%m%d_%H%M%S)"

   # Ensure authentication
   if ! oceanum auth status &>/dev/null; then
       echo "❌ Not authenticated. Please run: oceanum auth login"
       exit 1
   fi

   echo "🚀 Starting automated modeling workflow"

   # Create project if needed
   echo "🏗️  Creating project (if needed)..."
   oceanum rompy create project ${PROJECT}.yaml || echo "Project may already exist"

   # Deploy the default pipeline template
   echo "🔧 Deploying default pipeline template..."
   oceanum rompy create pipeline --project ${PROJECT} || echo "Pipeline may already be deployed"

   # Generate configuration
   echo "📝 Generating ${MODEL} configuration..."
   oceanum rompy init ${MODEL} \
       --template ${TEMPLATE} \
       --domain ${DOMAIN} \
       --output config.yml

   # Execute model
   echo "🎯 Executing ${MODEL} model via Prax..."
   RUN_OUTPUT=$(oceanum rompy run config.yml ${MODEL} \
       --pipeline-name ${PIPELINE} \
       --project ${PROJECT} \
       --wait \
       --timeout 3600)

   # Extract run ID from output
   RUN_ID=$(echo "$RUN_OUTPUT" | grep "🆔 Prax run ID:" | cut -d' ' -f4)

   if [ -z "$RUN_ID" ]; then
       echo "❌ Failed to get run ID"
       exit 1
   fi

   echo "✅ Model execution completed: $RUN_ID"

   # Download results
   echo "📁 Downloading results..."
   mkdir -p ${OUTPUT_DIR}
   oceanum rompy sync ${RUN_ID} ${OUTPUT_DIR} --organize

   echo "🎉 Workflow completed successfully!"
   echo "📂 Results available in: ${OUTPUT_DIR}"

Python Script Example
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   #!/usr/bin/env python3
   """automated_modeling.py - Automated rompy modeling with Python"""

   import subprocess
   import json
   import sys
   from pathlib import Path
   from datetime import datetime

   def run_command(cmd, capture_output=True):
       """Run shell command and return result."""
       try:
           result = subprocess.run(
               cmd, shell=True, capture_output=capture_output,
               text=True, check=True
           )
           return result.stdout.strip() if capture_output else None
       except subprocess.CalledProcessError as e:
           print(f"❌ Command failed: {cmd}")
           print(f"Error: {e.stderr}")
           sys.exit(1)

   def submit_pipeline(config_file, model, pipeline_name, project):
       """Submit pipeline and return run ID."""
       cmd = f"oceanum rompy run {config_file} {model} --pipeline-name {pipeline_name} --project {project} --wait"
       output = run_command(cmd)

       # Extract run ID from output
       for line in output.split('\n'):
           if '🆔 Prax run ID:' in line:
               return line.split()[-1]

       raise ValueError("Could not extract run ID from output")

   def wait_for_completion(run_id, project, timeout=3600):
       """Wait for pipeline completion."""
       import time
       start_time = time.time()

       while time.time() - start_time < timeout:
           # Using oceanum prax command to check status
           cmd = f"oceanum prax --project {project} describe pipeline-runs {run_id} --output json"
           try:
               status_json = run_command(cmd)
               status_data = json.loads(status_json)

               # Extract status - this might vary based on actual API response
               current_status = status_data.get('status', 'UNKNOWN')
               print(f"🔄 Status: {current_status}")

               if current_status.upper() in ['COMPLETED', 'SUCCEEDED']:
                   print("✅ Pipeline completed successfully!")
                   return True
               elif current_status.upper() in ['FAILED', 'ERROR']:
                   print("❌ Pipeline execution failed!")
                   return False
           except Exception as e:
               print(f"⚠️  Status check failed: {e}")

           time.sleep(30)  # Check every 30 seconds

       print("⏰ Pipeline execution timed out!")
       return False

   def main():
       """Main execution workflow."""
       # Configuration
       domain = "perth_coast"
       model = "swan"
       template = "operational"
       pipeline = "swan-from-rompy"
       project = "wave-forecasting"

       timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
       output_dir = Path(f"./results/{timestamp}")

       print("🚀 Starting automated modeling workflow")

       # Check authentication
       try:
           run_command("oceanum auth status")
       except:
           print("❌ Not authenticated. Please run: oceanum auth login")
           sys.exit(1)

       # Create project if needed
       print("🏗️  Creating project (if needed)...")
       try:
           run_command(f"oceanum rompy create project {project}.yaml")
       except:
           print("Project may already exist or creation failed")

       # Deploy the default pipeline template
       print("🔧 Deploying default pipeline template...")
       try:
           run_command("oceanum rompy create pipeline --project rompy-oceanum")
       except:
           print("Pipeline may already be deployed")

       # Generate configuration
       print(f"📝 Generating {model} configuration...")
       run_command(f"oceanum rompy init {model} --template {template} --domain {domain}")

       # Submit pipeline
       print(f"🎯 Executing {model} model via Prax...")
       run_id = submit_pipeline("config.yml", model, pipeline, project)
       print(f"📋 Run ID: {run_id}")

       # Wait for completion (using oceanum prax commands)
       print("⏳ Waiting for pipeline completion...")
       if not wait_for_completion(run_id, project):
           sys.exit(1)

       # Download results
       print("📁 Downloading results...")
       output_dir.mkdir(parents=True, exist_ok=True)
       run_command(f"oceanum rompy sync {run_id} {output_dir} --organize")

       print("🎉 Workflow completed successfully!")
       print(f"📂 Results available in: {output_dir}")

   if __name__ == "__main__":
       main()

Troubleshooting
---------------

Common Issues
~~~~~~~~~~~~~

**Plugin Not Found**

If ``oceanum rompy`` commands are not available:

.. code-block:: bash

   # Verify oceanum CLI installation
   oceanum --version

   # Reinstall rompy-oceanum to ensure plugin registration
   pip install --force-reinstall rompy-oceanum

   # Check if plugin is loaded
   oceanum --help  # Should show 'rompy' in command list

**Authentication Errors**

If you get authentication errors:

.. code-block:: bash

   # Check authentication status
   oceanum auth status

   # Re-authenticate if needed
   oceanum auth logout
   oceanum auth login

   # Verify access to required services
   oceanum auth status --verbose

**Pipeline Execution Failures**

If pipeline execution fails:

.. code-block:: bash

   # Check detailed logs
   oceanum rompy logs <run-id> --level ERROR

   # Verify configuration file
   python -c "import yaml; yaml.safe_load(open('config.yml'))"

   # Check pipeline template availability
   oceanum rompy list pipelines --project my-project

   # Check project exists
   oceanum rompy list projects

   # Deploy default pipeline template if needed
   oceanum rompy create pipeline --project rompy-oceanum

**Download Issues**

If file downloads fail:

.. code-block:: bash

   # Check available outputs
   oceanum rompy status <run-id> --detailed

   # Try downloading specific files
   oceanum rompy sync <run-id> ./outputs --include "*.nc" --verify

   # Check disk space and permissions
   df -h
   ls -la ./outputs

Debug Mode
~~~~~~~~~~

Enable verbose output for troubleshooting:

.. code-block:: bash

   # Use oceanum's verbose flag
   oceanum --verbose rompy run config.yml swan --pipeline-name test

   # Check oceanum CLI debug information
   oceanum --help

   # Verify plugin loading
   python -c "from rompy_oceanum.cli.main import main; print('Plugin loaded successfully')"

Getting Help
~~~~~~~~~~~~

* Use ``--help`` with any command for detailed usage information
* Check the `GitHub Issues <https://github.com/rom-py/rompy-oceanum/issues>`_ for known issues
* Review the oceanum CLI documentation for platform-specific issues
* Contact support through the oceanum platform for authentication or service issues

Best Practices
--------------

**Configuration Management**

* Use version control for configuration files
* Generate configurations from templates rather than manual editing
* Validate configurations before submission
* Use meaningful domain names for organization

**Pipeline Execution**

* Set appropriate timeouts for your model complexity
* Use descriptive pipeline names for easier tracking
* Monitor resource usage and optimize configurations
* Implement retry logic for transient failures

**Output Management**

* Download outputs promptly to avoid storage limits
* Use organized downloads to maintain file structure
* Include metadata for provenance tracking
* Clean up local files when no longer needed

**Automation**

* Check authentication status before starting workflows
* Implement proper error handling and logging
* Use JSON output for programmatic processing
* Set up monitoring for long-running batch operations

Next Steps
----------

After mastering the CLI:

* Explore :doc:`basic-usage` for programmatic integration
* Learn about :doc:`configuration` for advanced model setup
* Try :doc:`../examples/swan-workflow` for complete workflows
* Review :doc:`troubleshooting` for common issues and solutions
