# Copyright 2015 Mirantis Inc.
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import ddt
from tempest.lib.common.utils import data_utils
from tempest.lib import exceptions

from manilaclient import config
from manilaclient.tests.functional import base

CONF = config.CONF


@ddt.ddt
class ShareServersReadOnlyTest(base.BaseTestCase):

    @classmethod
    def setUpClass(cls):
        super(ShareServersReadOnlyTest, cls).setUpClass()
        cls.client = cls.get_admin_client()

    def test_share_server_list(self):
        self.client.list_share_servers()

    def test_share_server_list_with_host_param(self):
        self.client.list_share_servers(filters={'host': 'fake_host'})

    def test_share_server_list_with_status_param(self):
        self.client.list_share_servers(filters={'status': 'fake_status'})

    def test_share_server_list_with_share_network_param(self):
        self.client.list_share_servers(filters={'share_network': 'fake_sn'})

    def test_share_server_list_with_project_id_param(self):
        self.client.list_share_servers(
            filters={'project_id': 'fake_project_id'})

    @ddt.data(
        'host', 'status', 'project_id', 'share_network',
        'host,status,project_id,share_network',
    )
    def test_share_server_list_with_specified_columns(self, columns):
        self.client.list_share_servers(columns=columns)

    def test_share_server_list_by_user(self):
        self.assertRaises(
            exceptions.CommandFailed, self.user_client.list_share_servers)


@ddt.ddt
class ShareServersReadWriteBase(base.BaseTestCase):

    protocol = None

    @classmethod
    def setUpClass(cls):
        super(ShareServersReadWriteBase, cls).setUpClass()
        if not CONF.run_share_servers_tests:
            message = "share-servers tests are disabled."
            raise cls.skipException(message)
        if cls.protocol not in CONF.enable_protocols:
            message = "%s tests are disabled." % cls.protocol
            raise cls.skipException(message)

        cls.client = cls.get_admin_client()
        if not cls.client.share_network:
            message = "Can run only with DHSS=True mode"
            raise cls.skipException(message)

    def test_get_and_delete_share_server(self):
        name = data_utils.rand_name('autotest_share_name')
        description = data_utils.rand_name('autotest_share_description')

        # We create separate share network to be able to delete share server
        # further knowing that it is not used by any other concurrent test.
        common_share_network = self.client.get_share_network(
            self.client.share_network)
        neutron_net_id = (
            common_share_network['neutron_net_id']
            if 'none' not in common_share_network['neutron_net_id'].lower()
            else None)
        neutron_subnet_id = (
            common_share_network['neutron_subnet_id']
            if 'none' not in common_share_network['neutron_subnet_id'].lower()
            else None)
        share_network = self.client.create_share_network(
            neutron_net_id=neutron_net_id,
            neutron_subnet_id=neutron_subnet_id,
        )

        self.share = self.create_share(
            share_protocol=self.protocol,
            size=1,
            name=name,
            description=description,
            share_network=share_network['id'],
            client=self.client,
        )
        share_server_id = self.client.get_share(
            self.share['id'])['share_server_id']

        # Get share server
        server = self.client.get_share_server(share_server_id)
        expected_keys = (
            'id', 'host', 'status', 'created_at', 'updated_at',
            'share_network_id', 'share_network_name', 'project_id',
        )
        for key in expected_keys:
            self.assertIn(key, server)

        # Delete share
        self.client.delete_share(self.share['id'])
        self.client.wait_for_share_deletion(self.share['id'])

        # Delete share server
        self.client.delete_share_server(share_server_id)
        self.client.wait_for_share_server_deletion(share_server_id)


class ShareServersReadWriteNFSTest(ShareServersReadWriteBase):
    protocol = 'nfs'


class ShareServersReadWriteCIFSTest(ShareServersReadWriteBase):
    protocol = 'cifs'


def load_tests(loader, tests, _):
    result = []
    for test_case in tests:
        if type(test_case._tests[0]) is ShareServersReadWriteBase:
            continue
        result.append(test_case)
    return loader.suiteClass(result)
