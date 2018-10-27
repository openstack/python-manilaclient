#!/bin/bash -xe
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

# This script is executed inside post_test_hook function in devstack gate.

export MANILACLIENT_DIR="$BASE/new/python-manilaclient"
export MANILACLIENT_CONF="$MANILACLIENT_DIR/etc/manilaclient/manilaclient.conf"

# Go to the manilaclient dir
cd $MANILACLIENT_DIR

# Give permissions
sudo chown -R $USER:stack .

# Create manilaclient config file
touch $MANILACLIENT_CONF

# Import functions from devstack
source $BASE/new/devstack/functions

env | grep OS_

# Set options to config client.
source $BASE/new/devstack/openrc demo demo
env | grep OS_
export OS_TENANT_NAME=${OS_PROJECT_NAME:-$OS_TENANT_NAME}
iniset $MANILACLIENT_CONF DEFAULT username $OS_USERNAME
iniset $MANILACLIENT_CONF DEFAULT tenant_name $OS_TENANT_NAME
iniset $MANILACLIENT_CONF DEFAULT password $OS_PASSWORD
iniset $MANILACLIENT_CONF DEFAULT auth_url $OS_AUTH_URL
iniset $MANILACLIENT_CONF DEFAULT project_domain_name $OS_PROJECT_DOMAIN_NAME
iniset $MANILACLIENT_CONF DEFAULT user_domain_name $OS_USER_DOMAIN_NAME
iniset $MANILACLIENT_CONF DEFAULT project_domain_id $OS_PROJECT_DOMAIN_ID
iniset $MANILACLIENT_CONF DEFAULT user_domain_id $OS_USER_DOMAIN_ID

source $BASE/new/devstack/openrc admin demo
env | grep OS_
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
SUPPRESS_ERRORS=${SUPPRESS_ERRORS_IN_CLEANUP:-True}
iniset $MANILACLIENT_CONF DEFAULT suppress_errors_in_cleanup $SUPPRESS_ERRORS

# Set access type usage specific to dummy driver that we are using in CI
iniset $MANILACLIENT_CONF DEFAULT access_types_mapping "nfs:ip,cifs:user"

# Dummy driver is capable of running share migration tests
iniset $MANILACLIENT_CONF DEFAULT run_migration_tests "True"

# Dummy driver is capable of running share manage tests
iniset $MANILACLIENT_CONF DEFAULT run_manage_tests "True"

# Running mountable snapshot tests in dummy driver
iniset $MANILACLIENT_CONF DEFAULT run_mount_snapshot_tests "True"

# Create share network and use it for functional tests if required
USE_SHARE_NETWORK=$(trueorfalse True USE_SHARE_NETWORK)
if [[ ${USE_SHARE_NETWORK} = True ]]; then
    SHARE_NETWORK_NAME=${SHARE_NETWORK_NAME:-ci}

    DEFAULT_NEUTRON_NET=$(openstack network show private -c id -f value)
    DEFAULT_NEUTRON_SUBNET=$(openstack subnet show private-subnet -c id -f value)
    NEUTRON_NET=${NEUTRON_NET:-$DEFAULT_NEUTRON_NET}
    NEUTRON_SUBNET=${NEUTRON_SUBNET:-$DEFAULT_NEUTRON_SUBNET}

    manila share-network-create \
        --name $SHARE_NETWORK_NAME \
        --neutron-net $NEUTRON_NET \
        --neutron-subnet $NEUTRON_SUBNET

    iniset $MANILACLIENT_CONF DEFAULT share_network $SHARE_NETWORK_NAME
    iniset $MANILACLIENT_CONF DEFAULT admin_share_network $SHARE_NETWORK_NAME
fi

# Set share type if required
if [[ "$SHARE_TYPE" ]]; then
    iniset $MANILACLIENT_CONF DEFAULT share_type $SHARE_TYPE
fi

# let us control if we die or not
set +o errexit

CONCURRENCY=${CONCURRENCY:-8}

# Run functional tests
sudo -H -u $USER tox -e functional -v -- --concurrency=$CONCURRENCY
EXIT_CODE=$?

# Copy artifacts into ZUUL's workspace
sudo -H -u $USER cp -r $MANILACLIENT_DIR $WORKSPACE

return $EXIT_CODE