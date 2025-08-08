# rompy-oceanum Documentation

This directory contains the complete documentation for rompy-oceanum, built with [Sphinx](https://www.sphinx-doc.org/) and automatically deployed to [GitHub Pages](https://rom-py.github.io/rompy-oceanum/). rompy-oceanum provides seamless integration with the oceanum CLI as the `oceanum rompy` command group.

📖 **[View Documentation Online](https://rom-py.github.io/rompy-oceanum/)**

## 📚 Documentation Structure

```
docs/
├── source/               # Source files for documentation
│   ├── _static/         # Static assets (CSS, images, etc.)
│   ├── _templates/      # Custom Sphinx templates
│   ├── user-guide/      # User guides and tutorials
│   ├── examples/        # Practical examples
│   ├── development/     # Development documentation
│   ├── api/            # Auto-generated API documentation
│   ├── conf.py         # Sphinx configuration
│   └── index.rst       # Main documentation index
├── build/              # Generated documentation (HTML, PDF, etc.)
├── Makefile           # Build commands for Unix/Linux/macOS
├── make.bat           # Build commands for Windows
└── README.md          # This file
```

## 🚀 Quick Start

### Prerequisites

1. **Python 3.8+** with rompy-oceanum and oceanum CLI installed
2. **Documentation dependencies** installed:

```bash
# Install with documentation dependencies
pip install -e ".[docs]"

# Verify oceanum CLI integration
oceanum rompy --help
```

### Building Documentation

**On Unix/Linux/macOS:**
```bash
cd docs
make html
```

**On Windows:**
```cmd
cd docs
make.bat html
```

The built documentation will be available in `docs/build/html/index.html`.

## 🛠️ Development Workflow

### Live Reload Development

For active documentation development with automatic rebuilding:

```bash
# Install development dependencies
make setup-dev

# Start live reload server (Unix/Linux/macOS)
make livehtml

# Or manually
sphinx-autobuild source build/html --host 0.0.0.0 --port 8000 --watch ../rompy_oceanum
```

Visit `http://localhost:8000` to see your documentation with live updates.

### Available Build Commands

| Command | Description |
|---------|-------------|
| `make html` | Build HTML documentation |
| `make dev` | Quick development build |
| `make strict` | Build with warnings as errors |
| `make clean` | Remove all build artifacts |
| `make linkcheck` | Check for broken links |
| `make install` | Install documentation dependencies |
| `make livehtml` | Start live reload server |
| `make setup-dev` | Setup development environment |

### CLI Integration Testing

Verify the oceanum CLI integration works:

```bash
# Test oceanum CLI plugin loading
oceanum rompy --help

# Test authentication
oceanum auth login
oceanum auth status
```

### Quality Checks

Before submitting documentation changes:

```bash
# Check for warnings and errors
make strict

# Verify all links work
make linkcheck

# Clean build to ensure no artifacts
make clean && make html
```

## 📝 Writing Documentation

### File Formats

- **reStructuredText (.rst)**: Primary format for structured documentation
- **Markdown (.md)**: Supported via MyST parser for simple content
- **Python docstrings**: Auto-extracted for API documentation

### Style Guidelines

1. **Headers**: Use consistent header hierarchy
   ```rst
   Main Title
   ==========
   
   Section
   -------
   
   Subsection
   ~~~~~~~~~~
   ```

2. **Code Blocks**: Always specify language
   ```rst
   .. code-block:: python
   
      import rompy_oceanum
   
   .. code-block:: bash
   
      oceanum rompy init swan --template basic
   ```

3. **Cross-references**: Use Sphinx roles for internal links
   ```rst
   See :doc:`user-guide/basic-usage` for details.
   Reference :class:`rompy_oceanum.PraxClient` class.
   ```

4. **Admonitions**: Use for important information
   ```rst
   .. note::
      This is important information.
   
   .. warning::
      Be careful with this operation.
   ```

### Documentation Sections

#### User Guide (`user-guide/`)
- Getting started tutorials with oceanum CLI integration
- Configuration guides and template usage
- CLI reference for `oceanum rompy` commands
- Common usage patterns and workflows
- Troubleshooting

#### Examples (`examples/`)
- Complete workflow examples using oceanum CLI
- CLI and programmatic code snippets
- Real-world use cases and automation patterns

#### API Reference (`api/`)
- Auto-generated from docstrings
- Comprehensive class and function documentation
- Usage examples in docstrings

#### Development (`development/`)
- Architecture documentation
- Contributing guidelines
- Testing procedures
- Migration guides

## 🎨 Themes and Styling

### Current Theme
- **Primary**: Sphinx RTD Theme with custom enhancements
- **Features**: Responsive design, dark/light mode, search, navigation

### Custom Styling
- Custom CSS in `source/_static/custom.css`
- Enhanced code highlighting
- Improved admonitions and grids
- Responsive design elements

### Extensions Used

| Extension | Purpose |
|-----------|---------|
| `sphinx.ext.autodoc` | Extract docstrings |
| `sphinx.ext.napoleon` | Google/NumPy style docstrings |
| `sphinx_autoapi` | Automatic API documentation |
| `myst_parser` | Markdown support |
| `sphinx_copybutton` | Copy code blocks |
| `sphinx_design` | Grid layouts and cards |
| `sphinxext.opengraph` | Social media previews |

## 📊 Analytics and Metrics

### Documentation Metrics
- Build time and success rate
- Link validation results
- Search analytics (when deployed)
- User feedback integration

### Performance Optimization
- Optimized image sizes
- Efficient Sphinx extensions
- Minimal JavaScript/CSS overhead
- Fast search indexing

## 🚀 Deployment

### GitHub Pages (Automatic)
Documentation is automatically built and deployed to GitHub Pages:

- **URL**: https://rom-py.github.io/rompy-oceanum/
- **Trigger**: Every push to `main` or `master` branch
- **Workflow**: `.github/workflows/docs.yml`
- **Status**: Check the "Actions" tab in the repository

### Local Testing Before Deployment

```bash
# Test the exact build that will be deployed
make clean && make html

# Check for warnings (these will fail the CI)
make html 2>&1 | grep -i warning

# View locally (same as GitHub Pages will show)
python -m http.server 8000 --directory build/html
# Visit http://localhost:8000
```

### Manual Deployment (Alternative)
For custom deployment to other hosting services:

```bash
# Build production documentation
make clean && make html

# Deploy to web server
rsync -av build/html/ user@server:/var/www/docs/
```

## 🔧 Troubleshooting

### Common Issues

1. **Build Failures**
   ```bash
   # Check for syntax errors
   make strict
   
   # Clear cache and rebuild
   make clean && make html
   ```

2. **Missing Dependencies**
   ```bash
   # Reinstall all dependencies
   pip install -e ".[docs]" --force-reinstall
   ```

3. **Import Errors in API Docs**
   ```bash
   # Ensure rompy-oceanum is installed in development mode
   pip install -e .
   pip install oceanum
   ```

4. **CLI Plugin Not Loading**
   ```bash
   # Verify oceanum CLI can find the plugin
   oceanum --help  # Should show 'rompy' in command list
   
   # Reinstall if needed
   pip install --force-reinstall rompy-oceanum
   ```

5. **GitHub Pages Deployment Issues**
   ```bash
   # Check workflow status
   # Go to: https://github.com/oceanum/rompy-oceanum/actions
   
   # Test locally with same build process
   cd docs && make clean && make html
   
   # Ensure no warnings (they fail CI)
   make html 2>&1 | grep -c WARNING  # Should return 0
   ```

6. **Live Reload Not Working**
   ```bash
   # Install sphinx-autobuild
   pip install sphinx-autobuild
   
   # Check file permissions and firewall settings
   ```

### Getting Help

- **Live Documentation**: https://rom-py.github.io/rompy-oceanum/
- **GitHub Actions Logs**: https://github.com/oceanum/rompy-oceanum/actions
- **Sphinx Documentation**: https://www.sphinx-doc.org/
- **reStructuredText Guide**: https://docutils.sourceforge.io/rst.html
- **MyST Parser**: https://myst-parser.readthedocs.io/
- **Project Issues**: https://github.com/oceanum/rompy-oceanum/issues

## 📋 Contributing

### Documentation Contributions

1. **Fork and Clone**: Standard GitHub workflow
2. **Create Branch**: `git checkout -b docs/your-feature`
3. **Make Changes**: Edit documentation files
4. **Test Locally**: `make dev` and review changes
5. **Submit PR**: With clear description of changes

### Content Guidelines

- **Accuracy**: Ensure all code examples work
- **Clarity**: Write for your intended audience
- **Completeness**: Cover all important use cases
- **Consistency**: Follow established patterns
- **Currency**: Keep information up to date

### Review Process

1. **Automated Checks**: CI/CD validation
2. **Peer Review**: Technical accuracy review
3. **User Testing**: Validate with actual users
4. **Final Approval**: Maintainer sign-off

## 📚 Resources

### Learning Materials
- [Sphinx Tutorial](https://www.sphinx-doc.org/en/master/tutorial/)
- [reStructuredText Primer](https://www.sphinx-doc.org/en/master/usage/restructuredtext/basics.html)
- [Documentation Best Practices](https://docs.python-guide.org/writing/documentation/)

### Tools and Extensions
- [Sphinx Extensions](https://www.sphinx-doc.org/en/master/usage/extensions/index.html)
- [Read the Docs](https://readthedocs.org/)
- [Documentation Testing](https://github.com/sphinx-doc/sphinx/blob/master/doc/usage/advanced/testing.rst)

---

**Happy documenting!** 📖✨

For questions about the documentation system, please open an issue or contact the development team.