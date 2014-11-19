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
sudo -H -u jenkins tox -e functional -v
EXIT_CODE=$?

if [ -d ".testrepository" ] ; then
    if [ -f ".testrepository/0.2" ] ; then
        cp .testrepository/0.2 ./subunit_log.txt
    elif [ -f ".testrepository/0" ] ; then
        .tox/functional/bin/subunit-1to2 < .testrepository/0 > ./subunit_log.txt
    fi
    .tox/functional/bin/python /usr/local/jenkins/slave_scripts/subunit2html.py ./subunit_log.txt testr_results.html
    SUBUNIT_SIZE=$(du -k ./subunit_log.txt | awk '{print $1}')
    gzip -9 ./subunit_log.txt
    gzip -9 ./testr_results.html
    sudo mv testr_results.html.gz $WORKSPACE/logs
    sudo mv subunit_log.txt.gz $WORKSPACE/logs
    sudo cp -R .tox $WORKSPACE
    sudo cp -R .testrepository $WORKSPACE

    if [[ "$SUBUNIT_SIZE" -gt 50000 ]]; then
        echo
        echo "sub_unit.log was greater than 50 MB of uncompressed data!"
        echo "Something is causing tests for this project to log significant amounts of data."
        echo "This may be writers to python logging, stdout, or stderr."
        echo "Failing this test as a result."
        echo
        exit 1
    fi

    rancount=$(.tox/functional/bin/testr last | sed -ne 's/Ran \([0-9]\+\).*tests in.*/\1/p')
    if [ -z "$rancount" ] || [ "$rancount" -eq "0" ] ; then
        echo
        echo "Zero tests were run. At least one test should have been run."
        echo "Failing this test as a result."
        echo
        exit 1
    fi
fi
return $EXIT_CODE
