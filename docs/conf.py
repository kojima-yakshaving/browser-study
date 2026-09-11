from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.abspath(".."))

project = "Gorushi"
copyright = "2026, malkoG"
author = "malkoG"

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    "sphinx.ext.intersphinx",
    "sphinx_autodoc_typehints",
    "myst_parser",
]

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

# -- autodoc --------------------------------------------------------------
# Interfaces are documented from signatures/type hints even before
# docstrings are written, so undocumented members still show up.
autodoc_default_options = {
    "members": True,
    "undoc-members": True,
    "show-inheritance": True,
}
autodoc_typehints = "description"
autodoc_member_order = "bysource"
napoleon_google_docstring = True
napoleon_numpy_docstring = False

intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
}

myst_enable_extensions = ["colon_fence"]

# -- HTML output ---------------------------------------------------------
html_theme = "furo"
html_static_path = ["_static"]
