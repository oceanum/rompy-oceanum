# Minimal makefile for Sphinx documentation
#

# You can set these variables from the command line, and also
# from the environment for the first two.
SPHINXOPTS    ?=
SPHINXBUILD  ?= sphinx-build
SOURCEDIR    = source
BUILDDIR     = build

# Put it first so that "make" without argument is like "make help".
help:
	@$(SPHINXBUILD) -M help "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

.PHONY: help Makefile

# Catch-all target: route all unknown targets to Sphinx-build using the new
# "make mode" option.  $(O) is meant as a shortcut for $(SPHINXOPTS).
%: Makefile
	@$(SPHINXBUILD) -M $@ "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

# Custom targets for development
clean:
	@echo "Removing everything under '$(BUILDDIR)'"
	@rm -rf $(BUILDDIR)/*

install:
	@echo "Installing documentation dependencies..."
	@pip install -e ".[docs]"

livehtml:
	@echo "Starting live reload server..."
	@sphinx-autobuild "$(SOURCEDIR)" "$(BUILDDIR)/html" $(SPHINXOPTS) $(O) \
		--host 0.0.0.0 \
		--port 8000 \
		--watch ../rompy_oceanum \
		--ignore "*.pyc" \
		--ignore "*~" \
		--ignore "*.swp" \
		--ignore "*.swo"

# Build documentation with warnings as errors
strict:
	@$(SPHINXBUILD) -W -b html "$(SOURCEDIR)" "$(BUILDDIR)/html" $(SPHINXOPTS) $(O)

# Quick development build
dev:
	@$(SPHINXBUILD) -b html "$(SOURCEDIR)" "$(BUILDDIR)/html" $(SPHINXOPTS) $(O)
	@echo "Build finished. The HTML pages are in $(BUILDDIR)/html."

# Check for broken links
linkcheck:
	@$(SPHINXBUILD) -b linkcheck "$(SOURCEDIR)" "$(BUILDDIR)/linkcheck" $(SPHINXOPTS) $(O)

# Build all formats
all: html epub latexpdf

# Setup development environment
setup-dev:
	@echo "Setting up development environment for documentation..."
	@pip install -e ".[docs]"
	@pip install sphinx-autobuild
	@echo "Setup complete. Run 'make livehtml' for live reload development."
