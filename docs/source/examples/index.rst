Examples
========

This section provides practical examples and tutorials for using rompy-oceanum effectively. The examples progress from basic usage patterns to advanced operational workflows, demonstrating real-world applications of wave modeling with Oceanum Prax integration.

.. grid:: 2

    .. grid-item::

        .. card:: :octicon:`zap` Quick Start
            :link: swan-workflow
            :link-type: doc

            Complete SWAN wave model workflow from configuration to results.

    .. grid-item::

        .. card:: :octicon:`gear` Advanced Configuration
            :link: advanced-configuration
            :link-type: doc

            Complex configuration patterns and optimization techniques.

    .. grid-item::

        .. card:: :octicon:`stack` Batch Processing
            :link: batch-processing
            :link-type: doc

            Execute multiple models efficiently with batch processing.

    .. grid-item::

        .. card:: :octicon:`workflow` Operational Workflows
            :class-card: sd-text-muted

            Production-ready forecasting and monitoring systems (coming soon).

Overview
--------

The examples are organized by complexity and use case:

**Getting Started Examples**
   Simple, focused examples for learning core concepts and basic workflows.

**Operational Examples**
   Production-ready patterns for automated forecasting and monitoring systems.

**Integration Examples**
   Demonstrations of rompy-oceanum integration with external systems and workflows.

**Advanced Examples**
   Complex scenarios including ensemble modeling, uncertainty quantification, and custom backends.

Prerequisites
-------------

Before working through these examples, ensure you have:

1. **rompy-oceanum installed** with all dependencies
2. **Oceanum CLI configured** and authenticated
3. **Access to Prax pipeline system** through your organization
4. **Basic familiarity** with rompy and wave modeling concepts

Setup for Examples
------------------

Most examples assume a common setup:

.. code-block:: bash

   # Authenticate with Oceanum
   oceanum auth login

   # Set environment variables
   export PRAX_ORG="your-organization"
   export PRAX_PROJECT="examples"
   export PRAX_USER="your-username"

   # Create working directory
   mkdir rompy-oceanum-examples
   cd rompy-oceanum-examples

Example Data
------------

Many examples use sample datasets available in the rompy-oceanum repository:

.. code-block:: bash

   # Download example data
   git clone https://github.com/oceanum/rompy-oceanum-examples.git
   cd rompy-oceanum-examples/data

Available datasets include:

* **Sample grids**: Pre-configured computational grids for different regions
* **Forcing data**: Sample wind and wave boundary condition files
* **Configuration templates**: Ready-to-use model configuration files
* **Expected outputs**: Reference results for validation

Example Categories
------------------

Basic Workflows
~~~~~~~~~~~~~~~

Learn fundamental concepts through simple, focused examples:

* **Hello World**: Your first rompy-oceanum model run
* **Configuration Basics**: Understanding configuration patterns
* **Result Management**: Working with model outputs
* **CLI Usage**: Command-line interface examples

Model-Specific Examples
~~~~~~~~~~~~~~~~~~~~~~~

Examples tailored for specific wave models:

* **SWAN Workflows**: Complete SWAN modeling examples
* **WAVEWATCH III**: WW3 configuration and execution
* **Multi-model Comparison**: Running different models on the same domain

Operational Patterns
~~~~~~~~~~~~~~~~~~~~

Production-ready examples for operational use:

* **Automated Forecasting**: Scheduled model execution
* **Monitoring and Alerting**: Real-time system monitoring
* **Error Recovery**: Robust error handling patterns
* **Performance Optimization**: Resource usage optimization

Integration Examples
~~~~~~~~~~~~~~~~~~~~

Demonstrations of rompy-oceanum integration:

* **Data Pipeline Integration**: Apache Airflow and Prefect workflows
* **Custom Backends**: Implementing custom execution backends
* **External API Integration**: Connecting to external data sources
* **Result Publishing**: Automated result dissemination

Code Organization
-----------------

Each example follows a consistent structure:

.. code-block:: text

   example-name/
   ├── README.rst          # Example overview and instructions
   ├── config/             # Configuration files
   │   ├── model.yml       # Model configuration
   │   └── backend.yml     # Backend configuration
   ├── scripts/            # Execution scripts
   │   ├── run.py          # Main execution script
   │   └── utils.py        # Helper functions
   ├── data/               # Input data files
   ├── outputs/            # Expected output directory
   └── tests/              # Validation tests

Running Examples
----------------

Each example can be executed in multiple ways:

**Interactive Execution:**

.. code-block:: bash

   # Navigate to example directory
   cd swan-workflow

   # Run interactively
   python scripts/run.py

**CLI Execution:**

.. code-block:: bash

   # Using oceanum CLI
   oceanum rompy run config/model.yml swan --pipeline-name example-run

**Jupyter Notebooks:**

Many examples include Jupyter notebooks for interactive exploration:

.. code-block:: bash

   # Start Jupyter
   jupyter lab

   # Open example notebook
   # Navigate to example-name/notebook.ipynb

Validation and Testing
----------------------

Each example includes validation to ensure correct execution:

.. code-block:: bash

   # Run example tests
   cd example-name
   pytest tests/

   # Validate outputs
   python scripts/validate.py

Expected outputs and reference results are provided for comparison.

Troubleshooting Examples
------------------------

If you encounter issues running examples:

1. **Check authentication**: Ensure you're properly authenticated with Oceanum
2. **Verify environment**: Check that all required environment variables are set
3. **Review logs**: Examine execution logs for detailed error information
4. **Check resources**: Ensure sufficient computational resources are available

Common issues and solutions:

**Authentication Errors:**

.. code-block:: bash

   # Refresh authentication
   oceanum auth login --refresh

**Resource Limitations:**

.. code-block:: bash

   # Check available resources
   oceanum status resources

**Configuration Issues:**

.. code-block:: bash

   # Validate configuration
   oceanum rompy validate config/model.yml

Contributing Examples
---------------------

We welcome contributions of new examples! To contribute:

1. **Follow the standard structure** outlined above
2. **Include comprehensive documentation** and comments
3. **Provide validation tests** to ensure correctness
4. **Use realistic, educational scenarios** that demonstrate best practices

See the :doc:`../development/contributing` guide for detailed contribution instructions.

Table of Contents
-----------------

.. toctree::
   :maxdepth: 2

   swan-workflow
   advanced-configuration
   batch-processing

Quick Reference
---------------

* **Most Popular Examples:**

* :doc:`swan-workflow` - Complete SWAN modeling workflow
* :doc:`batch-processing` - Parallel model execution patterns
* Operational workflows - Production forecasting systems (coming soon)

**By Difficulty Level:**

* **Beginner**: :doc:`swan-workflow`
* **Intermediate**: :doc:`advanced-configuration`, :doc:`batch-processing`
* **Advanced**: Operational workflows (coming soon)

**By Use Case:**

* **Research**: Configuration optimization, sensitivity analysis
* **Operations**: Automated forecasting, monitoring, alerting (coming soon)
* **Development**: Custom backends, integration patterns

Additional Resources
--------------------

* :doc:`../user-guide/index` - Comprehensive user documentation
* :doc:`../api/index` - Complete API reference
* `rompy Documentation <https://rompy.readthedocs.io/>`_ - Core framework documentation
* `Oceanum Platform <https://oceanum.science/>`_ - Platform documentation and tutorials
