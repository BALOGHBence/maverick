# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

import os
import sys
from datetime import date

from sphinx.config import Config

sys.path.insert(0, os.path.abspath("../../src"))

import maverick as library

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = library.__pkg_name__
copyright = "2026-%s, Bence Balogh" % date.today().year
author = "Bence Balogh"


def setup(app: Config):
    app.add_config_value("project_name", project, "html")


# The short X.Y version.
version = library.__version__
# The full version, including alpha/beta/rc tags.
release = "v" + library.__version__

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "myst_nb",
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.intersphinx",
    "sphinx.ext.viewcode",
    "sphinx.ext.autosummary",
    "sphinx_copybutton",
]

source_suffix = {
    ".rst": "restructuredtext",
    ".md": "myst-nb",
    ".ipynb": "myst-nb",
}

templates_path = ["_templates"]
exclude_patterns = []

language = "en"

# Napoleon settings for NumPy-style docstrings
napoleon_google_docstring = False
napoleon_numpy_docstring = True
napoleon_include_init_with_doc = True
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

# Autodoc settings
autodoc_default_options = {
    "members": True,
    "member-order": "bysource",
    "exclude-members": "__weakref__",
    "imported-members": False,
    "inherited-members": False,
}

# MyST settings
myst_enable_extensions = [
    "colon_fence",
    "deflist",
    "linkify",
]

# -- Options for Notebooks

# Notebook execution behavior:
# - "off" = never execute during build (fastest, most reproducible)
# - "auto" = execute if no outputs are stored
# - "force" = always execute
nb_execution_mode = "off"

# Optional: fail the build if a notebook would error when executed
nb_execution_raise_on_error = True

# Optional: where execution happens (keeps build folder clean)
nb_execution_in_temp = True

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_static_path = ["_static"]
html_css_files = ["css/custom.css"]

html_theme = "sphinx_book_theme"

html_theme_options = {
    "show_navbar_depth": 2,
    "toc_title": "On this page",
    "show_toc_level": 2,
    "repository_url": "https://github.com/BALOGHBence/maverick",
    "use_repository_button": True,
    "use_issues_button": True,
    "use_download_button": True,
    "use_fullscreen_button": True,
    "logo": {
      "image_light": "_static/img/logo-maverick-light.svg",
      "image_dark": "_static/img/logo-maverick-dark.svg",
    },
    "extra_footer": "<div>hi there!</div>"
}

# Intersphinx configuration
intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "pydantic": ("https://docs.pydantic.dev/latest/", None),
}
