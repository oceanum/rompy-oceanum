# rompy-oceanum

A rompy plugin that provides Prax pipeline backend integration for executing models on Oceanum's platform using rompy's plugin architecture.

## Installation

```bash
pip install rompy-oceanum
```

## Features

- **Pipeline Backend**: Execute rompy models on Oceanum's Prax platform
- **Runtime Configuration**: Backend selection at execution time, not model configuration time
- **Monitoring & Management**: Pipeline status monitoring, log retrieval, and output management
- **DataMesh Integration**: Optional postprocessor for registering outputs with DataMesh
- **CLI Tools**: Command-line interface for pipeline operations

## Usage

### Basic Pipeline Execution

```python
import rompy
from rompy_oceanum.config import PraxConfig

# Create a rompy model configuration as usual
model_run = rompy.ModelRun(
    config=swan_config,
    output_dir="./outputs",
    run_id="my-run"
)

# Execute using Prax pipeline backend
result = model_run.pipeline(
    backend="prax",
    pipeline_name="swan-from-rompy",
    wait_for_completion=True,
    download_outputs=True
)

# Check results
if result["success"]:
    print(f"Pipeline completed! Run ID: {result['prax_run_id']}")
    print(f"Downloaded files: {result.get('downloaded_files', [])}")
```

### Explicit Configuration

```python
from rompy_oceanum.config import PraxConfig, DataMeshConfig

# Create explicit configurations
prax_config = PraxConfig(
    base_url="https://prax.oceanum.io",
    token="your-token",
    org="your-org",
    project="your-project",
    stage="dev"
)

datamesh_config = DataMeshConfig(
    base_url="https://datamesh.oceanum.io",
    token="your-datamesh-token"
)

# Execute with explicit config
result = model_run.pipeline(
    backend="prax",
    pipeline_name="swan-from-rompy",
    prax_config=prax_config,
    datamesh_config=datamesh_config,
    deploy_pipeline=True,
    wait_for_completion=True,
    download_outputs=True
)
```

### Direct Client Usage

```python
from rompy_oceanum.client import PraxClient
from rompy_oceanum.config import PraxConfig

# Create client for direct API access
config = PraxConfig.from_env()
client = PraxClient(config)

# Check pipeline status
status = client.get_run_status("run-id")

# Get logs
logs = client.get_run_logs("run-id", tail=100)

# Download outputs
client.download_run_artifacts("run-id", "./outputs")
```

### Command Line Interface

```bash
# Submit a pipeline
rompy-oceanum run swan config.yml --pipeline-name swan-from-rompy --wait --download

# Monitor pipeline
rompy-oceanum status <run-id>

# Get logs
rompy-oceanum logs <run-id> --tail 50

# Download outputs
rompy-oceanum download <run-id> ./outputs
```

## Backend Configuration

### Using rompy CLI with Backend Configurations

The updated rompy backend system supports three execution scenarios:

```bash
# Generate Docker backend for local testing (spawns containers)
rompy-oceanum generate-backend-config swan --backend-type docker --cpu 4 --memory 2G

# Generate Local backend for native execution (no containers)
rompy-oceanum generate-backend-config swan --backend-type local --mpi-procs 2

# Generate Prax backend for pipeline containers (local execution inside container)
rompy-oceanum generate-backend-config swan --backend-type prax --mpi-procs 2
```

### Backend Configuration Files

Create backend configuration files for different execution scenarios:

#### Docker Backend (Local Testing)
**Purpose**: Spawns Docker containers for execution - good for local development/testing

```yaml
# backend_config_swan_docker.yaml
backend:
  type: docker
  image: "us-central1-docker.pkg.dev/oceanum-prod/oceanum-public/swan:latest"
  timeout: 3600
  cpu: 4
  memory: "2G"
  mpiexec: "mpirun -n 2"
  user: "root"
  env_vars:
    OMPI_ALLOW_RUN_AS_ROOT: "1"
    OMPI_ALLOW_RUN_AS_ROOT_CONFIRM: "1"
    OMP_NUM_THREADS: "2"
    ROMPY_MODEL: "swan"
  remove_container: true
```

#### Prax Backend (Pipeline Containers)
**Purpose**: Runs within Prax pipeline containers using local backend (no nested containers)

```yaml
# backend_config_swan_prax.yaml
backend:
  type: local  # Uses local backend inside the container
  timeout: 3600
  command: "mpirun -n 2 /usr/local/bin/swan.exe"
  shell: true
  capture_output: true
  working_dir: "/app"
  env_vars:
    OMPI_ALLOW_RUN_AS_ROOT: "1"
    OMPI_ALLOW_RUN_AS_ROOT_CONFIRM: "1"
    OMP_NUM_THREADS: "2"
    ROMPY_MODEL: "swan"
```

### Pipeline Template Integration

The SWAN pipeline template uses local backend within containers (correct for Prax):

```yaml
# Updated pipeline tasks
tasks:
  - name: generate
    image: "us-central1-docker.pkg.dev/oceanum-prod/oceanum-public/rompy:latest"
    command: rompy generate --config-from-env -v
    
  - name: run
    image: "us-central1-docker.pkg.dev/oceanum-prod/oceanum-public/swan:latest"
    command: rompy run --config-from-env --run-backend local -v
    
  - name: postprocess
    image: "us-central1-docker.pkg.dev/oceanum-prod/oceanum-public/rompy:latest"
    command: rompy postprocess --config-from-env --processor datamesh -v
```

### Available Backend Types

1. **Local Backend** - Execute natively or within containers
```yaml
type: local
command: "mpirun -n 2 swan.exe"  # or "/usr/local/bin/swan.exe" for containers
shell: true
capture_output: true
working_dir: "/app"  # for container execution
env_vars:
  OMP_NUM_THREADS: "2"
  OMPI_ALLOW_RUN_AS_ROOT: "1"  # for container execution
```

2. **Docker Backend** - Spawn Docker containers for execution
```yaml
type: docker
image: "swan:latest"
cpu: 4
memory: "2G"
mpiexec: "mpirun -n 2"
executable: "/usr/local/bin/swan.exe"
```

### Backend Selection Guide

- **Docker Backend**: For local testing (spawns containers)
- **Local Backend**: For native execution OR execution within Prax pipeline containers
- **Prax Backend**: Special case of local backend configured for container paths

## Configuration

### Environment Variables

Set up your Prax credentials and configuration:

```bash
export PRAX_TOKEN="your_prax_token"
export PRAX_ORG="your_organization"
export PRAX_PROJECT="your_project"
export PRAX_BASE_URL="https://prax.oceanum.io"  # Optional
export PRAX_STAGE="dev"  # Optional, defaults to "dev"
```

For DataMesh integration:

```bash
export DATAMESH_TOKEN="your_datamesh_token"
export DATAMESH_BASE_URL="https://datamesh.oceanum.io"  # Optional
```

### Configuration Files

You can also provide configuration explicitly in your code:

```python
from rompy_oceanum.config import PraxConfig

config = PraxConfig(
    base_url="https://prax.oceanum.io",
    token="your-token",
    org="your-org",
    project="your-project",
    stage="dev"
)
```

## Architecture

This package implements rompy's plugin architecture:

- **Pipeline Backend**: Registered as `rompy.pipeline` entry point
- **Postprocessor**: DataMesh integration via `rompy.postprocess` entry point
- **Runtime Selection**: Backends chosen at execution time, not configuration time
- **Separation of Concerns**: Model configuration separate from execution configuration

## Migration

If you're upgrading from the legacy `OceanumModelRun` approach, see [MIGRATION.md](./MIGRATION.md) for a complete migration guide.

## Examples

See the [examples directory](./examples/) for comprehensive usage examples:

- `prax_backend_example.py`: Complete examples showing all features
- Template files for common pipeline configurations

## Documentation

For more detailed documentation, see the [docs](./docs) directory.

## License

MIT
