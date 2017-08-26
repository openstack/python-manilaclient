Contributing
============

Code is hosted at `git.openstack.org`_. Submit bugs to the
python-manilaclient project on `Launchpad`_. Submit code to the
openstack/python-manilaclient project using `Gerrit`_.

.. _git.openstack.org: https://git.openstack.org/cgit/openstack/python-manilaclient
.. _Launchpad: https://launchpad.net/python-manilaclient
.. _Gerrit: https://docs.openstack.org/infra/manual/developers.html#development-workflow

Testing
-------

Manilaclient has two types of tests - 'unit' and 'functional'.

The preferred way to run tests is using ``tox``.

See `Consistent Testing Interface`_ for more details.

.. _Consistent Testing Interface: https://git.openstack.org/cgit/openstack/governance/tree/reference/project-testing-interface.rst

Functional tests
----------------

Functional CLI tests require several things to be able to run:

* Deployed and working manila service.
* Configured config file.

Config file is used to get information like 'auth_url', 'username',
'tenant_name' and 'password'.
To get config sample need to run following 'tox' job:

.. code-block:: console

  $ tox -e genconfig

This will create file 'etc/manilaclient/manilaclient.conf.sample' with all
available config opts.
Then rename it removing ".sample" and set values for opts there. After it,
tests can be run using following tox job:

.. code-block:: console

  $ tox -e functional

