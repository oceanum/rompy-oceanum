# Installation

## Prerequisites

Before installing `rompy-oceanum`, you need to have:

1. Python 3.8 or higher
2. The `rompy` package installed
3. A Prax account with Oceanum

## Standard Installation

You can install the package directly from PyPI:

```bash
pip install rompy-oceanum
```

## Development Installation

For development, you can install the package in editable mode:

```bash
git clone https://github.com/oceanum/rompy-oceanum.git
cd rompy-oceanum
pip install -e .
```

## Authentication

To use this package, you need to set your Prax API token. You can do this by setting the `PRAX_TOKEN` environment variable:

```bash
export PRAX_TOKEN="your_token_here"
```

You can also set other environment variables for convenience:

```bash
export PRAX_USER="your_username"
export PRAX_ORG="your_organization"
export PRAX_PROJECT="your_project"
```

If you don't set these environment variables, you'll need to provide them as parameters when calling methods.
