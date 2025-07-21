Testing
=======

.. note::
   This section is under development. Detailed testing guidelines will be added in a future release.

Overview
--------

rompy-oceanum follows testing best practices to ensure reliability and maintainability. The testing strategy includes unit tests, integration tests, and end-to-end workflow validation.

Test Structure
--------------

The test suite is organized as follows:

.. code-block:: text

   tests/
   ├── unit/           # Unit tests for individual components
   ├── integration/    # Integration tests with external services
   ├── fixtures/       # Test data and configuration files
   └── conftest.py     # Pytest configuration and shared fixtures

Running Tests
-------------

.. code-block:: bash

   # Run all tests
   pytest

   # Run with coverage
   pytest --cov=rompy_oceanum

   # Run specific test categories
   pytest tests/unit/
   pytest tests/integration/

   # Run tests matching a pattern
   pytest -k "test_prax"

Test Categories
---------------

This section will cover:

* **Unit Tests**: Testing individual functions and classes in isolation
* **Integration Tests**: Testing interactions with Prax API and external services
* **Configuration Tests**: Validating configuration parsing and validation
* **CLI Tests**: Testing command-line interface functionality
* **Backend Tests**: Testing pipeline backend implementations

Testing Guidelines
------------------

When contributing tests:

1. Follow pytest conventions and best practices
2. Use descriptive test names that explain what is being tested
3. Include both positive and negative test cases
4. Mock external dependencies appropriately
5. Ensure tests are deterministic and can run in any order

.. todo::
   Add detailed testing guidelines, mock strategies, and test data management documentation.

For now, please refer to:

* The existing test suite in the tests/ directory
* :doc:`contributing` - Development setup and contribution guidelines
* `pytest documentation <https://docs.pytest.org/>`_ - Testing framework reference

See Also
--------

* :doc:`contributing` - Development guidelines
* :doc:`architecture` - System architecture
* :doc:`../user-guide/troubleshooting` - Debugging and troubleshooting
