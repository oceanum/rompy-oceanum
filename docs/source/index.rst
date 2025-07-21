rompy-oceanum Documentation
===========================

Welcome to the documentation for **rompy-oceanum**, a Python library that extends `rompy <https://github.com/rom-py/rompy>`_ with Oceanum Prax pipeline integration capabilities through the oceanum CLI plugin system.

This library provides seamless integration with the oceanum CLI, enabling submission of rompy model configurations to Oceanum's Prax pipeline system for remote execution, monitoring, and result management through the unified ``oceanum rompy`` command interface.

.. grid:: 2

    .. grid-item-card:: :octicon:`rocket` Quick Start
        :link: getting-started
        :link-type: doc

        Get up and running with rompy-oceanum in minutes.

    .. grid-item-card:: :octicon:`book` User Guide
        :link: user-guide/index
        :link-type: doc

        Learn how to use rompy-oceanum effectively.

    .. grid-item-card:: :octicon:`code` API Reference
        :link: api/index
        :link-type: doc

        Complete API documentation for all modules and classes.

    .. grid-item-card:: :octicon:`repo` Examples
        :link: examples/index
        :link-type: doc

        Practical examples and tutorials.

Key Features
------------

* **Oceanum CLI Integration**: Seamlessly integrated as ``oceanum rompy`` command group
* **Unified Authentication**: Uses oceanum's built-in authentication system
* **Enhanced User Experience**: Rich terminal output with progress indicators and organized file management
* **Plugin-Based Architecture**: Uses oceanum's plugin system for extensible command structure
* **Complete Workflow Support**: From configuration generation to result management
* **Smart Configuration Templates**: Automated rompy configuration generation optimized for Prax execution
* **Organized Output Management**: Automatic file organization by stage and type

Architecture Overview
---------------------

rompy-oceanum follows a modular architecture aligned with rompy's plugin system:

**Architecture Flow:**

::

   rompy ModelRun
        │
        ▼
   PraxPipelineBackend ──────► PraxClient ──────► Oceanum Prax API
        │
        ▼
   DataMeshPostprocessor ──────► Oceanum DataMesh
        │
        ▲
   CLI Interface ──────────────┘
        │
   Configuration Models

Core Components:

* **PraxPipelineBackend**: Main pipeline backend implementation for Prax integration
* **PraxClient**: Low-level API client for Prax service interactions
* **Configuration Models**: Pydantic models for backend configuration (PraxConfig, DataMeshConfig)
* **Result Management**: PraxResult for status monitoring and output retrieval
* **CLI Integration**: Command-line interface for pipeline operations

Quick Example
-------------

Here's a simple example of using the oceanum rompy CLI integration:

.. code-block:: bash

   # First, authenticate with oceanum
   oceanum auth login

   # Create optimized rompy configuration
   oceanum rompy init swan --template basic --domain "my_domain"

   # Execute model via Prax pipeline
   oceanum rompy run config.yml swan --pipeline-name my-pipeline

   # Monitor pipeline status
   oceanum rompy status <run-id>

   # View real-time logs
   oceanum rompy logs <run-id> --follow

   # Download organized results
   oceanum rompy sync <run-id> ./outputs --organize

For programmatic usage:

.. code-block:: python

   import rompy
   from rompy_oceanum import PraxPipelineBackend

   # Create your rompy model configuration
   model_run = rompy.ModelRun(config=swan_config, ...)

   # Execute using Prax pipeline backend
   result = model_run.pipeline(
       backend="prax",
       pipeline_name="swan-from-rompy",
       user="username",
       org="orgname",
       project="project-name",
       stage="dev"
   )

   # Monitor the pipeline
   print(f"Pipeline submitted with ID: {result.run_id}")
   result.wait_for_completion()

Installation
------------

Install rompy-oceanum and oceanum CLI using pip:

.. code-block:: bash

   pip install rompy-oceanum oceanum

Verify the integration works:

.. code-block:: bash

   oceanum rompy --help

Or for development:

.. code-block:: bash

   git clone https://github.com/rom-py/rompy-oceanum
   cd rompy-oceanum
   pip install -e ".[dev,docs]"
   pip install oceanum

Table of Contents
-----------------

.. toctree::
   :maxdepth: 2
   :caption: Getting Started

   getting-started
   installation

.. toctree::
   :maxdepth: 2
   :caption: User Guide

   user-guide/index
   user-guide/basic-usage
   user-guide/configuration
   user-guide/pipeline-backends
   user-guide/cli-reference
   user-guide/troubleshooting

.. toctree::
   :maxdepth: 2
   :caption: Examples

   examples/index
   examples/swan-workflow
   examples/advanced-configuration
   examples/batch-processing

.. toctree::
   :maxdepth: 2
   :caption: API Reference

   api/index

.. toctree::
   :maxdepth: 2
   :caption: Development

   development/index
   development/contributing
   development/architecture
   development/testing
   development/migration-guide

.. toctree::
   :maxdepth: 1
   :caption: Links

   GitHub Repository <https://github.com/rom-py/rompy-oceanum>
   rompy Documentation <https://rompy.readthedocs.io/>
   Oceanum Platform <https://oceanum.science/>

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
