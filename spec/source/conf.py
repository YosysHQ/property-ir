# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html


import sys
import os

sys.path.insert(0, os.path.abspath('./_ext'))
#import _ext.sexpr_ext

#from pathlib import Path
#
#sys.path += [os.path.dirname(__file__) + '/_ext']
#
#
#sys.path.insert(0, os.path.abspath('./_ext'))
#
#from _ext.sexpr_lexer import SExprLexer
#extensions = ['sphinx.ext.ifconfig', 'myExt']
#testlevel = 2


#sys.path.insert(0, os.path.abspath('./_ext'))


# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'Property IR'
copyright = '2026, YosysHQ'
author = 'YosysHQ'
release = '0.1'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = ["sphinx.ext.mathjax", "sphinx.ext.ifconfig", "sexpr_ext"]

templates_path = ['_templates']
exclude_patterns = []



# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'furo-ys'
html_css_files = ['custom.css']
html_static_path = ['_static']

