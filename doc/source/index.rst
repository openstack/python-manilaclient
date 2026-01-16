Python bindings to the OpenStack Manila API
===========================================

This is a client for OpenStack Manila API. There's :doc:`a Python API
<user/api>` (the :mod:`manilaclient` module) for programmatic access, and
a command-line interface via the OpenStack CLI client. See
:ref:`project-structure` for more information.

You'll need credentials for an OpenStack cloud that implements the
Manila API in order to use the manila client.

Command-Line Reference
~~~~~~~~~~~~~~~~~~~~~~
Use the "openstack" CLI client to interact with the Manila API from the
command line:

.. toctree::
   :maxdepth: 1

   cli/osc_plugin_cli
   cli/decoder

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
