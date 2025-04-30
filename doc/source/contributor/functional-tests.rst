Functional tests
================

There is a suite of functional tests under the
python-manilaclient/tests/functional directory. Unlike unit tests, these
tests perform API calls to Manila and are designed to run on a DevStack.

Adding functional tests to your changes is not mandatory but it's certainly
a good practice and it's encouraged.

Prerequisite
------------

You need to have manila running somewhere. If you wish to use DevStack to
run manila, a good place to start would be the `manila contributor guide`_.

.. note::

    We absolutely recommend using a ``fake shared file system back end`` as
    opposed to a real storage system, because our tests are written with the
    assumption that all APIs manila exposes are usable. In reality,
    different real world storage back ends have `different capabilities`_ and
    this project doesn't need to worry about them to provide a general purpose
    interface to Manila. A fake driver provides fake storage, so don't
    expect to be able to mount or use the shared file systems that you
    create with it.

You can use the following local.conf file to configure DevStack including
Manila using a few fake back ends:

.. code-block:: bash

    [[local|localrc]]

    # auth
    ADMIN_PASSWORD=nomoresecret
    DATABASE_PASSWORD=$ADMIN_PASSWORD
    RABBIT_PASSWORD=$ADMIN_PASSWORD
    SERVICE_PASSWORD=$ADMIN_PASSWORD

    # enable logging for DevStack
    LOGFILE=/opt/stack/logs/stack.sh.log

    # Logging mode for DevStack services
    VERBOSE=True

    # manila
    enable_plugin manila https://opendev.org/openstack/manila

    # python-manilaclient
    LIBS_FROM_GIT=python-manilaclient

    # share driver
    SHARE_DRIVER=manila.tests.share.drivers.dummy.DummyDriver

    # share types
    MANILA_DEFAULT_SHARE_TYPE_EXTRA_SPECS='snapshot_support=True create_share_from_snapshot_support=True revert_to_snapshot_support=True mount_snapshot_support=True'
    MANILA_CONFIGURE_DEFAULT_TYPES=True

    # backends and groups
    MANILA_ENABLED_BACKENDS=alpha,beta,gamma,delta
    MANILA_CONFIGURE_GROUPS=alpha,beta,gamma,delta,membernet,adminnet

    # alpha
    MANILA_OPTGROUP_alpha_share_driver=manila.tests.share.drivers.dummy.DummyDriver
    MANILA_OPTGROUP_alpha_driver_handles_share_servers=True
    MANILA_OPTGROUP_alpha_share_backend_name=ALPHA
    MANILA_OPTGROUP_alpha_network_config_group=membernet
    MANILA_OPTGROUP_alpha_admin_network_config_group=adminnet

    # beta
    MANILA_OPTGROUP_beta_share_driver=manila.tests.share.drivers.dummy.DummyDriver
    MANILA_OPTGROUP_beta_driver_handles_share_servers=True
    MANILA_OPTGROUP_beta_share_backend_name=BETA
    MANILA_OPTGROUP_beta_network_config_group=membernet
    MANILA_OPTGROUP_beta_admin_network_config_group=adminnet

    # gamma
    MANILA_OPTGROUP_gamma_share_driver=manila.tests.share.drivers.dummy.DummyDriver
    MANILA_OPTGROUP_gamma_driver_handles_share_servers=False
    MANILA_OPTGROUP_gamma_share_backend_name=GAMMA
    MANILA_OPTGROUP_gamma_replication_domain=DUMMY_DOMAIN

    # delta
    MANILA_OPTGROUP_delta_share_driver=manila.tests.share.drivers.dummy.DummyDriver
    MANILA_OPTGROUP_delta_driver_handles_share_servers=False
    MANILA_OPTGROUP_delta_share_backend_name=DELTA
    MANILA_OPTGROUP_delta_replication_domain=DUMMY_DOMAIN

    # membernet
    MANILA_OPTGROUP_membernet_network_api_class=manila.network.standalone_network_plugin.StandaloneNetworkPlugin
    MANILA_OPTGROUP_membernet_standalone_network_plugin_gateway=10.0.0.1
    MANILA_OPTGROUP_membernet_standalone_network_plugin_mask=24
    MANILA_OPTGROUP_membernet_standalone_network_plugin_network_type=vlan
    MANILA_OPTGROUP_membernet_standalone_network_plugin_segmentation_id=1010
    MANILA_OPTGROUP_membernet_standalone_network_plugin_allowed_ip_ranges=10.0.0.10-10.0.0.209
    MANILA_OPTGROUP_membernet_network_plugin_ipv4_enabled=True

    # adminnet
    MANILA_OPTGROUP_adminnet_network_api_class=manila.network.standalone_network_plugin.StandaloneNetworkPlugin
    MANILA_OPTGROUP_adminnet_standalone_network_plugin_gateway=11.0.0.1
    MANILA_OPTGROUP_adminnet_standalone_network_plugin_mask=24
    MANILA_OPTGROUP_adminnet_standalone_network_plugin_network_type=vlan
    MANILA_OPTGROUP_adminnet_standalone_network_plugin_segmentation_id=1011
    MANILA_OPTGROUP_adminnet_standalone_network_plugin_allowed_ip_ranges=11.0.0.10-11.0.0.19,11.0.0.30-11.0.0.39,11.0.0.50-11.0.0.199
    MANILA_OPTGROUP_adminnet_network_plugin_ipv4_enabled=True

Configuration
-------------

The functional tests require a couple of configuration files, so you will need
to generate them before running the tests.

For DevStack
^^^^^^^^^^^^

On your DevStack machine, you can run the following script. It assumes that
``devstack`` is cloned onto your base folder.

.. code-block:: bash

    DEST=${DEST:-/opt/stack}
    MANILACLIENT_DIR=${MANILACLIENT_DIR:-$DEST/python-manilaclient}
    MANILACLIENT_CONF="$MANILACLIENT_DIR/etc/manilaclient/manilaclient.conf"
    # Go to the manilaclient dir
    cd $MANILACLIENT_DIR
    # Give permissions
    sudo chown -R $USER:stack .
    # Create manilaclient config file
    touch $MANILACLIENT_CONF
    # Import functions from devstack
    source $HOME/devstack/functions
    # Set options to config client.
    source $HOME/devstack/openrc demo demo
    export OS_TENANT_NAME=${OS_PROJECT_NAME:-$OS_TENANT_NAME}
    iniset $MANILACLIENT_CONF DEFAULT username $OS_USERNAME
    iniset $MANILACLIENT_CONF DEFAULT tenant_name $OS_TENANT_NAME
    iniset $MANILACLIENT_CONF DEFAULT password $OS_PASSWORD
    iniset $MANILACLIENT_CONF DEFAULT auth_url $OS_AUTH_URL
    iniset $MANILACLIENT_CONF DEFAULT project_domain_name $OS_PROJECT_DOMAIN_NAME
    iniset $MANILACLIENT_CONF DEFAULT user_domain_name $OS_USER_DOMAIN_NAME
    iniset $MANILACLIENT_CONF DEFAULT project_domain_id $OS_PROJECT_DOMAIN_ID
    iniset $MANILACLIENT_CONF DEFAULT user_domain_id $OS_USER_DOMAIN_ID
    source $HOME/devstack/openrc admin demo
    export OS_TENANT_NAME=${OS_PROJECT_NAME:-$OS_TENANT_NAME}
    iniset $MANILACLIENT_CONF DEFAULT admin_username $OS_USERNAME
    iniset $MANILACLIENT_CONF DEFAULT admin_tenant_name $OS_TENANT_NAME
    iniset $MANILACLIENT_CONF DEFAULT admin_password $OS_PASSWORD
    iniset $MANILACLIENT_CONF DEFAULT admin_auth_url $OS_AUTH_URL
    iniset $MANILACLIENT_CONF DEFAULT admin_project_domain_name $OS_PROJECT_DOMAIN_NAME
    iniset $MANILACLIENT_CONF DEFAULT admin_user_domain_name $OS_USER_DOMAIN_NAME
    iniset $MANILACLIENT_CONF DEFAULT admin_project_domain_id $OS_PROJECT_DOMAIN_ID
    iniset $MANILACLIENT_CONF DEFAULT admin_user_domain_id $OS_USER_DOMAIN_ID
    # Suppress errors in cleanup of resources
    SUPPRESS_ERRORS=${SUPPRESS_ERRORS_IN_CLEANUP:-False}
    iniset $MANILACLIENT_CONF DEFAULT suppress_errors_in_cleanup $SUPPRESS_ERRORS
    # Set access type usage specific to dummy driver that we are using in CI
    iniset $MANILACLIENT_CONF DEFAULT access_types_mapping "nfs:ip,cifs:user"
    # Dummy driver is capable of running share migration tests
    iniset $MANILACLIENT_CONF DEFAULT run_migration_tests "True"
    # Running mountable snapshot tests in dummy driver
    iniset $MANILACLIENT_CONF DEFAULT run_mount_snapshot_tests "True"
    # Create share network and use it for functional tests if required
    USE_SHARE_NETWORK=$(trueorfalse True USE_SHARE_NETWORK)

.. code-block:: bash

    if [[ ${USE_SHARE_NETWORK} = True ]]; then
        SHARE_NETWORK_NAME=${SHARE_NETWORK_NAME:-ci}
        DEFAULT_NEUTRON_NET=$(openstack network show private -c id -f value)
        DEFAULT_NEUTRON_SUBNET=$(openstack subnet show private-subnet -c id -f value)
        NEUTRON_NET=${NEUTRON_NET:-$DEFAULT_NEUTRON_NET}
        NEUTRON_SUBNET=${NEUTRON_SUBNET:-$DEFAULT_NEUTRON_SUBNET}
        manila share-network-create --name $SHARE_NETWORK_NAME --neutron-net $NEUTRON_NET --neutron-subnet $NEUTRON_SUBNET
        iniset $MANILACLIENT_CONF DEFAULT share_network $SHARE_NETWORK_NAME
        iniset $MANILACLIENT_CONF DEFAULT admin_share_network $SHARE_NETWORK_NAME

    fi

.. code-block:: bash

    # Set share type if required
    if [[ "$SHARE_TYPE" ]]; then
        iniset $MANILACLIENT_CONF DEFAULT share_type $SHARE_TYPE

    fi

Running the tests
-----------------

To run all functional tests make sure you are in the top level of your
python-manilaclient module (e.g. /opt/stack/python-manilaclient/) and simply
run::

    tox -e functional

This will create a virtual environment, load all the packages from
test-requirements.txt and run all functional tests.


.. _manila contributor guide: https://docs.openstack.org/manila/latest/contributor/development-environment-devstack.html
.. _different capabilities: https://docs.openstack.org/manila/latest/admin/share_back_ends_feature_support_mapping.html
