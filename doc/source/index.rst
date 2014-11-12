Python bindings to the OpenStack Manila API
===========================================

This is a client for OpenStack Manila API. There's :doc:`a Python API
<api>` (the :mod:`manilaclient` module), and a :doc:`command-line script
<shell>` (installed as :program:`manila`). Each implements the entire
OpenStack Manila API.

You'll need credentials for an OpenStack cloud that implements the
Manila API in order to use the manila client.

Contents:

.. toctree::
   :maxdepth: 2

   shell
   api

Contributing
============

Code is hosted at `git.openstack.org`_. Submit bugs to the
python-manilaclient project on `Launchpad`_. Submit code to the
openstack/python-manilaclient project using `Gerrit`_.

.. _git.openstack.org: https://git.openstack.org/cgit/openstack/python-manilaclient
.. _Launchpad: https://launchpad.net/python-manilaclient
.. _Gerrit: http://wiki.openstack.org/GerritWorkflow

Testing
-------

The preferred way to run the unit tests is using ``tox``.

See `Consistent Testing Interface`_ for more details.

.. _Consistent Testing Interface: http://git.openstack.org/cgit/openstack/governance/tree/reference/project-testing-interface.rst

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`


Release Notes
=============

No releases.
