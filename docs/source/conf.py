# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

import os
import sys
from pathlib import Path

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
sys.path.insert(0, os.path.abspath('../../'))

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'rompy-oceanum'
copyright = '2025, rompy-oceanum contributors'
author = 'rompy-oceanum contributors'
release = '0.1.0'
version = '0.1.0'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.autosummary',
    'sphinx.ext.viewcode',
    'sphinx.ext.napoleon',
    'sphinx.ext.intersphinx',
    'sphinx.ext.githubpages',
    'sphinx_autodoc_typehints',
    'myst_parser',
    'sphinx_copybutton',
    'sphinxext.opengraph',
    'sphinx_design',
]

templates_path = ['_templates']
exclude_patterns = []

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']

# Logo configuration - using the real banner_light.svg logo
html_logo = '_static/banner_light.svg'
html_favicon = '_static/banner_light.svg'

# Theme options
html_theme_options = {
    'canonical_url': '',
    'analytics_id': '',
    'logo_only': False,
    'prev_next_buttons_location': 'bottom',
    'style_external_links': False,
    'vcs_pageview_mode': '',
    'style_nav_header_background': '#0d2d3f',
    # Toc options
    'collapse_navigation': True,
    'sticky_navigation': True,
    'navigation_depth': 4,
    'includehidden': True,
    'titles_only': False
}

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ['_static']

# GitHub Pages configuration
html_baseurl = 'https://rom-py.github.io/rompy-oceanum/'
html_extra_path = ['.nojekyll']

# HTML title and other options
html_title = f"{project} v{version}"
html_short_title = project

# Ensure assets work correctly on GitHub Pages
html_css_files = []
html_js_files = []

# -- Extension configuration -------------------------------------------------

# MyST Parser configuration
myst_enable_extensions = [
    "colon_fence",
    "deflist",
    "dollarmath",
    "html_admonition",
    "html_image",
    "linkify",
    "replacements",
    "smartquotes",
    "substitution",
    "tasklist",
]

# Custom directive for mermaid diagrams
rst_prolog = """
.. |mermaid| replace:: **Diagram**
"""

# Autodoc configuration
autodoc_default_options = {
    'members': True,
    'member-order': 'bysource',
    'special-members': '__init__',
    'undoc-members': True,
    'exclude-members': '__weakref__'
}

autodoc_typehints = 'description'
autodoc_typehints_description_target = 'documented'

# AutoAPI configuration disabled to prevent duplicate documentation issues
# autoapi_dirs = ['../../rompy_oceanum']
# autoapi_type = 'python'
# autoapi_template_dir = '_templates/autoapi'
# autoapi_options = [
#     'members',
#     'undoc-members',
#     'show-inheritance',
#     'show-module-summary',
# ]
# autoapi_python_class_content = 'both'
# autoapi_member_order = 'groupwise'
# autoapi_root = 'api'
# autoapi_ignore = ['**/cli/**']
# autoapi_add_toctree_entry = False

# Napoleon settings for Google/NumPy style docstrings
napoleon_google_docstring = True
napoleon_numpy_docstring = True
napoleon_include_init_with_doc = False
napoleon_include_private_with_doc = False
napoleon_include_special_with_doc = True
napoleon_use_admonition_for_examples = False
napoleon_use_admonition_for_notes = False
napoleon_use_admonition_for_references = False
napoleon_use_ivar = False
napoleon_use_param = True
napoleon_use_rtype = True
napoleon_preprocess_types = False
napoleon_type_aliases = None
napoleon_attr_annotations = True

# Intersphinx mapping
intersphinx_mapping = {
    'python': ('https://docs.python.org/3/', None),
    'pydantic': ('https://docs.pydantic.dev/latest/', None),
    'requests': ('https://requests.readthedocs.io/en/latest/', None),
    'rompy': ('https://rompy.readthedocs.io/en/latest/', None),
}

# Copy button configuration
copybutton_prompt_text = r">>> |\.\.\. |\$ |In \[\d*\]: | {2,5}\.\.\.: | {5,8}: "
copybutton_prompt_is_regexp = True

# OpenGraph configuration
ogp_site_url = "https://rom-py.github.io/rompy-oceanum/"
ogp_site_name = "rompy-oceanum"
ogp_image = "https://rom-py.github.io/rompy-oceanum/_static/banner_light.svg"

# -- Custom configuration ---------------------------------------------------

# Custom CSS
def setup(app):
    """Setup function to add custom CSS."""
    app.add_css_file('custom.css')

# Source file suffixes
source_suffix = {
    '.rst': None,
    '.md': 'myst_parser',
}

# Master document
master_doc = 'index'

# Language
language = 'en'

# Add numbered figures and tables
numfig = True
numfig_format = {
    'figure': 'Figure %s',
    'table': 'Table %s',
    'code-block': 'Listing %s',
    'section': 'Section %s',
}

# Suppress warnings
suppress_warnings = [
    'toc.not_readable',
    'ref.not_found',
    'docutils'
]

# GitHub Pages specific configuration
html_copy_source = False
html_show_sourcelink = False

# Ensure proper URL generation for GitHub Pages
if os.environ.get('GITHUB_ACTIONS'):
    html_baseurl = 'https://rom-py.github.io/rompy-oceanum/'
