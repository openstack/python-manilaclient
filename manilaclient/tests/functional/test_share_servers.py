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

import ast
import ddt
import testtools

from tempest.lib.common.utils import data_utils
from tempest.lib import exceptions

from manilaclient.common import constants
from manilaclient import config
from manilaclient.tests.functional import base
from manilaclient.tests.functional import utils

CONF = config.CONF


@ddt.ddt
class ShareServersReadOnlyTest(base.BaseTestCase):

    def setUp(self):
        super(ShareServersReadOnlyTest, self).setUp()
        self.client = self.get_admin_client()

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

    def setUp(self):
        super(ShareServersReadWriteBase, self).setUp()
        if not CONF.run_share_servers_tests:
            message = "share-server tests are disabled."
            raise self.skipException(message)
        if self.protocol not in CONF.enable_protocols:
            message = "%s tests are disabled." % self.protocol
            raise self.skipException(message)
        self.client = self.get_admin_client()
        if not self.client.share_network:
            message = "Can run only with DHSS=True mode"
            raise self.skipException(message)

    def _create_share_and_share_network(self):
        name = data_utils.rand_name('autotest_share_name')
        description = data_utils.rand_name('autotest_share_description')

        common_share_network = self.client.get_share_network(
            self.client.share_network)
        share_net_info = (
            utils.get_default_subnet(self.user_client,
                                     common_share_network['id'])
            if utils.share_network_subnets_are_supported()
            else common_share_network)
        neutron_net_id = (
            share_net_info['neutron_net_id']
            if 'none' not in share_net_info['neutron_net_id'].lower()
            else None)
        neutron_subnet_id = (
            share_net_info['neutron_subnet_id']
            if 'none' not in share_net_info['neutron_subnet_id'].lower()
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
            wait_for_creation=True
        )
        self.share = self.client.get_share(self.share['id'])
        return self.share, share_network

    def _delete_share_and_share_server(self, share_id, share_server_id):
        # Delete share
        self.client.delete_share(share_id)
        self.client.wait_for_share_deletion(share_id)

        # Delete share server
        self.client.delete_share_server(share_server_id)
        self.client.wait_for_share_server_deletion(share_server_id)

    def test_get_and_delete_share_server(self):
        self.share, share_network = self._create_share_and_share_network()
        share_server_id = self.client.get_share(
            self.share['id'])['share_server_id']

        # Get share server
        server = self.client.get_share_server(share_server_id)
        expected_keys = (
            'id', 'host', 'status', 'created_at', 'updated_at',
            'share_network_id', 'share_network_name', 'project_id',
        )

        if utils.is_microversion_supported('2.49'):
            expected_keys += ('identifier', 'is_auto_deletable')

        for key in expected_keys:
            self.assertIn(key, server)

        self._delete_share_and_share_server(self.share['id'], share_server_id)
        self.client.delete_share_network(share_network['id'])

    @testtools.skipUnless(
        CONF.run_manage_tests, 'Share Manage/Unmanage tests are disabled.')
    @utils.skip_if_microversion_not_supported('2.49')
    def test_manage_and_unmanage_share_server(self):
        share, share_network = self._create_share_and_share_network()
        share_server_id = self.client.get_share(
            self.share['id'])['share_server_id']
        server = self.client.get_share_server(share_server_id)
        server_host = server['host']
        export_location = self.client.list_share_export_locations(
            self.share['id'])[0]['Path']
        share_host = share['host']
        identifier = server['identifier']

        self.assertEqual('True', server['is_auto_deletable'])

        # Unmanages share
        self.client.unmanage_share(share['id'])
        self.client.wait_for_share_deletion(share['id'])

        server = self.client.get_share_server(share_server_id)
        self.assertEqual('False', server['is_auto_deletable'])

        # Unmanages share server
        self.client.unmanage_server(share_server_id)
        self.client.wait_for_share_server_deletion(share_server_id)

        # Manage share server
        managed_share_server_id = self.client.share_server_manage(
            server_host, share_network['id'], identifier)
        self.client.wait_for_resource_status(
            managed_share_server_id, constants.STATUS_ACTIVE,
            resource_type='share_server')

        managed_server = self.client.get_share_server(managed_share_server_id)
        self.assertEqual('False', managed_server['is_auto_deletable'])

        # Manage share
        managed_share_id = self.client.manage_share(
            share_host, self.protocol, export_location,
            managed_share_server_id)
        self.client.wait_for_resource_status(managed_share_id,
                                             constants.STATUS_AVAILABLE)

        self._delete_share_and_share_server(managed_share_id,
                                            managed_share_server_id)
        self.client.delete_share_network(share_network['id'])


class ShareServersReadWriteNFSTest(ShareServersReadWriteBase):
    protocol = 'nfs'


class ShareServersReadWriteCIFSTest(ShareServersReadWriteBase):
    protocol = 'cifs'


@ddt.ddt
@utils.skip_if_microversion_not_supported('2.57')
class ShareServersMigrationBase(base.BaseTestCase):

    protocol = None

    def setUp(self):
        super(ShareServersMigrationBase, self).setUp()
        if not CONF.run_share_servers_tests:
            message = "Share-server tests are disabled."
            raise self.skipException(message)
        if self.protocol not in CONF.enable_protocols:
            message = "%s tests are disabled." % self.protocol
            raise self.skipException(message)
        self.client = self.get_admin_client()
        if not self.client.share_network:
            message = "Can run only with DHSS=True mode"
            raise self.skipException(message)
        if not CONF.run_share_servers_migration_tests:
            message = "Share server migration tests are disabled."
            raise self.skipException(message)

    def _create_share_and_share_network(self):
        name = data_utils.rand_name('autotest_share_name')
        description = data_utils.rand_name('autotest_share_description')

        common_share_network = self.client.get_share_network(
            self.client.share_network)
        share_net_info = utils.get_default_subnet(self.client,
                                                  common_share_network['id'])

        neutron_net_id = (
            share_net_info['neutron_net_id']
            if 'none' not in share_net_info['neutron_net_id'].lower()
            else None)
        neutron_subnet_id = (
            share_net_info['neutron_subnet_id']
            if 'none' not in share_net_info['neutron_subnet_id'].lower()
            else None)
        share_network = self.client.create_share_network(
            neutron_net_id=neutron_net_id,
            neutron_subnet_id=neutron_subnet_id,
        )
        share_type = self.create_share_type(
            data_utils.rand_name('test_share_type'),
            driver_handles_share_servers=True)

        share = self.create_share(
            share_protocol=self.protocol,
            size=1,
            name=name,
            description=description,
            share_type=share_type['ID'],
            share_network=share_network['id'],
            client=self.client,
            wait_for_creation=True
        )
        share = self.client.get_share(share['id'])
        return share, share_network

    @ddt.data('cancel', 'complete')
    def test_share_server_migration(self, operation):

        # Create a share and share network to be used in the tests.
        share, share_network = self._create_share_and_share_network()
        share_server_id = share['share_server_id']
        src_host = share['host'].split('#')[0]
        pools = self.admin_client.pool_list(detail=True)

        host_list = list()
        # Filter the backends DHSS True and different
        # than the source host.
        for hosts in pools:
            host_name = hosts['Name'].split('#')[0]
            if (ast.literal_eval(hosts['Capabilities']).get(
                'driver_handles_share_servers') and
                    host_name != src_host):
                host_list.append(host_name)

        host_list = list(set(host_list))
        # If not found any host we need skip the test.
        if len(host_list) == 0:
            raise self.skipException("No hosts available for "
                                     "share server migration.")

        dest_backend = None
        # If found at least one host, we still need to verify the
        # share server migration compatibility with the destination host.
        for host in host_list:
            compatibility = self.admin_client.share_server_migration_check(
                server_id=share_server_id, dest_host=host,
                writable=False, nondisruptive=False, preserve_snapshots=False,
                new_share_network=None)
            # If found at least one compatible host, we will use it.
            if compatibility['compatible']:
                dest_host = host
        # If not found, we need skip the test.
        if dest_backend is not None:
            raise self.skipException("No hosts compatible to perform a "
                                     "share server migration.")

        # Start the share server migration
        self.admin_client.share_server_migration_start(
            share_server_id, dest_host)

        server = self.admin_client.get_share_server(share_server_id)
        share = self.admin_client.get_share(share['id'])
        self.assertEqual(constants.STATUS_SERVER_MIGRATING, share['status'])

        # Wait for the share server migration driver phase 1 done.
        task_state = constants.TASK_STATE_MIGRATION_DRIVER_PHASE1_DONE
        server = self.admin_client.wait_for_server_migration_task_state(
            share_server_id, dest_host, task_state)
        migration_progress = (
            self.admin_client.share_server_migration_get_progress(
                share_server_id))
        dest_share_server_id = migration_progress.get(
            'destination_share_server_id')

        # Call share server migration complete or cancel operations
        # according the ddt.
        if operation == 'complete':
            task_state = constants.TASK_STATE_MIGRATION_SUCCESS
            self.admin_client.share_server_migration_complete(
                share_server_id)
            server = self.admin_client.wait_for_server_migration_task_state(
                dest_share_server_id, dest_host, task_state)

            self.admin_client.wait_for_share_server_deletion(share_server_id)
        else:
            self.admin_client.share_server_migration_cancel(server['id'])
            task_state = constants.TASK_STATE_MIGRATION_CANCELLED
            # Wait for the respectives task state for each operation above.
            server = self.admin_client.wait_for_server_migration_task_state(
                server['id'], dest_host, task_state)

        # Check if the share is available again.
        share = self.admin_client.get_share(share['id'])
        self.assertEqual('available', share['status'])


class ShareServersMigrationNFSTest(ShareServersMigrationBase):
    protocol = 'nfs'


class ShareServersMigrationCIFSTest(ShareServersMigrationBase):
    protocol = 'cifs'


def load_tests(loader, tests, _):
    result = []
    for test_case in tests:
        if type(test_case._tests[0]) is ShareServersReadWriteBase:
            continue
        if type(test_case._tests[0]) is ShareServersMigrationBase:
            continue
        result.append(test_case)
    return loader.suiteClass(result)
