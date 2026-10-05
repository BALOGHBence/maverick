# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

import os
import sys
from datetime import date

from docutils import nodes
from sphinx.application import Sphinx

sys.path.insert(0, os.path.abspath("../../src"))

import maverick as library

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = library.__pkg_name__
_first_year, _this_year = 2026, date.today().year
_years = (
    str(_first_year) if _this_year == _first_year else f"{_first_year}-{_this_year}"
)
project_copyright = f"{_years}, Bence Balogh"
author = "Bence Balogh"


def _md_visit_classifier(self, node: nodes.classifier) -> None:
    self.add(" : ")


def _md_depart_classifier(self, node: nodes.classifier) -> None:
    pass


def _md_admonition_handlers(title: str) -> tuple:
    def visit(self, node: nodes.Admonition) -> None:
        self._push_box(title)

    def depart(self, node: nodes.Admonition) -> None:
        self._pop_context(node)

    return visit, depart


def setup(app: Sphinx):
    app.add_config_value("project_name", project, "html")

    # Teach the Markdown builder used by sphinx_llm the nodes it does not
    # support out of the box, otherwise their content is dropped.
    md_builder = "llms-markdown"
    app.add_node(
        nodes.classifier,
        override=True,
        **{md_builder: (_md_visit_classifier, _md_depart_classifier)},
    )
    for node_cls, title in [
        (nodes.tip, "TIP"),
        (nodes.danger, "DANGER"),
        (nodes.caution, "CAUTION"),
        (nodes.error, "ERROR"),
    ]:
        app.add_node(
            node_cls, override=True, **{md_builder: _md_admonition_handlers(title)}
        )


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
    
    # LLM-powered content generation
    # https://github.com/NVIDIA/sphinx-llm
    "sphinx_llm.txt",
]

_docs_base_url = "https://pymaverick.readthedocs.io/en/latest/"

# Without this, sphinx_llm falls back to the package metadata, i.e. the README.
llms_txt_description = (
    "Maverick is a Python library for simulating poker games with custom player "
    "strategies. It provides a complete poker game loop (dealing, betting rounds, "
    "showdown, pot distribution), a composable player interface and an event "
    "stream for building, testing and benchmarking poker bots.\n"
    "\n"
    "How to read this file:\n"
    "\n"
    "- Every link below points to a Markdown version of a documentation page.\n"
    "- Links are relative URLs, resolved against the directory that contains "
    "the llms.txt file you are reading.\n"
    "- Fetch the linked `.html.md` files directly; they contain the full page "
    "content as Markdown.\n"
    "- If you are reading a local copy, resolve the links against its directory "
    "on disk the same way.\n"
    "\n"
    f"Examples for the top-level index at {_docs_base_url}llms.txt:\n"
    "\n"
    "- `[Overview](overview.html.md)` resolves to "
    f"{_docs_base_url}overview.html.md\n"
    "- `[User Guide](user_guide/index.html.md)` resolves to "
    f"{_docs_base_url}user_guide/index.html.md\n"
    "- `[Configuring and Running Games](user_guide/games.html.md)` resolves to "
    f"{_docs_base_url}user_guide/games.html.md\n"
    "\n"
    "Each subdirectory also has its own index (for example "
    f"{_docs_base_url}user_guide/llms.txt) whose links are relative to that "
    "subdirectory, so the same page is linked there as `games.html.md`."
)

# Nodes with no meaningful Markdown representation: <meta> tags and the
# abbreviation used for the keyword-only "*" marker in signatures.
llms_txt_suppress_unknown_node_warnings = ["meta", "abbreviation"]

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
html_js_files = ["js/download_md.js"]

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
}

# Intersphinx configuration
intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "pydantic": ("https://docs.pydantic.dev/latest/", None),
}
