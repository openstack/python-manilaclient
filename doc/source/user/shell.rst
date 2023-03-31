The :program:`manila` shell utility
=========================================

.. important::

    This shell client is deprecated as of version ``5.0.0``. A future
    version of python-manilaclient may not ship this legacy shell client. If
    you rely on it, it is highly recommended that you begin using the
    openstack CLI client right away. Refer to the `mapping guide
    <../cli/decoder.html>`_ to help with this transition.

.. program:: manila
.. highlight:: bash

The :program:`manila` shell utility interacts with the OpenStack Manila API
from the command line. It supports the entirety of the OpenStack Manila API.

You'll need to provide :program:`manila` with your OpenStack username and API
key. You can do this with the `--os-username`, `--os-password` and
`--os-tenant-name` options, but it's easier to just set them as environment
variables by setting two environment variables:

.. envvar:: OS_USERNAME or MANILA_USERNAME

    Your OpenStack Manila username.

.. envvar:: OS_PASSWORD or MANILA_PASSWORD

    Your password.

.. envvar:: OS_TENANT_NAME or MANILA_PROJECT_ID

    Project for work.

.. envvar:: OS_AUTH_URL or MANILA_URL

    The OpenStack API server URL.

.. envvar:: OS_SHARE_API_VERSION

    The OpenStack Shared Filesystems API version.

For example, in Bash you'd use::

    export OS_USERNAME=foo
    export OS_PASSWORD=bar
    export OS_TENANT_NAME=foobarproject
    export OS_AUTH_URL=http://...
    export OS_SHARE_API_VERSION=2

From there, all shell commands take the form::

    manila <command> [arguments...]

Run :program:`manila help` to get a full list of all possible commands,
and run :program:`manila help <command>` to get detailed help for that
command.

.. program-output:: manila --help
