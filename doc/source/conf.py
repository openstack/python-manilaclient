#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.


# python-manilaclient documentation build configuration file

import os
import sys

import openstackdocstheme

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(BASE_DIR, "..", ".."))
sys.path.insert(0, ROOT)
# path to local extensions
sys.path.append(os.path.abspath('exts'))

# -- General configuration ----------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions
# coming with Sphinx (named 'sphinx.ext.*') or your custom ones.
extensions = ['sphinx.ext.autodoc', 'openstackdocstheme', 'clidoc']

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# The suffix of source filenames.
source_suffix = '.rst'

# The master toctree document.
master_doc = 'index'

# General information about the project.
project = u'python-manilaclient'
copyright = u'Rackspace, based on work by Jacob Kaplan-Moss'

# The version info for the project you're documenting, acts as replacement for
# |version| and |release|, also used in various other places throughout the
# built documents.
#
# The short X.Y version.
version = '2.6'
# The full version, including alpha/beta/rc tags.
release = '2.6.10'

# List of directories, relative to source directory, that shouldn't be searched
# for source files.
exclude_trees = []

# If true, '()' will be appended to :func: etc. cross-reference text.
add_function_parentheses = True

# If true, the current module name will be prepended to all description
# unit titles (such as .. function::).
add_module_names = True

# The name of the Pygments (syntax highlighting) style to use.
pygments_style = 'sphinx'

# -- Options for HTML output --------------------------------------------------

# Output file base name for HTML help builder.
htmlhelp_basename = 'python-manilaclientdoc'
html_theme = 'openstackdocs'
html_theme_path = [openstackdocstheme.get_html_theme_path()]

# openstackdocstheme options
repository_name = 'openstack/python-manilaclient'
bug_project = 'python-manilaclient'
bug_tag = 'docs'
html_last_updated_fmt = '%Y-%m-%d %H:%M'

