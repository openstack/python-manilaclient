Python bindings to the OpenStack Manila API
===========================================

This is a client for OpenStack Manila API. There's :doc:`a Python API
<user/api>` (the :mod:`manilaclient` module), and a :doc:`command-line script
<user/shell>` (installed as :program:`manila`). Each implements the entire
OpenStack Manila API. See :ref:`project-structure` for more information.

You'll need credentials for an OpenStack cloud that implements the
Manila API in order to use the manila client.

Command-Line Reference
~~~~~~~~~~~~~~~~~~~~~~
There are two shell implementations supported by python-manilaclient.
The "manila" client supports full feature parity with the manila API:

.. toctree::
   :maxdepth: 2

   user/shell

From version 2.0.0, there is a growing support for the OpenStack client.
It does not yet have full feature parity with the manila API:

.. toctree::
   :maxdepth: 1

   cli/osc_plugin_cli

Using the python module
~~~~~~~~~~~~~~~~~~~~~~~

.. toctree::
   :maxdepth: 2

   user/api

Contributing
~~~~~~~~~~~~

.. toctree::
   :maxdepth: 2

   contributor/index

.. only:: html

   Indices and tables
   ~~~~~~~~~~~~~~~~~~

   * :ref:`genindex`
   * :ref:`search`
