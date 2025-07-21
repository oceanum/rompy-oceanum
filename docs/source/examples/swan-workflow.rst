SWAN Workflow Example
=====================

.. note::
   This is a basic example demonstrating SWAN model execution with rompy-oceanum.
   Advanced features and detailed configurations will be added in future releases.

Overview
--------

This example shows how to run a SWAN wave model using rompy-oceanum with the Oceanum Prax backend. The workflow demonstrates:

* Basic SWAN model configuration
* Submitting to the Prax pipeline system
* Monitoring execution progress
* Retrieving results

Prerequisites
-------------

Before starting this example, ensure you have:

.. code-block:: bash

   # Install required packages
   pip install rompy-oceanum oceanum

   # Authenticate with Oceanum
   oceanum auth login

   # Set environment variables
   export PRAX_ORG="your-organization"
   export PRAX_PROJECT="your-project"

Basic Configuration
-------------------

Create a simple SWAN model configuration:

.. code-block:: yaml
   :caption: config/swan_model.yml

   # Basic SWAN Configuration Example
   model:
     type: swan

   grid:
     # Basic grid configuration
     # Details depend on your specific rompy setup

   time:
     start: "2024-01-01T00:00:00"
     end: "2024-01-01T12:00:00"

   outputs:
     - type: field
       variables: ["hs", "tm01"]

Execution with CLI
------------------

The simplest way to run the model is using the oceanum CLI:

.. code-block:: bash

   # Submit model to Prax pipeline
   oceanum rompy run config/swan_model.yml swan --pipeline-name my-swan-run

   # Monitor progress
   oceanum rompy status <run-id>

   # View logs
   oceanum rompy logs <run-id>

   # Download results when complete
   oceanum rompy sync <run-id> ./outputs

Programmatic Execution
----------------------

You can also execute models programmatically:

.. code-block:: python

   import rompy
   from rompy_oceanum.backends import PraxPipelineBackend

   # Load your model configuration
   config = rompy.load_config("config/swan_model.yml")

   # Create model run
   model_run = rompy.ModelRun(config=config)

   # Execute using Prax backend
   result = model_run.pipeline(
       backend="prax",
       pipeline_name="my-swan-run",
       org="your-org",
       project="your-project"
   )

   print(f"Submitted with run ID: {result.run_id}")

Monitoring Progress
-------------------

Check the status of your model run:

.. code-block:: bash

   # Get current status
   oceanum rompy status <run-id>

   # Follow logs in real-time
   oceanum rompy logs <run-id> --follow

Result Management
-----------------

Once your model completes, download the results:

.. code-block:: bash

   # Download all outputs
   oceanum rompy sync <run-id> ./outputs

   # List available outputs before downloading
   oceanum rompy list <run-id>

Next Steps
----------

This basic example gets you started with rompy-oceanum. For more advanced usage:

* Explore different model configurations in the rompy documentation
* Customize resource requirements for your models
* Set up automated workflows for operational forecasting

.. todo::
   Add more detailed configuration examples and advanced workflow patterns.

See Also
--------

* :doc:`../user-guide/basic-usage` - Complete usage guide
* :doc:`../user-guide/configuration` - Configuration reference
* `rompy Documentation <https://rompy.readthedocs.io/>`_ - Core framework documentation
