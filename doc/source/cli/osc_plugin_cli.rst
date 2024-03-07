================================================
``openstack share`` Command-Line Interface (CLI)
================================================

.. program:: openstack share

Synopsis
========

:program:`openstack [options] share` <command> [command-options]

:program:`openstack help share` <command>


Description
===========

The OpenStack Client plugin interacts with the Manila service
through the ``openstack share`` command line interface (CLI).

To use the CLI, you must provide your OpenStack username, password,
project, auth endpoint and the share API version.
You can use configuration options ``--os-username``,
``--os-password``, ``--os-project-name``, ``--os-auth-url``
and ``--os-share-api-version``, or set the corresponding
environment variables::

    export OS_USERNAME=foo
    export OS_PASSWORD=bar
    export OS_TENANT_NAME=foobarproject
    export OS_AUTH_URL=http://...
    export OS_SHARE_API_VERSION=2.51


Getting help
============

To get a full list of all possible commands, run::

    $ openstack help share

To get detailed help for one command, run::

    $ openstack help share <command>


Examples
========

Get information about the openstack share create command::

    $ openstack help share create

Create one share::

    $ openstack share create NFS 1 --name "myshare"

List shares::

    $ openstack share list

Display a share::

    $ openstack share show myshare

Delete a share::

    $ openstack share delete myshare

Extend a 1gb share to 2gb::

    $ openstack share resize myshare 2

Shrink a 2gb share to 1gb::

    $ openstack share resize myshare 1


Command Reference
=================
.. toctree::
   :glob:
   :maxdepth: 3

   osc/v2/*
