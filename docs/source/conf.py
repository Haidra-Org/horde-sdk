# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html


import pathlib
import sys

# -- Path setup --------------------------------------------------------------
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent.parent / "src"))

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = "horde_sdk"
copyright = "2023, hairda-org"  # noqa: A001
author = "tazlin, db0"
release = "0.1.x"

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = ["sphinx.ext.autodoc", "sphinx.ext.napoleon"]

templates_path = ["_templates"]
exclude_patterns: list[str] = []

autodoc_default_options = {
    "members": True,
    "member-order": "bysource",
    "undoc-members": "__init__",
    "exclude-members": "__weakref__,model_fields,model_config",
}

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "sphinx_rtd_theme"
# html_theme = "groundwork"

html_static_path = ["_static"]
