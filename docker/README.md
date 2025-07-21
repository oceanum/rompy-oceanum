# Docker Images and CI/CD for Rompy-Oceanum

This directory contains Docker configurations and GitHub Actions workflows for building and testing Docker images for the rompy-oceanum project.

## Docker Images

### 1. SWAN Image (`swan.Dockerfile`)

A Docker image containing the SWAN wave model with all necessary dependencies.

**Features:**
- Ubuntu 20.04 base
- SWAN version 4141
- NetCDF support
- MPI support  
- Fortran compiler
- Built with CMake and Ninja

**Usage:**
```bash
docker build -t rompy-oceanum/swan:latest -f docker/swan.Dockerfile .
docker run --rm rompy-oceanum/swan:latest swan.exe --help
```

### 2. Rompy Image (`rompy.Dockerfile`)

A Docker image containing Python with rompy, rompy-oceanum, and oceanum packages.

**Features:**
- Python 3.12 slim base
- Pre-installed rompy and oceanum packages
- rompy-oceanum plugin from local source
- CLI tools available

**Usage:**
```bash
docker build -t rompy-oceanum/rompy:latest -f docker/rompy.Dockerfile .
docker run --rm rompy-oceanum/rompy:latest python -c "import rompy_oceanum"
docker run --rm rompy-oceanum/rompy:latest rompy-oceanum --help
```

## GitHub Actions Workflows

### 1. Main Build Workflow (`docker-build.yml`)

**Triggers:**
- Push to main/master/develop branches (when Docker-related files change)
- Pull requests (when Docker-related files change)
- Releases
- Manual workflow dispatch

**Features:**
- Smart change detection (only builds images when relevant files change)
- Multi-platform builds (linux/amd64, linux/arm64)
- Pushes to GitHub Container Registry
- Security scanning with Trivy
- Comprehensive testing
- Semantic versioning for releases

**Image Tags:**
- `latest` (main/master branch)
- `<branch-name>` (feature branches)
- `pr-<number>` (pull requests)
- `<version>` (releases)
- `<image>-<date>-<sha>` (all builds)

### 2. Development Testing Workflow (`docker-test.yml`)

**Triggers:**
- Push/PR to main/master/develop branches
- Manual workflow dispatch

**Features:**
- Dockerfile linting with hadolint
- Quick build tests (single platform)
- Integration testing
- Plugin verification
- Performance analysis
- Vulnerability scanning

**Purpose:**
- Fast feedback for development
- Comprehensive testing without pushing images
- Performance and security analysis

### 3. Local Development Workflow (`docker-local.yml`)

**Triggers:**
- Manual workflow dispatch only

**Features:**
- Build specific images with custom tags
- Save images as downloadable artifacts
- Local development focused
- No registry authentication required

**Usage:**
1. Go to Actions tab in GitHub
2. Select "Local Docker Development"
3. Click "Run workflow"
4. Choose image(s) and tag
5. Download artifacts after build completes

## Registry and Image Names

Images are pushed to GitHub Container Registry:

- **SWAN:** `ghcr.io/<owner>/<repo>/swan`
- **Rompy:** `ghcr.io/<owner>/<repo>/rompy`

## Development Workflow

### For Contributors

1. **Make changes** to Dockerfiles or related code
2. **Create PR** - triggers automated testing
3. **Review results** - check Docker test workflow results
4. **Merge** - triggers build and push to registry

### For Local Development

1. **Use local workflow** for quick image builds
2. **Download artifacts** from workflow runs
3. **Load images** locally:
   ```bash
   docker load < swan-dev.tar.gz
   docker load < rompy-dev.tar.gz
   ```

### For Testing

```bash
# Build both images locally
docker build -t test-swan -f docker/swan.Dockerfile .
docker build -t test-rompy -f docker/rompy.Dockerfile .

# Test SWAN
docker run --rm test-swan swan.exe --help

# Test Rompy
docker run --rm test-rompy python -c "import rompy_oceanum"
docker run --rm test-rompy rompy-oceanum --help

# Test plugin integration
docker run --rm test-rompy python -c "
from rompy_oceanum.pipeline import PraxPipelineBackend
print('Plugin loaded successfully')
"
```

## Configuration

### Environment Variables

The workflows support several environment variables:

- `REGISTRY`: Container registry (default: `ghcr.io`)
- `IMAGE_NAME`: Base image name (auto-detected from repo)

### Secrets Required

- `GITHUB_TOKEN`: Automatically provided for registry access

### Manual Triggers

All workflows support manual triggering via workflow dispatch:

1. Go to repository Actions tab
2. Select desired workflow
3. Click "Run workflow" 
4. Adjust parameters as needed

## Troubleshooting

### Build Failures

1. **Check logs** in GitHub Actions
2. **Verify Dockerfile syntax** locally
3. **Test builds locally** before pushing
4. **Check dependency versions** in pyproject.toml

### Image Size Issues

- Review layer sizes in workflow output
- Consider multi-stage builds for optimization
- Use `.dockerignore` to exclude unnecessary files

### Security Vulnerabilities

- Check Trivy scan results in Security tab
- Update base images and dependencies
- Review vulnerability reports

### Plugin Issues

- Verify entry points in pyproject.toml
- Test plugin loading in container
- Check import paths and dependencies

## Best Practices

### Dockerfile Best Practices

- Use specific version tags for base images
- Minimize layers and image size
- Use multi-stage builds when beneficial
- Add health checks where appropriate
- Follow security best practices

### Development Best Practices

- Test locally before pushing
- Use the development workflow for iteration
- Review security scan results
- Monitor image sizes
- Keep dependencies updated

### CI/CD Best Practices

- Let automated testing complete before manual testing
- Use semantic versioning for releases
- Monitor build times and optimize as needed
- Review and update workflows regularly

## Support

For issues with Docker builds or workflows:

1. Check existing GitHub Issues
2. Review workflow logs for error details
3. Test locally to isolate the problem
4. Create detailed issue reports with logs and context