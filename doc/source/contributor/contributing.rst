============================
So You Want to Contribute...
============================

For general information on contributing to OpenStack, check out the
`contributor guide <https://docs.openstack.org/contributors/>`_ to get started.
It covers all the basics that are common to all OpenStack projects: the
accounts you need, the basics of interacting with our Gerrit review system,
how we communicate as a community, etc.

This project contains a python SDK and command line clients to interact with
the API exposed by `Manila <https://opendev.org/openstack/manila>`_,
the OpenStack Shared File Systems service. Refer to the `Contributor guide
for Manila <https://docs.openstack.org/manila/latest/contributor/contributing.html>`_
for information regarding the team's task trackers, communicating with other
project developers and contacting the core team.

Bugs
~~~~

You found an issue and want to make sure we are aware of it? You can do so on
`Launchpad <https://bugs.launchpad.net/python-manilaclient>`_.

If you're looking to contribute, search for the `low-hanging-fruit`_ tag to
see issues that are easier to get started with.

.. _project-structure:

Project Structure
~~~~~~~~~~~~~~~~~

This project includes three distinct components:

- manilaclient SDK: python bindings for Manila API `version V1`_ and
  `version V2`_
- manilaclient shell: A `command line utility`_ (``manila``)
- OpenStack client shell: A `plugin to support the OpenStack Client`_
  Command Line Interface.

The version 2 of the API for Manila supports microversions. The manilaclient
library is expected to handle these for complete backwards compatibility.
All versions of the Manila API are currently supported, however, future
releases of manilaclient may drop support for older versions of the API.

If you're working on the OpenStack Client command line interface plugin that
exists in this project, do read the `OpenStack Client Developer
Documentation`_. This includes the Human Interface Guide and some design
priciples including command structure and command specs that you will find
helpful.

.. _low-hanging-fruit: https://bugs.launchpad.net/python-manilaclient/+bugs?field.tag=low-hanging-fruit
.. _version V1: https://opendev.org/openstack/python-manilaclient/src/branch/master/manilaclient/v1
.. _version V2: https://opendev.org/openstack/python-manilaclient/src/branch/master/manilaclient/v2
.. _command line utility: https://opendev.org/openstack/python-manilaclient/src/branch/master/manilaclient/shell.py
.. _plugin to support the OpenStack Client: https://opendev.org/openstack/python-manilaclient/src/branch/master/manilaclient/osc
.. _OpenStack Client Developer Documentation: https://docs.openstack.org/python-openstackclient/latest/contributor/index.html
