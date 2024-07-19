#   All rights reserved.
#
#   Licensed under the Apache License, Version 2.0 (the "License"); you may
#   not use this file except in compliance with the License. You may obtain
#   a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#   WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#   License for the specific language governing permissions and limitations
#   under the License.
#


from unittest import mock

from osc_lib import exceptions
from osc_lib import utils as oscutils

from manilaclient import api_versions
from manilaclient.osc.v2 import share_servers as osc_share_servers
from manilaclient.tests.unit.osc import osc_utils
from manilaclient.tests.unit.osc.v2 import fakes as manila_fakes


class TestShareServer(manila_fakes.TestShare):

    def setUp(self):
        super(TestShareServer, self).setUp()

        self.servers_mock = self.app.client_manager.share.share_servers
        self.servers_mock.reset_mock()

        self.share_networks_mock = self.app.client_manager.share.share_networks
        self.share_networks_mock.reset_mock()

        self.app.client_manager.share.api_version = api_versions.APIVersion(
            api_versions.MAX_VERSION)


class TestDeleteShareServer(TestShareServer):

    def setUp(self):
        super(TestDeleteShareServer, self).setUp()

        self.share_server = (
            manila_fakes.FakeShareServer.create_one_server())
        self.servers_mock.get.return_value = self.share_server

        self.cmd = osc_share_servers.DeleteShareServer(self.app, None)

    def test_share_server_delete_missing_args(self):
        arglist = []
        verifylist = []

        self.assertRaises(osc_utils.ParserException,
                          self.check_parser, self.cmd, arglist, verifylist)

    def test_share_server_delete(self):
        arglist = [
            self.share_server.id
        ]
        verifylist = [
            ('share_servers', [self.share_server.id])
        ]

        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        result = self.cmd.take_action(parsed_args)

        self.servers_mock.delete.assert_called_once_with(
            self.share_server)
        self.assertIsNone(result)

    def test_share_server_delete_wait(self):
        arglist = [
            self.share_server.id,
            '--wait'
        ]
        verifylist = [
            ('share_servers', [self.share_server.id]),
            ('wait', True)
        ]

        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        with mock.patch('osc_lib.utils.wait_for_delete', return_value=True):
            result = self.cmd.take_action(parsed_args)

            self.servers_mock.delete.assert_called_once_with(
                self.share_server)
            self.assertIsNone(result)

    def test_share_server_delete_wait_exception(self):
        arglist = [
            self.share_server.id,
            '--wait'
        ]
        verifylist = [
            ('share_servers', [self.share_server.id]),
            ('wait', True)
        ]

        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        with mock.patch('osc_lib.utils.wait_for_delete', return_value=False):
            self.assertRaises(
                exceptions.CommandError,
                self.cmd.take_action,
                parsed_args
            )


class TestShowShareServer(TestShareServer):

    def setUp(self):
        super(TestShowShareServer, self).setUp()

        self.share_server = (
            manila_fakes.FakeShareServer.create_one_server())
        self.servers_mock.get.return_value = self.share_server

        self.cmd = osc_share_servers.ShowShareServer(self.app, None)

        self.data = tuple(self.share_server._info.values())
        self.columns = tuple(self.share_server._info.keys())

    def test_share_server_show_missing_args(self):
        arglist = []
        verifylist = []

        self.assertRaises(
            osc_utils.ParserException,
            self.check_parser, self.cmd, arglist, verifylist)

    def test_share_server_show(self):
        arglist = [
            self.share_server.id
        ]
        verifylist = [
            ('share_server', self.share_server.id)
        ]

        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        columns, data = self.cmd.take_action(parsed_args)

        self.servers_mock.get.assert_called_with(
            self.share_server.id
        )

        self.assertCountEqual(self.columns, columns)
        self.assertCountEqual(self.data, data)


class TestListShareServer(TestShareServer):

    columns = [
        'ID',
        'Host',
        'Status',
        'Share Network ID',
        'Project ID',
    ]

    def setUp(self):
        super(TestListShareServer, self).setUp()

        self.servers_list = (
            manila_fakes.FakeShareServer.create_share_servers(
                count=2))
        self.servers_mock.list.return_value = self.servers_list

        self.values = (oscutils.get_dict_properties(
            i._info, self.columns) for i in self.servers_list)

        self.cmd = osc_share_servers.ListShareServer(self.app, None)

    def test_list_share_server(self):
        arglist = []
        verifylist = []

        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        columns, data = self.cmd.take_action(parsed_args)

        self.servers_mock.list.assert_called_with(search_opts={
            'status': None,
            'host': None,
            'project_id': None,
        })

        self.assertEqual(self.columns, columns)
        self.assertEqual(list(self.values), list(data))

    def test_share_server_list_by_status(self):
        arglist = [
            '--status', self.servers_list[0].status,
        ]
        verifylist = [
            ('status', self.servers_list[0].status),
        ]
        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        columns, data = self.cmd.take_action(parsed_args)

        search_opts = {
            'status': None,
            'host': None,
            'project_id': None,
        }

        self.servers_mock.list.assert_called_once_with(
            search_opts=search_opts,
        )

        self.assertEqual(self.columns, columns)
        self.assertEqual(list(self.values), list(data))

    def test_share_server_list_by_source_share_server(self):
        expected_source_share_server_id = (
            self.servers_list[0].source_share_server_id
        )
        arglist = [
            '--source-share-server-id', expected_source_share_server_id,
        ]
        verifylist = [
            ('source_share_server_id', expected_source_share_server_id),
        ]
        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        columns, data = self.cmd.take_action(parsed_args)

        search_opts = {
            'status': None,
            'host': None,
            'project_id': None,
            'source_share_server_id': expected_source_share_server_id,
        }

        self.servers_mock.list.assert_called_once_with(
            search_opts=search_opts,
        )

        self.assertEqual(self.columns, columns)
        self.assertEqual(list(self.values), list(data))

    def test_share_server_list_by_identifier(self):
        expected_identifier = self.servers_list[0].identifier
        arglist = ['--identifier', expected_identifier,]
        verifylist = [('identifier', expected_identifier),]
        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        columns, data = self.cmd.take_action(parsed_args)

        search_opts = {
            'status': None,
            'host': None,
            'project_id': None,
            'identifier': expected_identifier,
        }

        self.servers_mock.list.assert_called_once_with(
            search_opts=search_opts,
        )

        self.assertEqual(self.columns, columns)
        self.assertEqual(list(self.values), list(data))


class TestAdoptShareServer(TestShareServer):

    def setUp(self):
        super(TestAdoptShareServer, self).setUp()

        self.share_server = (
            manila_fakes.FakeShareServer.create_one_server(
                attrs={'status': 'available'}
            ))
        self.servers_mock.get.return_value = self.share_server
        self.servers_mock.manage.return_value = self.share_server
        self.share_network_subnets_mock = (
            self.app.client_manager.share.share_network_subnets)

        self.share_network = (
            manila_fakes.FakeShareNetwork.create_one_share_network(
                attrs={'status': 'available'}
            ))
        self.share_network_subnet = (
            manila_fakes.FakeShareNetworkSubnet.create_one_share_subnet())

        self.share_networks_mock.get.return_value = self.share_network
        self.share_network_subnets_mock.get.return_value = (
            self.share_network_subnet)

        self.cmd = osc_share_servers.AdoptShareServer(self.app, None)

        self.data = tuple(self.share_server._info.values())
        self.columns = tuple(self.share_server._info.keys())

    def test_share_server_adopt_missing_args(self):
        arglist = []
        verifylist = []

        self.assertRaises(osc_utils.ParserException,
                          self.check_parser, self.cmd, arglist, verifylist)

    def test_share_server_adopt(self):
        arglist = [
            'somehost@backend',
            self.share_network['id'],
            'share_server_identifier',
            '--share-network-subnet', self.share_network_subnet['id'],
        ]
        verifylist = [
            ('host', 'somehost@backend'),
            ('share_network', self.share_network['id']),
            ('identifier', 'share_server_identifier'),
            ('share_network_subnet', self.share_network_subnet['id']),
        ]

        parsed_args = self.check_parser(self.cmd, arglist, verifylist)
        columns, data = self.cmd.take_action(parsed_args)
        self.servers_mock.manage.assert_called_with(
            host='somehost@backend',
            share_network_id=self.share_network['id'],
            identifier='share_server_identifier',
            driver_options={},
            share_network_subnet_id=self.share_network_subnet['id'],
        )
        self.assertCountEqual(self.columns, columns)
        self.assertCountEqual(self.data, data)

    def test_share_server_adopt_wait(self):
        arglist = [
            'somehost@backend',
            self.share_network['id'],
            'share_server_identifier',
            '--share-network-subnet', self.share_network_subnet['id'],
            '--wait'
        ]
        verifylist = [
            ('host', 'somehost@backend'),
            ('share_network', self.share_network['id']),
            ('identifier', 'share_server_identifier'),
            ('share_network_subnet', self.share_network_subnet['id']),
            ('wait', True)
        ]

        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        with mock.patch('osc_lib.utils.wait_for_status', return_value=True):
            self.cmd.take_action(parsed_args)
            self.servers_mock.manage.assert_called_with(
                host='somehost@backend',
                share_network_id=self.share_network['id'],
                identifier='share_server_identifier',
                driver_options={},
                share_network_subnet_id=self.share_network_subnet['id']
            )

    def test_share_server_adopt_subnet_not_supported(self):
        arglist = [
            'somehost@backend',
            self.share_network['id'],
            'share_server_identifier',
            '--share-network-subnet', self.share_network_subnet['id'],
            '--wait'
        ]
        verifylist = [
            ('host', 'somehost@backend'),
            ('share_network', self.share_network['id']),
            ('identifier', 'share_server_identifier'),
            ('share_network_subnet', self.share_network_subnet['id']),
            ('wait', True)
        ]
        self.app.client_manager.share.api_version = api_versions.APIVersion(
            "2.50")

        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        self.assertRaises(exceptions.CommandError,
                          self.cmd.take_action,
                          parsed_args)


class TestAbandonShareServer(TestShareServer):

    def setUp(self):
        super(TestAbandonShareServer, self).setUp()

        self.share_server = (
            manila_fakes.FakeShareServer.create_one_server())
        self.servers_mock.get.return_value = self.share_server

        self.cmd = osc_share_servers.AbandonShareServer(self.app, None)

        self.data = tuple(self.share_server._info.values())
        self.columns = tuple(self.share_server._info.keys())

    def test_share_server_abandon_missing_args(self):
        arglist = []
        verifylist = []

        self.assertRaises(osc_utils.ParserException,
                          self.check_parser, self.cmd, arglist, verifylist)

    def test_share_server_abandon(self):
        arglist = [
            self.share_server.id
        ]
        verifylist = [
            ('share_server', [self.share_server.id])
        ]

        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        result = self.cmd.take_action(parsed_args)

        self.servers_mock.unmanage.assert_called_with(
            self.share_server)
        self.assertIsNone(result)

    def test_share_server_abandon_multiple(self):
        share_servers = (
            manila_fakes.FakeShareServer.create_share_servers(
                count=2))
        arglist = [
            share_servers[0].id,
            share_servers[1].id
        ]
        verifylist = [
            ('share_server', [share_servers[0].id, share_servers[1].id])
        ]
        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        result = self.cmd.take_action(parsed_args)

        self.assertEqual(self.servers_mock.unmanage.call_count,
                         len(share_servers))
        self.assertIsNone(result)

    def test_share_server_abandon_force(self):
        arglist = [
            self.share_server.id,
            '--force'
        ]
        verifylist = [
            ('share_server', [self.share_server.id]),
            ('force', True)
        ]

        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        result = self.cmd.take_action(parsed_args)

        self.servers_mock.unmanage.assert_called_with(
            self.share_server,
            force=True)
        self.assertIsNone(result)

    def test_share_server_abandon_force_exception(self):
        arglist = [
            self.share_server.id,
        ]
        verifylist = [
            ('share_server', [self.share_server.id]),
        ]

        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        self.servers_mock.unmanage.side_effect = exceptions.CommandError()
        self.assertRaises(exceptions.CommandError,
                          self.cmd.take_action,
                          parsed_args)

    def test_share_server_abandon_wait(self):
        arglist = [
            self.share_server.id,
            '--wait'
        ]
        verifylist = [
            ('share_server', [self.share_server.id]),
            ('wait', True)
        ]

        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        with mock.patch('osc_lib.utils.wait_for_delete', return_value=True):
            result = self.cmd.take_action(parsed_args)
            self.servers_mock.unmanage.assert_called_with(
                self.share_server)
            self.assertIsNone(result)

    def test_share_server_abandon_wait_error(self):
        arglist = [
            self.share_server.id,
            '--wait'
        ]
        verifylist = [
            ('share_server', [self.share_server.id]),
            ('wait', True)
        ]

        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        with mock.patch('osc_lib.utils.wait_for_delete', return_value=False):
            self.assertRaises(
                exceptions.CommandError,
                self.cmd.take_action,
                parsed_args)


class TestSetShareServer(TestShareServer):

    def setUp(self):
        super(TestSetShareServer, self).setUp()

        self.share_server = (
            manila_fakes.FakeShareServer.create_one_server(
                methods={'reset_task_state': None}
            )
        )
        self.servers_mock.get.return_value = self.share_server

        self.cmd = osc_share_servers.SetShareServer(self.app, None)

    def test_share_server_set_status(self):
        arglist = [
            self.share_server.id,
            '--status', 'active'
        ]
        verifylist = [
            ('share_server', self.share_server.id),
            ('status', 'active')
        ]
        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        result = self.cmd.take_action(parsed_args)

        self.servers_mock.reset_state.assert_called_with(
            self.share_server,
            parsed_args.status)
        self.assertIsNone(result)

    def test_share_server_set_task_state(self):
        arglist = [
            self.share_server.id,
            '--task-state', 'migration_in_progress'
        ]
        verifylist = [
            ('share_server', self.share_server.id),
            ('task_state', 'migration_in_progress')
        ]

        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        result = self.cmd.take_action(parsed_args)

        self.servers_mock.reset_task_state.assert_called_with(
            self.share_server,
            parsed_args.task_state)
        self.assertIsNone(result)

    def test_share_server_set_status_exception(self):
        arglist = [
            self.share_server.id,
            '--status', 'active'
        ]
        verifylist = [
            ('share_server', self.share_server.id),
            ('status', 'active')
        ]
        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        self.servers_mock.reset_state.side_effect = Exception()

        self.assertRaises(
            exceptions.CommandError,
            self.cmd.take_action,
            parsed_args)


class TestShareServerMigrationCancel(TestShareServer):

    def setUp(self):
        super(TestShareServerMigrationCancel, self).setUp()

        self.share_server = (
            manila_fakes.FakeShareServer.create_one_server(
                attrs={
                    'status': 'migrating',
                },
                methods={'migration_cancel': None}
            )
        )
        self.servers_mock.get.return_value = self.share_server

        # Get the command objects to test
        self.cmd = osc_share_servers.ShareServerMigrationCancel(self.app, None)

    def test_share_server_migration_cancel(self):
        arglist = [
            self.share_server.id
        ]
        verifylist = [
            ('share_server', self.share_server.id)
        ]
        parsed_args = self.check_parser(self.cmd, arglist, verifylist)
        self.cmd.take_action(parsed_args)
        self.share_server.migration_cancel.assert_called


class TestShareServerMigrationComplete(TestShareServer):

    def setUp(self):
        super(TestShareServerMigrationComplete, self).setUp()

        self.share_server = (
            manila_fakes.FakeShareServer.create_one_server(
                attrs={
                    'status': 'migrating',
                },
                methods={'migration_complete': None}
            )
        )
        self.servers_mock.get.return_value = self.share_server

        # Get the command objects to test
        self.cmd = osc_share_servers.ShareServerMigrationComplete(
            self.app, None)

    def test_share_server_migration_complete(self):
        arglist = [
            self.share_server.id
        ]
        verifylist = [
            ('share_server', self.share_server.id)
        ]
        parsed_args = self.check_parser(self.cmd, arglist, verifylist)
        self.cmd.take_action(parsed_args)
        self.share_server.migration_complete.assert_called


class TestShareServerMigrationShow(TestShareServer):

    def setUp(self):
        super(TestShareServerMigrationShow, self).setUp()

        self.new_share_network = manila_fakes.FakeShareNetwork \
            .create_one_share_network()
        self.share_networks_mock.get.return_value = self.new_share_network

        self.share_server = (
            manila_fakes.FakeShareServer.create_one_server(
                attrs={
                    'status': 'migrating',
                    'task_state': 'migration_in_progress'
                },
                methods={'migration_get_progress': None}
            )
        )
        self.servers_mock.get.return_value = self.share_server

        # Get the command objects to test
        self.cmd = osc_share_servers.ShareServerMigrationShow(self.app, None)

    def test_share_server_migration_show(self):
        arglist = [
            self.share_server.id
        ]
        verifylist = [
            ('share_server', self.share_server.id)
        ]
        parsed_args = self.check_parser(self.cmd, arglist, verifylist)
        self.cmd.take_action(parsed_args)
        self.share_server.migration_get_progress.assert_called


class TestShareServerMigrationStart(TestShareServer):
    def setUp(self):
        super(TestShareServerMigrationStart, self).setUp()

        self.new_share_network = manila_fakes.FakeShareNetwork \
            .create_one_share_network()
        self.share_networks_mock.get.return_value = self.new_share_network

        self.share_server = (
            manila_fakes.FakeShareServer.create_one_server(
                attrs={
                    'check_only': 'False',
                },
                methods={'migration_start': None, 'migration_check': None}
            ))
        self.servers_mock.get.return_value = self.share_server

        # Get the command objects to test
        self.cmd = osc_share_servers.ShareServerMigrationStart(self.app, None)

    def test_share_server_migration_start_with_new_share_network(self):
        """Test share server migration with new_share_network"""

        arglist = [
            '1234',
            'host@backend',
            '--preserve-snapshots', 'False',
            '--writable', 'False',
            '--nondisruptive', 'False',
            '--new-share-network', self.new_share_network.id
        ]

        verifylist = [
            ('share_server', '1234'),
            ('host', 'host@backend'),
            ('preserve_snapshots', 'False'),
            ('writable', 'False'),
            ('nondisruptive', 'False'),
            ('new_share_network', self.new_share_network.id)
        ]

        self.app.client_manager.share.api_version = api_versions.APIVersion(
            "2.57")
        parsed_args = self.check_parser(self.cmd, arglist, verifylist)
        result = self.cmd.take_action(parsed_args)

        self.share_server.migration_start.assert_called_with(
            'host@backend',
            'False',
            'False',
            'False',
            self.new_share_network.id
        )
        self.assertEqual(result, ({}, {}))

    def test_share_server_migration_start_with_check_only(self):
        """Test share server migration start with check only"""

        arglist = [
            '1234',
            'host@backend',
            '--preserve-snapshots', 'True',
            '--writable', 'True',
            '--nondisruptive', 'False',
            '--new-share-network', self.new_share_network.id,
            '--check-only',
        ]

        verifylist = [
            ('share_server', '1234'),
            ('host', 'host@backend'),
            ('preserve_snapshots', 'True'),
            ('writable', 'True'),
            ('nondisruptive', 'False'),
            ('new_share_network', self.new_share_network.id),
            ('check_only', True)
        ]

        expected_result = {
            'compatible': True,
            'requested_capabilities': {
                'writable': 'True',
                'nondisruptive': 'False',
                'preserve_snapshots': 'True',
                'share_network_id': None,
                'host': 'host@backend'
            },
            'supported_capabilities': {
                'writable': True,
                'nondisruptive': False,
                'preserve_snapshots': True,
                'share_network_id': self.new_share_network.id,
                'migration_cancel': True,
                'migration_get_progress': True
            }
        }

        self.share_server.migration_check.return_value = expected_result

        self.app.client_manager.share.api_version = api_versions.APIVersion(
            "2.57")
        parsed_args = self.check_parser(self.cmd, arglist, verifylist)
        columns, data = self.cmd.take_action(parsed_args)

        self.share_server.migration_check.assert_called_with(
            'host@backend',
            'True',
            'False',
            'True',
            self.new_share_network.id,

        )
        result_dict = {}
        for count, column in enumerate(columns):
            result_dict[column] = data[count]
        self.assertEqual(expected_result, result_dict)

    def test_share_server_migration_start_with_api_version_exception(self):
        """Test share server migration start with API microversion exception"""

        self.app.client_manager.share.api_version = api_versions.APIVersion(
            "2.50")
        arglist = [
            '1234',
            'host@backend',
            '--preserve-snapshots', 'False',
            '--writable', 'False',
            '--nondisruptive', 'False',
            '--new-share-network', self.new_share_network.id
        ]

        verifylist = [
            ('share_server', '1234'),
            ('host', 'host@backend'),
            ('preserve_snapshots', 'False'),
            ('writable', 'False'),
            ('nondisruptive', 'False'),
            ('new_share_network', self.new_share_network.id)
        ]

        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        self.assertRaises(
            exceptions.CommandError,
            self.cmd.take_action,
            parsed_args)
