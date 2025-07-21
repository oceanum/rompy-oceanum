CLI Reference
=============

This guide provides comprehensive documentation for the rompy-oceanum integration with the oceanum CLI. The integration is available as the ``oceanum rompy`` command group, providing seamless ocean model execution through the Oceanum Prax platform.

Overview
--------

The oceanum rompy CLI integration provides the following capabilities:

* **Configuration Management**: Generate optimized rompy configurations from templates
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

run
~~~

Execute rompy configurations via Oceanum Prax pipeline.

**Syntax:**

.. code-block:: bash

   oceanum rompy run CONFIG MODEL [OPTIONS]

**Required Arguments:**

* ``CONFIG``: Path to rompy configuration file
* ``MODEL``: Model type (``swan``, ``schism``, ``ww3``)

**Required Options:**

* ``--pipeline-name TEXT``: Name of the Prax pipeline template

**Optional Options:**

* ``--project TEXT``: Prax project name (overrides oceanum context)
* ``--stage {dev,prod}``: Deployment stage (default: dev)
* ``--template PATH``: Custom pipeline template file
* ``--deploy/--no-deploy``: Deploy pipeline if needed (default: --deploy)
* ``--wait/--no-wait``: Wait for pipeline completion (default: --no-wait)
* ``--timeout INTEGER``: Execution timeout in seconds
* ``--tags TEXT``: Comma-separated tags for metadata

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

   # Execute in production with tags
   oceanum rompy run config.yml schism \
       --pipeline-name schism-operational \
       --stage prod \
       --tags "australia,operational,storm-surge"

   # Execute with custom pipeline template
   oceanum rompy run config.yml ww3 \
       --pipeline-name custom-ww3 \
       --template ./custom_pipeline.yml \
       --deploy

**Output:**

The command returns rich terminal output with execution details:

.. code-block:: text

   🚀 Executing pipeline: swan-operational
   📊 Model: swan, Run ID: perth_coast_swan_basic
   🏢 Org: oceanum, Project: wave-forecasting, Stage: dev
   ✅ Pipeline executed successfully!
   🆔 Prax run ID: prax-perth_coast_swan_basic
   💡 Monitor with: oceanum rompy status prax-perth_coast_swan_basic

status
~~~~~~

Monitor pipeline execution status with real-time updates.

**Syntax:**

.. code-block:: bash

   oceanum rompy status RUN_ID [OPTIONS]

**Required Arguments:**

* ``RUN_ID``: Prax run identifier

**Options:**

* ``--watch/--no-watch``: Continuously monitor status updates (default: --no-watch)
* ``--interval INTEGER``: Update interval for watch mode in seconds (default: 10)
* ``--json``: Output status in JSON format
* ``--detailed``: Show detailed execution information

**Examples:**

.. code-block:: bash

   # Check current status
   oceanum rompy status prax-perth_coast_swan_basic

   # Monitor status with real-time updates
   oceanum rompy status prax-perth_coast_swan_basic --watch

   # Get detailed status information
   oceanum rompy status prax-perth_coast_swan_basic --detailed

   # Export status as JSON
   oceanum rompy status prax-perth_coast_swan_basic --json

**Output Examples:**

Basic status output:

.. code-block:: text

   📊 Pipeline Status: prax-perth_coast_swan_basic
   🔄 Status: RUNNING
   ⏱️  Started: 2024-01-15 10:30:45 UTC
   ⏳ Duration: 0:15:23
   📈 Progress: Stage 2/4 (Executing model)

Watch mode output:

.. code-block:: text

   🔄 Monitoring pipeline: prax-perth_coast_swan_basic
   📊 Status: RUNNING → COMPLETED ✅
   ⏱️  Total duration: 0:23:15
   📁 Outputs: 15 files (245.7 MB)
   💡 Download with: oceanum rompy sync prax-perth_coast_swan_basic ./outputs

logs
~~~~

View and filter pipeline execution logs.

**Syntax:**

.. code-block:: bash

   oceanum rompy logs RUN_ID [OPTIONS]

**Required Arguments:**

* ``RUN_ID``: Prax run identifier

**Options:**

* ``--follow, -f``: Follow log output in real-time
* ``--tail INTEGER``: Show last N lines (default: 100)
* ``--stage TEXT``: Filter logs by pipeline stage
* ``--level {DEBUG,INFO,WARNING,ERROR}``: Filter by log level
* ``--grep TEXT``: Filter logs by text pattern
* ``--since TEXT``: Show logs since timestamp (ISO format)
* ``--output PATH``: Save logs to file
* ``--no-color``: Disable colored log output

**Examples:**

.. code-block:: bash

   # View recent logs
   oceanum rompy logs prax-perth_coast_swan_basic

   # Follow logs in real-time
   oceanum rompy logs prax-perth_coast_swan_basic --follow

   # View logs for specific stage
   oceanum rompy logs prax-perth_coast_swan_basic --stage model-execution

   # Filter error logs and save to file
   oceanum rompy logs prax-perth_coast_swan_basic \
       --level ERROR \
       --output error_logs.txt

   # Filter logs by pattern
   oceanum rompy logs prax-perth_coast_swan_basic \
       --grep "wave height" \
       --tail 200

   # Show logs since specific time
   oceanum rompy logs prax-perth_coast_swan_basic \
       --since "2024-01-15T10:30:00Z"

**Output:**

Logs are displayed with color coding and timestamps:

.. code-block:: text

   📋 Pipeline Logs: prax-perth_coast_swan_basic
   ════════════════════════════════════════════
   [10:30:45] 🔄 INIT    Starting SWAN model execution
   [10:30:46] ℹ️  INFO    Grid: 100x80, Resolution: 0.05°
   [10:31:15] ✅ INFO    Model initialization complete
   [10:31:16] 🌊 INFO    Processing wave conditions...
   [10:35:22] ⚠️  WARN    High wave heights detected in domain
   [10:42:18] ✅ INFO    Model execution completed successfully

sync
~~~~

Download and organize pipeline outputs with automatic file management.

**Syntax:**

.. code-block:: bash

   oceanum rompy sync RUN_ID OUTPUT_DIR [OPTIONS]

**Required Arguments:**

* ``RUN_ID``: Prax run identifier
* ``OUTPUT_DIR``: Local directory for downloaded files

**Options:**

* ``--organize/--no-organize``: Organize files by stage and type (default: --organize)
* ``--include TEXT``: Include only files matching pattern (e.g., "*.nc,*.txt")
* ``--exclude TEXT``: Exclude files matching pattern
* ``--stage TEXT``: Download files from specific pipeline stage only
* ``--verify/--no-verify``: Verify file integrity after download (default: --verify)
* ``--overwrite/--no-overwrite``: Overwrite existing files (default: --no-overwrite)
* ``--metadata/--no-metadata``: Include run metadata file (default: --metadata)

**Examples:**

.. code-block:: bash

   # Download all outputs with organization
   oceanum rompy sync prax-perth_coast_swan_basic ./outputs

   # Download only NetCDF files
   oceanum rompy sync prax-perth_coast_swan_basic ./netcdf_data \
       --include "*.nc" \
       --no-organize

   # Download from specific stage
   oceanum rompy sync prax-perth_coast_swan_basic ./model_outputs \
       --stage postprocess \
       --verify

   # Download without file organization
   oceanum rompy sync prax-perth_coast_swan_basic ./raw_outputs \
       --no-organize \
       --no-metadata

   # Download excluding log files
   oceanum rompy sync prax-perth_coast_swan_basic ./outputs \
       --exclude "*.log,*.tmp" \
       --overwrite

**Output:**

The command provides detailed download progress:

.. code-block:: text

   📁 Syncing outputs: prax-perth_coast_swan_basic
   🔍 Found 15 files (245.7 MB total)
   📊 Downloading: ████████████████████ 100%

   📂 Files organized by stage and type:
     outputs/
     ├── postprocess/
     │   ├── netcdf/
     │   │   ├── wave_height.nc (125.3 MB)
     │   │   └── wave_period.nc (89.4 MB)
     │   └── plots/
     │       ├── wave_field.png (2.1 MB)
     │       └── time_series.png (1.8 MB)
     ├── run/
     │   ├── logs/
     │   │   └── model.log (15.2 MB)
     │   └── input/
     │       └── config.yml (2.3 KB)
     └── run_metadata.json (1.8 KB)

   ✅ Downloaded 15 files successfully
   📋 Run metadata saved to: outputs/run_metadata.json

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
   PIPELINE="swan-operational"
   OUTPUT_DIR="./results/$(date +%Y%m%d_%H%M%S)"

   # Ensure authentication
   if ! oceanum auth status &>/dev/null; then
       echo "❌ Not authenticated. Please run: oceanum auth login"
       exit 1
   fi

   echo "🚀 Starting automated modeling workflow"

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

   def submit_pipeline(config_file, model, pipeline_name):
       """Submit pipeline and return run ID."""
       cmd = f"oceanum rompy run {config_file} {model} --pipeline-name {pipeline_name} --wait"
       output = run_command(cmd)

       # Extract run ID from output
       for line in output.split('\n'):
           if '🆔 Prax run ID:' in line:
               return line.split()[-1]

       raise ValueError("Could not extract run ID from output")

   def wait_for_completion(run_id, timeout=3600):
       """Wait for pipeline completion."""
       import time
       start_time = time.time()

       while time.time() - start_time < timeout:
           status_json = run_command(f"oceanum rompy status {run_id} --json")
           status_data = json.loads(status_json)

           current_status = status_data['status']
           print(f"🔄 Status: {current_status}")

           if current_status == 'COMPLETED':
               print("✅ Pipeline completed successfully!")
               return True
           elif current_status == 'FAILED':
               print("❌ Pipeline execution failed!")
               return False

           time.sleep(30)  # Check every 30 seconds

       print("⏰ Pipeline execution timed out!")
       return False

   def main():
       """Main execution workflow."""
       # Configuration
       domain = "perth_coast"
       model = "swan"
       template = "operational"
       pipeline = "swan-operational"

       timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
       output_dir = Path(f"./results/{timestamp}")

       print("🚀 Starting automated modeling workflow")

       # Check authentication
       try:
           run_command("oceanum auth status")
       except:
           print("❌ Not authenticated. Please run: oceanum auth login")
           sys.exit(1)

       # Generate configuration
       print(f"📝 Generating {model} configuration...")
       run_command(f"oceanum rompy init {model} --template {template} --domain {domain}")

       # Submit pipeline
       print(f"🎯 Executing {model} model via Prax...")
       run_id = submit_pipeline("config.yml", model, pipeline)
       print(f"📋 Run ID: {run_id}")

       # Wait for completion
       if not wait_for_completion(run_id):
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
   oceanum prax pipelines list

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
