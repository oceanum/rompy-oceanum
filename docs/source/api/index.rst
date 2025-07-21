API Reference
=============

.. note::
   This section is under development. Complete API documentation will be added in future releases.

Overview
--------

The rompy-oceanum API provides programmatic access to wave modeling capabilities through the Oceanum Prax pipeline system.

Coming Soon
-----------

This section will include documentation for:

* **Backend Classes**: PraxPipelineBackend, PraxConfig, and related components
* **Client Interfaces**: PraxClient and API interaction classes
* **Result Management**: PraxResult and output handling utilities
* **Configuration Models**: Pydantic models for validation and serialization
* **CLI Commands**: oceanum rompy command implementations

For now, please refer to:

* The source code docstrings in the rompy_oceanum package
* :doc:`../user-guide/index` - User guide with usage examples
* `rompy API documentation <https://rompy.readthedocs.io/>`_ - Core framework API

Module Structure
----------------

The rompy-oceanum package is organized as follows:

.. code-block:: text

   rompy_oceanum/
   ├── pipeline/       # Pipeline backend implementations
   ├── postprocess/    # Post-processing components
   ├── cli/            # Command-line interface
   └── config/         # Configuration utilities

Quick Reference
---------------

For common programmatic usage patterns:

.. code-block:: python

   # Basic usage
   import rompy

   # Create model run with rompy configuration
   model_run = rompy.ModelRun(config=your_config)

   # Execute with Prax backend
   result = model_run.pipeline(
       backend="prax",
       pipeline_name="my-model",
       org="your-org",
       project="your-project"
   )

   # Monitor progress
   print(f"Status: {result.status}")

See Also
--------

* :doc:`../user-guide/basic-usage` - Getting started guide
* :doc:`../user-guide/pipeline-backends` - Backend configuration
* :doc:`../examples/index` - Practical examples
