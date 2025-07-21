User Guide
==========

This section provides comprehensive documentation for using rompy-oceanum effectively. Whether you're new to the framework or looking to implement advanced workflows, these guides will help you make the most of the Oceanum Prax pipeline integration.

.. grid:: 2

    .. grid-item-card:: :octicon:`rocket` Basic Usage
        :link: basic-usage
        :link-type: doc

        Learn the fundamentals of using rompy-oceanum for wave model execution.

    .. grid-item-card:: :octicon:`gear` Configuration
        :link: configuration
        :link-type: doc

        Configure rompy-oceanum for your specific needs and environment.

    .. grid-item-card:: :octicon:`workflow` Pipeline Backends
        :link: pipeline-backends
        :link-type: doc

        Understand and configure different pipeline execution backends.

    .. grid-item-card:: :octicon:`terminal` CLI Reference
        :link: cli-reference
        :link-type: doc

        Complete command-line interface documentation and examples.

    .. grid-item-card:: :octicon:`tools` Troubleshooting
        :link: troubleshooting
        :link-type: doc

        Solve common issues and debug problems effectively.

    .. grid-item-card:: :octicon:`workflow` Advanced Workflows
        :link: advanced-workflows
        :link-type: doc

        Implement complex modeling workflows and automation.

Overview
--------

rompy-oceanum extends the rompy wave modeling framework with cloud-native execution capabilities through the Oceanum Prax pipeline system. The user guide covers:

**Core Concepts**
   Understanding the plugin architecture, configuration patterns, and execution models.

**Getting Started**
   Step-by-step instructions for your first wave model submission to Prax.

**Configuration Management**
   Environment variables, configuration files, and runtime parameters.

**Pipeline Operations**
   Submitting, monitoring, and managing model execution pipelines.

**Result Management**
   Downloading outputs, registering in DataMesh, and post-processing workflows.

**Best Practices**
   Performance optimization, error handling, and production deployment strategies.

Quick Navigation
----------------

New Users
~~~~~~~~~

If you're new to rompy-oceanum, start with:

1. :doc:`basic-usage` - Learn core concepts and simple workflows
2. :doc:`configuration` - Set up your environment and authentication
3. :doc:`../examples/swan-workflow` - Follow a complete SWAN modeling example

Experienced Users
~~~~~~~~~~~~~~~~~

For advanced usage patterns:

1. :doc:`pipeline-backends` - Configure custom execution environments
2. :doc:`advanced-workflows` - Implement batch processing and automation
3. :doc:`../api/index` - Explore programmatic interfaces

Administrators
~~~~~~~~~~~~~~

For deployment and management:

1. :doc:`configuration` - Environment and security configuration
2. :doc:`troubleshooting` - Debugging and monitoring
3. :doc:`../development/architecture` - Understanding system design

Common Workflows
----------------

The most common rompy-oceanum workflows include:

**Single Model Execution**
   Submit a single wave model configuration for remote execution.

**Batch Processing**
   Process multiple model configurations in parallel or sequence.

**Ensemble Modeling**
   Run multiple model variants with different parameters or forcing data.

**Operational Forecasting**
   Automated model execution for real-time wave forecasting.

**Research Workflows**
   Interactive model development and sensitivity analysis.

Plugin Architecture
-------------------

rompy-oceanum integrates with rompy through a clean plugin architecture:

**Architecture Flow:**

::

   rompy ModelRun
        │
        ▼
   Pipeline Backend Selection
        │
        ▼
   ┌─────────────┬─────────────┐
   │    local    │    prax     │
   │ execution   │  backend    │
   └─────────────┴─────────────┘
                      │
                      ▼
              Oceanum Prax API
                      │
                      ▼
              DataMesh Registration

Key benefits of this architecture:

* **Runtime Selection**: Choose execution backend when running, not when configuring
* **Configuration Separation**: Backend settings don't pollute model configuration
* **Extensibility**: Easy to add new backends and postprocessors
* **Compatibility**: Works seamlessly with existing rompy workflows

Environment Setup
-----------------

Before diving into the guides, ensure your environment is properly configured:

.. code-block:: bash

   # Essential environment variables
   export PRAX_TOKEN="your-authentication-token"
   export PRAX_ORG="your-organization"
   export PRAX_PROJECT="your-project"
   export PRAX_BASE_URL="https://prax.oceanum.science"

.. tip::
   See the :doc:`configuration` guide for complete environment setup instructions.

Table of Contents
-----------------

.. toctree::
   :maxdepth: 2

   basic-usage
   configuration
   pipeline-backends
   cli-reference
   advanced-workflows
   troubleshooting

Additional Resources
--------------------

* :doc:`../examples/index` - Practical examples and tutorials
* :doc:`../api/index` - Complete API reference
* :doc:`../development/index` - Development and contribution guides
* `rompy Documentation <https://rompy.readthedocs.io/>`_ - Core framework documentation
* `Oceanum Platform <https://oceanum.science/>`_ - Platform documentation
