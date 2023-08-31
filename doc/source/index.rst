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
There are two shell implementations in python-manilaclient.

.. important::

    The legacy "manila" shell client is deprecated as of version ``5.0.0``.
    A future version of python-manilaclient may not ship this legacy shell
    client. If you rely on it, it is highly recommended that you begin using
    the openstack CLI client right away. Refer to the `mapping guide
    <cli/decoder.html>`_ to help with this transition.

The "openstack" CLI client intends to be fully compatible with the manila API:

.. toctree::
   :maxdepth: 1

   cli/osc_plugin_cli
   cli/decoder

The legacy "manila" client is deprecated and may not support newer API
features:

.. toctree::
   :maxdepth: 2

   user/shell

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
