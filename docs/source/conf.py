# Configuration file for the Sphinx documentation builder.

import selkie
print('SELKIE:', selkie.__file__)

# -- Project information

project = 'Selkie'
copyright = '2022, University of Michigan'
author = 'Steven Abney'

# release: x.y, version: x.y.z
release = '0.25'
version = '0.25.2'

# -- General configuration

extensions = [
    'sphinx.ext.duration',
    'sphinx.ext.doctest',
    'sphinx.ext.autodoc',
    'sphinx.ext.autosummary',
    'sphinx.ext.intersphinx',
]

intersphinx_mapping = {
    'python': ('https://docs.python.org/3/', None),
    'sphinx': ('https://www.sphinx-doc.org/en/master/', None),
}
intersphinx_disabled_domains = ['std']

templates_path = ['_templates']

# -- Options for HTML output

html_theme = 'sphinx_rtd_theme'

# -- Options for EPUB output
epub_show_urls = 'footnote'

