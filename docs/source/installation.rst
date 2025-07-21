Installation
============

This guide covers different installation methods for rompy-oceanum and its integration with the oceanum CLI, from basic pip installation to development setup.

Requirements
------------

System Requirements
~~~~~~~~~~~~~~~~~~~

* **Python**: 3.8 or higher
* **Operating System**: Linux, macOS, or Windows
* **Memory**: Minimum 4GB RAM (8GB+ recommended for large models)
* **Storage**: At least 1GB free space for installation and temporary files
* **oceanum CLI**: Required for the plugin integration

Python Dependencies
~~~~~~~~~~~~~~~~~~~

rompy-oceanum automatically installs the following core dependencies:

* ``rompy[swan,schism]>=0.5.1`` - Core wave modeling framework
* ``pydantic>=2.0.0`` - Data validation and settings management
* ``pyyaml>=6.0`` - YAML configuration file support
* ``requests>=2.25.0`` - HTTP client for API interactions
* ``tenacity>=9.0.0`` - Retry logic for robust API calls
* ``click>=8.0.0`` - Command-line interface framework
* ``rich>=10.11.0`` - Enhanced terminal output formatting

Required for oceanum CLI integration:

* ``oceanum`` - Oceanum platform SDK and CLI

Optional Dependencies
~~~~~~~~~~~~~~~~~~~~~

For development and documentation:

* ``pytest>=6.0.0`` - Testing framework
* ``pytest-cov>=2.12.0`` - Coverage reporting
* ``pytest-mock>=3.6.0`` - Mocking for tests
* ``sphinx>=7.0.0`` - Documentation generation
* ``sphinx-rtd-theme>=1.3.0`` - Read the Docs theme
* ``myst-parser>=2.0.0`` - Markdown support in Sphinx

Installation Methods
--------------------

Method 1: Standard Installation (Recommended)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Install rompy-oceanum and oceanum CLI from PyPI using pip:

.. code-block:: bash

   pip install rompy-oceanum oceanum

This installs the latest stable version with all required dependencies and enables the oceanum CLI plugin integration.

Verify the installation:

.. code-block:: bash

   oceanum rompy --help

Method 2: Development Installation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

For contributing to rompy-oceanum or accessing the latest features:

.. code-block:: bash

   # Clone the repository
   git clone https://github.com/rom-py/rompy-oceanum.git
   cd rompy-oceanum

   # Install in development mode with all optional dependencies
   pip install -e ".[dev,docs]"

   # Install oceanum CLI for plugin integration
   pip install oceanum

Method 3: Specific Version Installation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To install a specific version:

.. code-block:: bash

   pip install rompy-oceanum==0.1.0

Method 4: From Source (Latest)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To install the latest development version directly from GitHub:

.. code-block:: bash

   pip install git+https://github.com/rom-py/rompy-oceanum.git oceanum

Virtual Environment Setup
--------------------------

It's strongly recommended to use a virtual environment to avoid dependency conflicts:

Using venv (Python 3.3+)
~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Create virtual environment
   python -m venv rompy-oceanum-env

   # Activate (Linux/macOS)
   source rompy-oceanum-env/bin/activate

   # Activate (Windows)
   rompy-oceanum-env\Scripts\activate

   # Install rompy-oceanum and oceanum CLI
   pip install rompy-oceanum oceanum

Using conda
~~~~~~~~~~~

.. code-block:: bash

   # Create conda environment
   conda create -n rompy-oceanum python=3.9

   # Activate environment
   conda activate rompy-oceanum

   # Install rompy-oceanum and oceanum CLI
   pip install rompy-oceanum oceanum

Using pipenv
~~~~~~~~~~~~

.. code-block:: bash

   # Create Pipfile and install
   pipenv install rompy-oceanum oceanum

   # Activate shell
   pipenv shell

Docker Installation
-------------------

For containerized environments:

.. code-block:: dockerfile

   FROM python:3.9-slim

   # Install system dependencies
   RUN apt-get update && apt-get install -y \
       git \
       && rm -rf /var/lib/apt/lists/*

   # Install rompy-oceanum and oceanum CLI
   RUN pip install rompy-oceanum oceanum

   # Set working directory
   WORKDIR /app

   # Copy your configuration files
   COPY . .

   # Default command
   CMD ["oceanum", "rompy", "--help"]

Build and run:

.. code-block:: bash

   docker build -t rompy-oceanum .
   docker run -it rompy-oceanum

Post-Installation Setup
------------------------

Authentication Setup
~~~~~~~~~~~~~~~~~~~~

After installation, set up authentication with the oceanum platform:

.. code-block:: bash

   # Authenticate with oceanum (one-time setup)
   oceanum auth login

This will authenticate you with all oceanum services, including Prax. No manual token management is required.

.. tip::
   The authentication session persists across terminal sessions. You only need to login once
   or when your session expires.

Plugin Verification
~~~~~~~~~~~~~~~~~~~

1. **Verify oceanum CLI Integration**: Test that the rompy plugin is properly loaded:

   .. code-block:: bash

      oceanum rompy --help

2. **Test Plugin Commands**: Verify all commands are available:

   .. code-block:: bash

      oceanum rompy init --help
      oceanum rompy run --help
      oceanum rompy status --help
      oceanum rompy logs --help
      oceanum rompy sync --help

3. **Test Authentication**: Verify you can authenticate:

   .. code-block:: bash

      oceanum auth status

Verification
------------

Verify your installation works correctly:

.. code-block:: bash

   # Check oceanum CLI integration
   oceanum rompy --help

   # List available rompy commands
   oceanum rompy init --help

   # Verify dependencies
   python -c "import rompy_oceanum; print('Installation successful!')"

   # Test authentication status
   oceanum auth status

Common Installation Issues
--------------------------

Permission Errors
~~~~~~~~~~~~~~~~~~

If you encounter permission errors during installation:

.. code-block:: bash

   # Use --user flag to install in user directory
   pip install --user rompy-oceanum oceanum

   # Or use sudo (not recommended)
   sudo pip install rompy-oceanum oceanum

Dependency Conflicts
~~~~~~~~~~~~~~~~~~~~~

If you have conflicting dependencies:

.. code-block:: bash

   # Create a fresh virtual environment
   python -m venv fresh-env
   source fresh-env/bin/activate  # Linux/macOS
   pip install rompy-oceanum

Network Issues
~~~~~~~~~~~~~~

If installation fails due to network issues:

.. code-block:: bash

   # Use a different index
   pip install --index-url https://pypi.org/simple/ rompy-oceanum oceanum

   # Or increase timeout
   pip install --timeout 1000 rompy-oceanum oceanum

Missing System Dependencies
~~~~~~~~~~~~~~~~~~~~~~~~~~~

On some systems, you may need to install additional system packages:

**Ubuntu/Debian:**

.. code-block:: bash

   sudo apt-get update
   sudo apt-get install python3-dev build-essential

**CentOS/RHEL:**

.. code-block:: bash

   sudo yum install python3-devel gcc

**macOS:**

.. code-block:: bash

   # Install Xcode command line tools
   xcode-select --install

Windows-Specific Issues
~~~~~~~~~~~~~~~~~~~~~~~

On Windows, you may need:

1. **Microsoft C++ Build Tools**: Download and install from Microsoft
2. **Git for Windows**: Required for development installation
3. **PowerShell**: Use PowerShell instead of Command Prompt for better compatibility

Upgrading
---------

To upgrade to the latest version:

.. code-block:: bash

   # Upgrade from PyPI
   pip install --upgrade rompy-oceanum oceanum

   # Force reinstall if needed
   pip install --upgrade --force-reinstall rompy-oceanum oceanum

For development installations:

.. code-block:: bash

   cd rompy-oceanum
   git pull origin main
   pip install -e ".[dev,docs]"
   pip install --upgrade oceanum

Uninstallation
--------------

To remove rompy-oceanum:

.. code-block:: bash

   pip uninstall rompy-oceanum

To remove both rompy-oceanum and oceanum CLI:

.. code-block:: bash

   pip uninstall rompy-oceanum oceanum

.. note::
   This only removes the specified packages. Other dependencies installed automatically
   may remain. Use ``pip list`` to see all installed packages.

Next Steps
----------

After successful installation:

1. Read the :doc:`getting-started` guide
2. Configure your :doc:`user-guide/configuration`
3. Try the :doc:`examples/swan-workflow` tutorial
4. Explore the :doc:`user-guide/cli-reference`

Support
-------

If you continue to experience installation issues:

* Check the `GitHub Issues <https://github.com/rom-py/rompy-oceanum/issues>`_
* Review the :doc:`user-guide/troubleshooting` guide
* Contact the development team through GitHub
