Troubleshooting
===============

This guide helps you diagnose and resolve common issues when using rompy-oceanum. It covers authentication problems, configuration errors, pipeline failures, and performance issues.

Quick Diagnostics
-----------------

If you're experiencing issues, start with these diagnostic commands:

.. code-block:: bash

   # Check version and installation
   rompy-oceanum --version

   # Validate configuration
   rompy-oceanum config validate

   # Test connectivity
   rompy-oceanum config test-connection

   # Check current configuration
   rompy-oceanum config show --hide-secrets

Common Issues
-------------

Authentication Problems
~~~~~~~~~~~~~~~~~~~~~~~

**Symptoms:**
- "Authentication failed" errors
- "Invalid token" messages
- 401/403 HTTP errors

**Solutions:**

1. **Verify Token Format:**

   .. code-block:: bash

      # Check if token is set
      echo ${PRAX_TOKEN:0:20}...  # Show first 20 characters

      # Token should be a long alphanumeric string
      # If empty or wrong format, obtain new token

2. **Check Token Validity:**

   .. code-block:: bash

      # Test connection with current token
      rompy-oceanum config test-connection

      # If fails, token may be expired or invalid

3. **Verify Environment Variables:**

   .. code-block:: bash

      # Check all required variables
      env | grep PRAX_

      # Should show:
      # PRAX_TOKEN=your-token
      # PRAX_ORG=your-org
      # PRAX_PROJECT=your-project
      # PRAX_BASE_URL=https://prax.oceanum.science

4. **Common Token Issues:**

   .. code-block:: bash

      # Wrong variable name
      export PRAX_TOKEN="your-token"  # Not PRAX_API_TOKEN

      # Extra whitespace (common copy-paste error)
      export PRAX_TOKEN="$(echo 'your-token' | xargs)"

      # Wrong base URL
      export PRAX_BASE_URL="https://prax.oceanum.science"  # Not .com

Configuration Errors
~~~~~~~~~~~~~~~~~~~~~

**Symptoms:**
- "Configuration validation failed"
- YAML syntax errors
- Missing required fields

**Solutions:**

1. **Validate YAML Syntax:**

   .. code-block:: bash

      # Check YAML is valid
      python -c "import yaml; yaml.safe_load(open('config.yaml'))"

      # Common YAML issues:
      # - Inconsistent indentation
      # - Missing quotes around special characters
      # - Incorrect nesting

2. **Validate rompy-oceanum Configuration:**

   .. code-block:: bash

      # Use built-in validation
      rompy-oceanum config validate config.yaml

      # Fix reported errors one by one

3. **Check File Permissions:**

   .. code-block:: bash

      # Configuration file should be readable
      ls -la ~/.rompy-oceanum/config.yaml

      # Fix permissions if needed
      chmod 600 ~/.rompy-oceanum/config.yaml

4. **Common Configuration Issues:**

   .. code-block:: yaml

      # Incorrect (missing required fields):
      prax:
        org: "my-org"

      # Correct:
      prax:
        base_url: "https://prax.oceanum.science"
        org: "my-org"
        project: "my-project"

Pipeline Submission Failures
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Symptoms:**
- "Pipeline not found" errors
- Submission timeouts
- "Invalid pipeline configuration"

**Solutions:**

1. **Verify Pipeline Exists:**

   .. code-block:: bash

      # List available pipelines
      rompy-oceanum pipelines --org your-org --project your-project

      # Check exact pipeline name (case-sensitive)

2. **Check Model Configuration:**

   .. code-block:: bash

      # Validate rompy configuration first
      python -c "
      import rompy
      config = rompy.ModelRun.from_file('your-config.yaml')
      print('Configuration valid')
      "

3. **Verify Resource Requirements:**

   - Check if your model requires more resources than pipeline allows
   - Large models may need special pipeline templates
   - Contact admin for resource limit increases

4. **Debug Submission:**

   .. code-block:: bash

      # Enable debug mode for detailed error info
      rompy-oceanum --debug run --config your-config.yaml --pipeline your-pipeline

Pipeline Execution Failures
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Symptoms:**
- Pipeline status shows "failed"
- Unexpected termination
- Resource limit errors

**Solutions:**

1. **Check Pipeline Logs:**

   .. code-block:: bash

      # View all logs
      rompy-oceanum logs your-run-id

      # Search for errors
      rompy-oceanum logs your-run-id --grep "ERROR\|FAILED\|Exception"

      # Check specific stages
      rompy-oceanum logs your-run-id --stage model-execution

2. **Common Execution Issues:**

   **Memory Errors:**

   .. code-block:: bash

      # Look for "Out of memory" or "OOMKilled"
      rompy-oceanum logs your-run-id --grep "memory\|OOM"

      # Solution: Use pipeline with more memory or optimize model

   **Timeout Errors:**

   .. code-block:: bash

      # Check for timeout messages
      rompy-oceanum logs your-run-id --grep "timeout\|exceeded"

      # Solution: Increase timeout or optimize model

   **Input Data Issues:**

   .. code-block:: bash

      # Check for file not found errors
      rompy-oceanum logs your-run-id --grep "No such file\|FileNotFound"

      # Solution: Verify input data paths and availability

3. **Resource Monitoring:**

   .. code-block:: bash

      # Get detailed status including resource usage
      rompy-oceanum status your-run-id --json

Network and Connectivity Issues
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Symptoms:**
- Connection timeouts
- "Network unreachable" errors
- Intermittent failures

**Solutions:**

1. **Check Network Connectivity:**

   .. code-block:: bash

      # Test basic connectivity
      curl -I https://prax.oceanum.science

      # Test with authentication
      curl -H "Authorization: Bearer $PRAX_TOKEN" \
           https://prax.oceanum.science/health

2. **Increase Timeouts:**

   .. code-block:: bash

      # Use longer timeout for unstable connections
      rompy-oceanum run \
           --config your-config.yaml \
           --pipeline your-pipeline \
           --timeout 7200  # 2 hours

3. **Check Firewall/Proxy:**

   - Ensure HTTPS (port 443) access to oceanum.science domains
   - Configure proxy settings if behind corporate firewall
   - Whitelist Oceanum IP ranges if needed

4. **Retry Logic:**

   .. code-block:: bash

      # rompy-oceanum has built-in retry logic
      # For additional reliability, use wrapper script:

      #!/bin/bash
      for i in {1..3}; do
          if rompy-oceanum run --config config.yaml --pipeline pipeline; then
              break
          fi
          echo "Attempt $i failed, retrying..."
          sleep 60
      done

Output Download Issues
~~~~~~~~~~~~~~~~~~~~~~

**Symptoms:**
- Download timeouts
- Partial downloads
- "File not found" errors

**Solutions:**

1. **Check Pipeline Completion:**

   .. code-block:: bash

      # Ensure pipeline completed successfully
      rompy-oceanum status your-run-id

      # Only download from completed pipelines

2. **Verify Output Files:**

   .. code-block:: bash

      # Check what outputs are available
      rompy-oceanum status your-run-id --json | jq '.outputs'

3. **Resume Interrupted Downloads:**

   .. code-block:: bash

      # Use --force to overwrite partial downloads
      rompy-oceanum download your-run-id --force --verify

4. **Download Specific Files:**

   .. code-block:: bash

      # Download only needed files to save time/space
      rompy-oceanum download your-run-id --files "*.nc"

Performance Issues
------------------

Slow Pipeline Execution
~~~~~~~~~~~~~~~~~~~~~~~

**Diagnosis:**

.. code-block:: bash

   # Monitor execution progress
   rompy-oceanum status your-run-id --watch

   # Check resource usage in logs
   rompy-oceanum logs your-run-id --grep "CPU\|Memory\|Progress"

**Solutions:**

1. **Optimize Model Configuration:**
   - Reduce grid resolution for testing
   - Simplify physics options
   - Use shorter simulation periods

2. **Use Appropriate Pipeline:**
   - Choose pipeline templates matching your resource needs
   - Use GPU-enabled pipelines for supported models
   - Consider parallel execution options

3. **Monitor Resource Usage:**

   .. code-block:: python

      # Add resource monitoring to your workflow
      import time
      from rompy_oceanum.client import PraxClient

      client = PraxClient()
      result = client.get_run_status(run_id)

      while not result.is_complete():
          status = result.get_detailed_status()
          print(f"CPU: {status.get('cpu_usage', 'N/A')}")
          print(f"Memory: {status.get('memory_usage', 'N/A')}")
          time.sleep(60)

High Memory Usage
~~~~~~~~~~~~~~~~~

**Symptoms:**
- "Out of memory" errors
- Pipeline termination
- Slow execution

**Solutions:**

1. **Reduce Model Size:**

   .. code-block:: python

      # Reduce grid resolution
      grid = SwanGrid(
          x0=115.0, y0=-35.0,
          dx=0.1,  # Increase from 0.05
          dy=0.1,  # Increase from 0.05
          nx=50,   # Reduce from 100
          ny=40    # Reduce from 80
      )

2. **Use Memory-Efficient Options:**

   .. code-block:: yaml

      # In SWAN configuration
      physics:
        whitecapping: true
        breaking: true
        memory_optimization: true  # If available

3. **Request More Memory:**

   .. code-block:: bash

      # Use high-memory pipeline if available
      rompy-oceanum run \
           --config config.yaml \
           --pipeline swan-highmem-from-rompy

Debugging Techniques
--------------------

Enable Debug Mode
~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Global debug flag
   rompy-oceanum --debug command args

   # Environment variable
   export ROMPY_OCEANUM_DEBUG=1

   # Configuration file
   echo "debug: true" >> ~/.rompy-oceanum/config.yaml

Verbose Logging
~~~~~~~~~~~~~~~

.. code-block:: python

   import logging
   from rompy_oceanum import configure_logging

   # Enable detailed logging
   configure_logging(level=logging.DEBUG)

   # Your rompy-oceanum code here

Inspect API Requests
~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Enable HTTP request logging
   import logging
   import http.client as http_client

   http_client.HTTPConnection.debuglevel = 1
   logging.basicConfig()
   logging.getLogger().setLevel(logging.DEBUG)

   # Now run your rompy-oceanum code

Test with Mock Mode
~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Use mock mode for testing without actual API calls
   export ROMPY_OCEANUM_MOCK_MODE=1
   rompy-oceanum run --config test-config.yaml --pipeline test-pipeline

Error Codes Reference
---------------------

Exit Codes
~~~~~~~~~~

* **0**: Success
* **1**: General error
* **2**: Command line usage error
* **3**: Authentication error
* **4**: Configuration error
* **5**: Network error
* **6**: Pipeline error
* **7**: File system error

HTTP Status Codes
~~~~~~~~~~~~~~~~~

* **400**: Bad request (check configuration)
* **401**: Unauthorized (check token)
* **403**: Forbidden (check permissions)
* **404**: Not found (check pipeline/run ID)
* **429**: Rate limited (wait and retry)
* **500**: Server error (contact support)
* **503**: Service unavailable (try later)

Advanced Troubleshooting
------------------------

Memory Dumps
~~~~~~~~~~~~

For severe issues, collect memory dumps:

.. code-block:: python

   import tracemalloc
   import gc

   # Start tracing
   tracemalloc.start()

   # Your problematic code
   try:
       result = model_run.pipeline(...)
   except Exception as e:
       # Get memory usage
       current, peak = tracemalloc.get_traced_memory()
       print(f"Current memory: {current / 1024 / 1024:.1f} MB")
       print(f"Peak memory: {peak / 1024 / 1024:.1f} MB")

       # Force garbage collection
       gc.collect()

       raise

Network Debugging
~~~~~~~~~~~~~~~~~

Capture network traffic for debugging:

.. code-block:: bash

   # Install mitmproxy
   pip install mitmproxy

   # Start proxy
   mitmdump --port 8080 --save-stream-file traffic.log &

   # Configure rompy-oceanum to use proxy
   export HTTPS_PROXY=http://localhost:8080
   rompy-oceanum run --config config.yaml --pipeline pipeline

   # Stop proxy and analyze traffic.log

System Information Collection
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Collect system information for support:

.. code-block:: bash

   # Create diagnostic report
   cat > diagnostic_report.txt << EOF
   # rompy-oceanum Diagnostic Report
   Date: $(date)

   ## System Information
   OS: $(uname -a)
   Python: $(python --version)

   ## Package Versions
   $(pip list | grep -E "(rompy|oceanum|pydantic)")

   ## Configuration
   $(rompy-oceanum config show --hide-secrets)

   ## Environment Variables
   $(env | grep -E "(PRAX|DATAMESH|ROMPY)")

   ## Recent Logs
   $(tail -50 ~/.rompy-oceanum/logs/rompy-oceanum.log)
   EOF

Getting Support
---------------

Before Contacting Support
~~~~~~~~~~~~~~~~~~~~~~~~~

1. **Check this troubleshooting guide**
2. **Search existing GitHub issues**
3. **Enable debug mode** and collect error messages
4. **Test with minimal configuration**
5. **Verify network connectivity**

What to Include in Support Requests
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* **Error messages** (full text, not screenshots)
* **Configuration files** (with secrets redacted)
* **System information** (OS, Python version, package versions)
* **Steps to reproduce** the issue
* **Expected vs actual behavior**
* **Debug logs** if available

Support Channels
~~~~~~~~~~~~~~~~~

* **GitHub Issues**: https://github.com/oceanum/rompy-oceanum/issues
* **Documentation**: https://rompy-oceanum.readthedocs.io/
* **rompy Community**: https://rompy.readthedocs.io/

Quick Reference
---------------

Diagnostic Commands
~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Quick health check
   rompy-oceanum config test-connection

   # Validate configuration
   rompy-oceanum config validate

   # Check recent runs
   rompy-oceanum list --limit 5

   # Monitor active run
   rompy-oceanum status --watch run-id

   # View error logs
   rompy-oceanum logs run-id --grep ERROR

Common Fixes
~~~~~~~~~~~~

.. code-block:: bash

   # Fix authentication
   export PRAX_TOKEN="your-new-token"
   rompy-oceanum config test-connection

   # Reset configuration
   rm ~/.rompy-oceanum/config.yaml
   rompy-oceanum config init

   # Clean cache
   rompy-oceanum clean --all

   # Force download
   rompy-oceanum download run-id --force

Prevention Tips
---------------

1. **Regular Testing**: Test configurations in development before production
2. **Monitor Resources**: Track memory and CPU usage patterns
3. **Update Regularly**: Keep rompy-oceanum and dependencies updated
4. **Backup Configurations**: Version control your configuration files
5. **Document Changes**: Keep track of configuration modifications
6. **Monitor Logs**: Set up log monitoring for early issue detection

Remember: Most issues are configuration-related and can be resolved by carefully checking authentication, network connectivity, and configuration syntax.
