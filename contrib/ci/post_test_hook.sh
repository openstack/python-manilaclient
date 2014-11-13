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
sudo chown -R jenkins:stack .

# Create manilaclient config file
touch $MANILACLIENT_CONF

# Import 'iniset' func from devstack functions
source $BASE/new/devstack/functions

# Set options to config client.
source $BASE/new/devstack/accrc/demo/demo
iniset $MANILACLIENT_CONF DEFAULT username $OS_USERNAME
iniset $MANILACLIENT_CONF DEFAULT tenant_name $OS_TENANT_NAME
iniset $MANILACLIENT_CONF DEFAULT password $OS_PASSWORD
iniset $MANILACLIENT_CONF DEFAULT auth_url $OS_AUTH_URL

source $BASE/new/devstack/accrc/demo/admin
iniset $MANILACLIENT_CONF DEFAULT admin_username $OS_USERNAME
iniset $MANILACLIENT_CONF DEFAULT admin_tenant_name $OS_TENANT_NAME
iniset $MANILACLIENT_CONF DEFAULT admin_password $OS_PASSWORD
iniset $MANILACLIENT_CONF DEFAULT admin_auth_url $OS_AUTH_URL

# let us control if we die or not
set +o errexit

# Run functional tests
sudo -H -u jenkins tox -e functional
