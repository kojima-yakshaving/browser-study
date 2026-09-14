from __future__ import annotations

import os
import sys

from docutils import nodes
from sphinx.util.docutils import SphinxDirective

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
html_theme = "sphinx_rtd_theme"
html_static_path = ["_static"]

# -- Demo pages ------------------------------------------------------------
# The sample HTML pages under demo/ (repo root) are published verbatim at
# <site>/demo/ so the toy browser can load them over HTTP from GitHub Pages.
DEMO_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "demo")
)


def copy_demo_pages(app, exception):
    """Copy demo/ into the HTML output root after a successful build."""
    if exception is not None or app.builder.name != "html":
        return
    from sphinx.util.fileutil import copy_asset

    copy_asset(DEMO_DIR, os.path.join(app.outdir, "demo"))


def demo_page_names():
    """Return the HTML file names under demo/, sorted."""
    return sorted(
        name for name in os.listdir(DEMO_DIR) if name.endswith(".html")
    )


class DemoListDirective(SphinxDirective):
    """Render a bullet list linking to every HTML file under demo/."""

    def run(self):
        """Build the list nodes from the current demo/ contents."""
        items = []
        for name in demo_page_names():
            link = nodes.reference("", name, refuri=f"demo/{name}")
            items.append(nodes.list_item("", nodes.paragraph("", "", link)))
        return [nodes.bullet_list("", *items)]


def outdate_demo_list(app, env, added, changed, removed):
    """Re-read pages using demo-list so new demo files show up."""
    return [doc for doc in ("demos",) if doc in env.found_docs]


def setup(app):
    """Register the demo directive and copy step with Sphinx."""
    app.add_directive("demo-list", DemoListDirective)
    app.connect("env-get-outdated", outdate_demo_list)
    app.connect("build-finished", copy_demo_pages)
