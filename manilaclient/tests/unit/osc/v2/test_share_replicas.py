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
from manilaclient.api_versions import MAX_VERSION
from manilaclient.common import cliutils

from manilaclient.osc import utils
from manilaclient.osc.v2 import share_replicas as osc_share_replicas

from manilaclient.tests.unit.osc import osc_utils
from manilaclient.tests.unit.osc.v2 import fakes as manila_fakes


class TestShareReplica(manila_fakes.TestShare):

    def setUp(self):
        super(TestShareReplica, self).setUp()

        self.shares_mock = self.app.client_manager.share.shares
        self.shares_mock.reset_mock()

        self.replicas_mock = self.app.client_manager.share.share_replicas
        self.replicas_mock.reset_mock()
        self.app.client_manager.share.api_version = api_versions.APIVersion(
            MAX_VERSION)

        self.replica_el_mock = (
            self.app.client_manager
                .share.share_replica_export_locations)
        self.replica_el_mock.reset_mock()


class TestShareReplicaCreate(TestShareReplica):

    def setUp(self):
        super(TestShareReplicaCreate, self).setUp()

        self.share = manila_fakes.FakeShare.create_one_share()
        self.shares_mock.get.return_value = self.share

        self.share_replica = (
            manila_fakes.FakeShareReplica.create_one_replica(
                attrs={
                    'availability_zone': 'manila-zone-1',
                    'status': 'available'}
            ))
        self.replicas_mock.create.return_value = self.share_replica
        self.replicas_mock.get.return_value = self.share_replica

        self.cmd = osc_share_replicas.CreateShareReplica(self.app, None)

        self.data = tuple(self.share_replica._info.values())
        self.columns = tuple(self.share_replica._info.keys())

    def test_share_replica_create_missing_args(self):
        arglist = []
        verifylist = []

        self.assertRaises(
            osc_utils.ParserException,
            self.check_parser, self.cmd, arglist, verifylist)

    def test_share_replica_create(self):
        arglist = [
            self.share.id
        ]
        verifylist = [
            ('share', self.share.id)
        ]

        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        columns, data = self.cmd.take_action(parsed_args)

        self.replicas_mock.create.assert_called_with(
            share=self.share,
            availability_zone=None
        )

        self.assertCountEqual(self.columns, columns)
        self.assertCountEqual(self.data, data)

    def test_share_replica_create_az(self):
        arglist = [
            self.share.id,
            '--availability-zone', self.share.availability_zone
        ]
        verifylist = [
            ('share', self.share.id),
            ('availability_zone', self.share.availability_zone)
        ]

        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        columns, data = self.cmd.take_action(parsed_args)

        self.replicas_mock.create.assert_called_with(
            share=self.share,
            availability_zone=self.share.availability_zone
        )

        self.assertCountEqual(self.columns, columns)
        self.assertCountEqual(self.data, data)

    def test_share_replica_create_scheduler_hint_valid(self):
        arglist = [
            self.share.id,
            '--availability-zone', self.share.availability_zone,
            '--scheduler-hint', ('only_host=host1@backend1#pool1'),
        ]
        verifylist = [
            ('share', self.share.id),
            ('availability_zone', self.share.availability_zone),
            ('scheduler_hint', {'only_host': 'host1@backend1#pool1'})
        ]

        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        columns, data = self.cmd.take_action(parsed_args)

        self.replicas_mock.create.assert_called_with(
            share=self.share,
            availability_zone=self.share.availability_zone,
            scheduler_hints={'only_host': 'host1@backend1#pool1'}
        )

        self.assertCountEqual(self.columns, columns)
        self.assertCountEqual(self.data, data)

    def test_share_replica_create_scheduler_hint_invalid_hint(self):
        arglist = [
            self.share.id,
            '--availability-zone', self.share.availability_zone,
            '--scheduler-hint', 'fake_hint=host1@backend1#pool1'
        ]
        verifylist = [
            ('share', self.share.id),
            ('availability_zone', self.share.availability_zone),
            ('scheduler_hint', {'fake_hint': 'host1@backend1#pool1'})
        ]

        parsed_args = self.check_parser(self.cmd, arglist, verifylist)
        self.assertRaises(exceptions.CommandError,
                          self.cmd.take_action,
                          parsed_args)

    def test_share_replica_create_scheduler_hint_invalid_version(self):
        self.app.client_manager.share.api_version = api_versions.APIVersion(
            "2.66")

        arglist = [
            self.share.id,
            '--availability-zone', self.share.availability_zone,
            '--scheduler-hint', 'only_host=host1@backend1#pool1'
        ]
        verifylist = [
            ('share', self.share.id),
            ('availability_zone', self.share.availability_zone),
            ('scheduler_hint', {'only_host': 'host1@backend1#pool1'})
        ]

        parsed_args = self.check_parser(self.cmd, arglist, verifylist)
        self.assertRaises(exceptions.CommandError,
                          self.cmd.take_action,
                          parsed_args)

    def test_share_replica_create_wait(self):
        arglist = [
            self.share.id,
            '--wait'
        ]
        verifylist = [
            ('share', self.share.id),
            ('wait', True)
        ]

        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        columns, data = self.cmd.take_action(parsed_args)

        self.replicas_mock.create.assert_called_with(
            share=self.share,
            availability_zone=None
        )

        self.replicas_mock.get.assert_called_with(self.share_replica.id)
        self.assertCountEqual(self.columns, columns)
        self.assertCountEqual(self.data, data)

    @mock.patch('manilaclient.osc.v2.share_replicas.LOG')
    def test_share_replica_create_wait_exception(self, mock_logger):
        arglist = [
            self.share.id,
            '--wait'
        ]
        verifylist = [
            ('share', self.share.id),
            ('wait', True)
        ]

        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        with mock.patch('osc_lib.utils.wait_for_status', return_value=False):
            columns, data = self.cmd.take_action(parsed_args)

            self.replicas_mock.create.assert_called_with(
                share=self.share,
                availability_zone=None
            )

            mock_logger.error.assert_called_with(
                "ERROR: Share replica is in error state.")

            self.replicas_mock.get.assert_called_with(self.share_replica.id)
            self.assertCountEqual(self.columns, columns)
            self.assertCountEqual(self.data, data)


class TestShareReplicaDelete(TestShareReplica):

    def setUp(self):
        super(TestShareReplicaDelete, self).setUp()

        self.share_replica = (
            manila_fakes.FakeShareReplica.create_one_replica())
        self.replicas_mock.get.return_value = self.share_replica

        self.cmd = osc_share_replicas.DeleteShareReplica(self.app, None)

    def test_share_replica_delete_missing_args(self):
        arglist = []
        verifylist = []

        self.assertRaises(osc_utils.ParserException,
                          self.check_parser, self.cmd, arglist, verifylist)

    def test_share_replica_delete(self):
        arglist = [
            self.share_replica.id
        ]
        verifylist = [
            ('replica', [self.share_replica.id])
        ]

        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        result = self.cmd.take_action(parsed_args)

        self.replicas_mock.delete.assert_called_with(
            self.share_replica,
            force=False)
        self.assertIsNone(result)

    def test_share_replica_delete_force(self):
        arglist = [
            self.share_replica.id,
            '--force'
        ]
        verifylist = [
            ('replica', [self.share_replica.id]),
            ('force', True)
        ]

        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        result = self.cmd.take_action(parsed_args)

        self.replicas_mock.delete.assert_called_with(
            self.share_replica,
            force=True)
        self.assertIsNone(result)

    def test_share_replica_delete_multiple(self):
        share_replicas = (
            manila_fakes.FakeShareReplica.create_share_replicas(
                count=2))
        arglist = [
            share_replicas[0].id,
            share_replicas[1].id
        ]
        verifylist = [
            ('replica', [share_replicas[0].id, share_replicas[1].id])
        ]
        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        result = self.cmd.take_action(parsed_args)

        self.assertEqual(self.replicas_mock.delete.call_count,
                         len(share_replicas))
        self.assertIsNone(result)

    def test_share_snapshot_delete_exception(self):
        arglist = [
            self.share_replica.id
        ]
        verifylist = [
            ('replica', [self.share_replica.id])
        ]

        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        self.replicas_mock.delete.side_effect = exceptions.CommandError()
        self.assertRaises(exceptions.CommandError,
                          self.cmd.take_action,
                          parsed_args)

    def test_share_replica_delete_wait(self):
        arglist = [
            self.share_replica.id,
            '--wait'
        ]
        verifylist = [
            ('replica', [self.share_replica.id]),
            ('wait', True)
        ]

        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        with mock.patch('osc_lib.utils.wait_for_delete', return_value=True):
            result = self.cmd.take_action(parsed_args)

            self.replicas_mock.delete.assert_called_with(
                self.share_replica,
                force=False)
            self.replicas_mock.get.assert_called_with(self.share_replica.id)
            self.assertIsNone(result)

    def test_share_replica_delete_wait_exception(self):
        arglist = [
            self.share_replica.id,
            '--wait'
        ]
        verifylist = [
            ('replica', [self.share_replica.id]),
            ('wait', True)
        ]

        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        with mock.patch('osc_lib.utils.wait_for_delete', return_value=False):
            self.assertRaises(
                exceptions.CommandError,
                self.cmd.take_action,
                parsed_args
            )


class TestShareReplicaList(TestShareReplica):

    columns = [
        'id',
        'status',
        'replica_state',
        'share_id',
        'host',
        'availability_zone',
        'updated_at',
    ]

    column_headers = utils.format_column_headers(columns)

    def setUp(self):
        super(TestShareReplicaList, self).setUp()

        self.share = manila_fakes.FakeShare.create_one_share()
        self.shares_mock.get.return_value = self.share

        self.replicas_list = (
            manila_fakes.FakeShareReplica.create_share_replicas(
                count=2))
        self.replicas_mock.list.return_value = self.replicas_list

        self.values = (oscutils.get_dict_properties(
            i._info, self.columns) for i in self.replicas_list)

        self.cmd = osc_share_replicas.ListShareReplica(self.app, None)

    def test_share_replica_list(self):
        arglist = []
        verifylist = []

        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        columns, data = self.cmd.take_action(parsed_args)

        self.replicas_mock.list.assert_called_with(share=None)

        self.assertEqual(self.column_headers, columns)
        self.assertEqual(list(self.values), list(data))

    def test_share_replica_list_for_share(self):
        arglist = [
            '--share', self.share.id
        ]
        verifylist = [
            ('share', self.share.id)
        ]

        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        columns, data = self.cmd.take_action(parsed_args)

        self.replicas_mock.list.assert_called_with(share=self.share)

        self.assertEqual(self.column_headers, columns)
        self.assertEqual(list(self.values), list(data))


class TestShareReplicaShow(TestShareReplica):

    def setUp(self):
        super(TestShareReplicaShow, self).setUp()

        self.share_replica = (
            manila_fakes.FakeShareReplica.create_one_replica()
        )
        self.replicas_mock.get.return_value = self.share_replica

        self.replica_el_list = (
            manila_fakes.FakeShareExportLocation.
            create_share_export_locations(count=2)
        )

        self.replica_el_mock.list.return_value = (
            self.replica_el_list)

        self.cmd = osc_share_replicas.ShowShareReplica(self.app, None)

        self.share_replica._info['export_locations'] = (
            cliutils.convert_dict_list_to_string(
                self.replica_el_list))

        self.data = tuple(self.share_replica._info.values())
        self.columns = tuple(self.share_replica._info.keys())

    def test_share_replica_show_missing_args(self):
        arglist = []
        verifylist = []

        self.assertRaises(
            osc_utils.ParserException,
            self.check_parser, self.cmd, arglist, verifylist)

    def test_share_replica_show(self):
        arglist = [
            self.share_replica.id
        ]
        verifylist = [
            ('replica', self.share_replica.id)
        ]

        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        columns, data = self.cmd.take_action(parsed_args)

        self.replicas_mock.get.assert_called_with(
            self.share_replica.id
        )

        self.assertCountEqual(self.columns, columns)
        self.assertCountEqual(self.data, data)


class TestShareReplicaSet(TestShareReplica):

    def setUp(self):
        super(TestShareReplicaSet, self).setUp()

        self.share_replica = (
            manila_fakes.FakeShareReplica.create_one_replica()
        )
        self.replicas_mock.get.return_value = self.share_replica

        self.cmd = osc_share_replicas.SetShareReplica(self.app, None)

    def test_share_replica_set_replica_state(self):
        new_replica_state = 'in_sync'
        arglist = [
            self.share_replica.id,
            '--replica-state', new_replica_state
        ]
        verifylist = [
            ('replica', self.share_replica.id),
            ('replica_state', new_replica_state)
        ]
        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        result = self.cmd.take_action(parsed_args)

        self.replicas_mock.reset_replica_state.assert_called_with(
            self.share_replica,
            new_replica_state)
        self.assertIsNone(result)

    def test_share_replica_set_replica_state_exception(self):
        new_replica_state = 'in_sync'
        arglist = [
            self.share_replica.id,
            '--replica-state', new_replica_state
        ]
        verifylist = [
            ('replica', self.share_replica.id),
            ('replica_state', new_replica_state)
        ]
        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        self.replicas_mock.reset_replica_state.side_effect = Exception()

        self.assertRaises(
            exceptions.CommandError,
            self.cmd.take_action,
            parsed_args)

    def test_share_replica_set_status(self):
        new_status = 'available'
        arglist = [
            self.share_replica.id,
            '--status', new_status
        ]
        verifylist = [
            ('replica', self.share_replica.id),
            ('status', new_status)
        ]
        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        result = self.cmd.take_action(parsed_args)

        self.replicas_mock.reset_state.assert_called_with(
            self.share_replica,
            new_status)
        self.assertIsNone(result)

    def test_share_replica_set_status_exception(self):
        new_status = 'available'
        arglist = [
            self.share_replica.id,
            '--status', new_status
        ]
        verifylist = [
            ('replica', self.share_replica.id),
            ('status', new_status)
        ]
        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        self.replicas_mock.reset_state.side_effect = Exception()

        self.assertRaises(
            exceptions.CommandError,
            self.cmd.take_action,
            parsed_args)

    def test_share_replica_set_nothing_defined(self):
        arglist = [
            self.share_replica.id,
        ]
        verifylist = [
            ('replica', self.share_replica.id),
        ]
        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        self.assertRaises(
            exceptions.CommandError,
            self.cmd.take_action,
            parsed_args)


class TestShareReplicaPromote(TestShareReplica):

    def setUp(self):
        super(TestShareReplicaPromote, self).setUp()

        self.share_replica = (
            manila_fakes.FakeShareReplica.create_one_replica()
        )
        self.replicas_mock.get.return_value = self.share_replica

        self.cmd = osc_share_replicas.PromoteShareReplica(
            self.app, None)

    def test_share_replica_promote(self):
        arglist = [
            self.share_replica.id,
        ]
        verifylist = [
            ('replica', self.share_replica.id),
        ]
        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        result = self.cmd.take_action(parsed_args)

        self.replicas_mock.promote.assert_called_with(
            self.share_replica)
        self.assertIsNone(result)

    def test_share_replica_promote_exception(self):
        arglist = [
            self.share_replica.id,
        ]
        verifylist = [
            ('replica', self.share_replica.id),
        ]
        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        self.replicas_mock.promote.side_effect = Exception()

        self.assertRaises(
            exceptions.CommandError,
            self.cmd.take_action,
            parsed_args)


class TestShareReplicaResync(TestShareReplica):

    def setUp(self):
        super(TestShareReplicaResync, self).setUp()

        self.share_replica = (
            manila_fakes.FakeShareReplica.create_one_replica()
        )
        self.replicas_mock.get.return_value = self.share_replica

        self.cmd = osc_share_replicas.ResyncShareReplica(
            self.app, None)

    def test_share_replica_resync(self):
        arglist = [
            self.share_replica.id,
        ]
        verifylist = [
            ('replica', self.share_replica.id),
        ]
        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        result = self.cmd.take_action(parsed_args)

        self.replicas_mock.resync.assert_called_with(
            self.share_replica)
        self.assertIsNone(result)

    def test_share_replica_resync_exception(self):
        arglist = [
            self.share_replica.id,
        ]
        verifylist = [
            ('replica', self.share_replica.id),
        ]
        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        self.replicas_mock.resync.side_effect = Exception()

        self.assertRaises(
            exceptions.CommandError,
            self.cmd.take_action,
            parsed_args)
