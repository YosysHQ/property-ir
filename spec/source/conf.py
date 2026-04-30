# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html


import sys
import os

sys.path.insert(0, os.path.abspath('./_ext'))


# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'Property IR'
copyright = '2026 YosysHQ GmbH'
author = 'YosysHQ GmbH'
release = '0.1'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = ["sphinx.ext.mathjax", "sphinx.ext.ifconfig", "sphinx.ext.autosectionlabel", "sexpr_ext"]

templates_path = ['_templates']
exclude_patterns = []



# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'furo-ys'
html_css_files = ['custom.css']
html_static_path = ['_static']

