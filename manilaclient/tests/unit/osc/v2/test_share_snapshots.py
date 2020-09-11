#   Copyright 2019 Red Hat Inc. All rights reserved.
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
import uuid

from osc_lib import exceptions
from osc_lib import utils as oscutils

from manilaclient import api_versions
from manilaclient.common import cliutils
from manilaclient.osc.v2 import share_snapshots as osc_share_snapshots
from manilaclient.tests.unit.osc import osc_utils
from manilaclient.tests.unit.osc.v2 import fakes as manila_fakes

COLUMNS = ['ID', 'Name']

COLUMNS_DETAIL = [
    'ID',
    'Name',
    'Status',
    'Description',
    'Created At',
    'Size',
    'Share ID',
    'Share Proto',
    'Share Size',
    'User ID'
]


class TestShareSnapshot(manila_fakes.TestShare):

    def setUp(self):
        super(TestShareSnapshot, self).setUp()

        self.shares_mock = self.app.client_manager.share.shares
        self.shares_mock.reset_mock()

        self.snapshots_mock = self.app.client_manager.share.share_snapshots
        self.snapshots_mock.reset_mock()
        self.app.client_manager.share.api_version = api_versions.APIVersion(
            "2.51")


class TestShareSnapshotCreate(TestShareSnapshot):

    def setUp(self):
        super(TestShareSnapshotCreate, self).setUp()

        self.share = manila_fakes.FakeShare.create_one_share()
        self.shares_mock.create.return_value = self.share

        self.shares_mock.get.return_value = self.share

        self.share_snapshot = (
            manila_fakes.FakeShareSnapshot.create_one_snapshot())
        self.snapshots_mock.create.return_value = self.share_snapshot

        self.cmd = osc_share_snapshots.CreateShareSnapshot(self.app, None)

        self.data = tuple(self.share_snapshot._info.values())
        self.columns = tuple(self.share_snapshot._info.keys())

    def test_share_snapshot_create_missing_args(self):
        arglist = []
        verifylist = []

        self.assertRaises(osc_utils.ParserException,
                          self.check_parser, self.cmd, arglist, verifylist)

    def test_share_snapshot_create_required_args(self):
        arglist = [
            self.share.id
        ]
        verifylist = [
            ('share', self.share.id)
        ]

        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        columns, data = self.cmd.take_action(parsed_args)

        self.snapshots_mock.create.assert_called_with(
            share=self.share,
            force=False,
            name=None,
            description=None
        )

        self.assertCountEqual(self.columns, columns)
        self.assertCountEqual(self.data, data)

    def test_share_snapshot_create_force(self):
        arglist = [
            self.share.id,
            '--force'
        ]
        verifylist = [
            ('share', self.share.id),
            ('force', True)
        ]

        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        columns, data = self.cmd.take_action(parsed_args)

        self.snapshots_mock.create.assert_called_with(
            share=self.share,
            force=True,
            name=None,
            description=None
        )

        self.assertCountEqual(columns, columns)
        self.assertCountEqual(self.data, data)

    def test_share_snapshot_create(self):
        arglist = [
            self.share.id,
            '--name', self.share_snapshot.name,
            '--description', self.share_snapshot.description
        ]
        verifylist = [
            ('share', self.share.id),
            ('name', self.share_snapshot.name),
            ('description', self.share_snapshot.description)
        ]

        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        columns, data = self.cmd.take_action(parsed_args)

        self.snapshots_mock.create.assert_called_with(
            share=self.share,
            force=False,
            name=self.share_snapshot.name,
            description=self.share_snapshot.description
        )

        self.assertCountEqual(self.columns, columns)
        self.assertCountEqual(self.data, data)


class TestShareSnapshotDelete(TestShareSnapshot):

    def setUp(self):
        super(TestShareSnapshotDelete, self).setUp()

        self.share_snapshot = (
            manila_fakes.FakeShareSnapshot.create_one_snapshot())

        self.snapshots_mock.get.return_value = self.share_snapshot

        self.cmd = osc_share_snapshots.DeleteShareSnapshot(self.app, None)

    def test_share_snapshot_delete_missing_args(self):
        arglist = []
        verifylist = []

        self.assertRaises(osc_utils.ParserException,
                          self.check_parser, self.cmd, arglist, verifylist)

    def test_share_snapshot_delete(self):
        arglist = [
            self.share_snapshot.id
        ]
        verifylist = [
            ('snapshot', [self.share_snapshot.id])
        ]

        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        result = self.cmd.take_action(parsed_args)

        self.snapshots_mock.delete.assert_called_with(self.share_snapshot)
        self.assertIsNone(result)

    def test_share_snapshot_delete_force(self):
        arglist = [
            self.share_snapshot.id,
            '--force'
        ]
        verifylist = [
            ('snapshot', [self.share_snapshot.id]),
            ('force', True)
        ]

        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        result = self.cmd.take_action(parsed_args)

        self.snapshots_mock.force_delete.assert_called_with(
            self.share_snapshot)
        self.assertIsNone(result)

    def test_share_snapshot_delete_multiple(self):
        share_snapshots = (
            manila_fakes.FakeShareSnapshot.create_share_snapshots(
                count=2))
        arglist = [
            share_snapshots[0].id,
            share_snapshots[1].id
        ]
        verifylist = [
            ('snapshot', [share_snapshots[0].id, share_snapshots[1].id])
        ]
        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        result = self.cmd.take_action(parsed_args)

        self.assertEqual(self.snapshots_mock.delete.call_count,
                         len(share_snapshots))
        self.assertIsNone(result)

    def test_share_snapshot_delete_exception(self):
        arglist = [
            self.share_snapshot.id
        ]
        verifylist = [
            ('snapshot', [self.share_snapshot.id])
        ]

        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        self.snapshots_mock.delete.side_effect = exceptions.CommandError()
        self.assertRaises(exceptions.CommandError,
                          self.cmd.take_action,
                          parsed_args)


class TestShareSnapshotShow(TestShareSnapshot):

    def setUp(self):
        super(TestShareSnapshotShow, self).setUp()

        self.export_location = (
            manila_fakes.FakeShareExportLocation.create_one_export_location())

        self.share_snapshot = (
            manila_fakes.FakeShareSnapshot.create_one_snapshot(
                attrs={
                    'export_locations': self.export_location
                }
            ))
        self.snapshots_mock.get.return_value = self.share_snapshot

        self.cmd = osc_share_snapshots.ShowShareSnapshot(self.app, None)

        self.data = self.share_snapshot._info.values()
        self.columns = self.share_snapshot._info.keys()

    def test_share_snapshot_show_missing_args(self):
        arglist = []
        verifylist = []

        self.assertRaises(osc_utils.ParserException,
                          self.check_parser, self.cmd, arglist, verifylist)

    def test_share_snapshot_show(self):
        arglist = [
            self.share_snapshot.id
        ]
        verifylist = [
            ('snapshot', self.share_snapshot.id)
        ]
        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        cliutils.transform_export_locations_to_string_view = mock.Mock()
        cliutils.transform_export_locations_to_string_view.return_value = (
            self.export_location)

        columns, data = self.cmd.take_action(parsed_args)
        self.snapshots_mock.get.assert_called_with(self.share_snapshot.id)
        self.assertCountEqual(self.columns, columns)
        self.assertCountEqual(self.data, data)


class TestShareSnapshotSet(TestShareSnapshot):

    def setUp(self):
        super(TestShareSnapshotSet, self).setUp()

        self.share_snapshot = (
            manila_fakes.FakeShareSnapshot.create_one_snapshot())

        self.snapshots_mock.get.return_value = self.share_snapshot

        self.cmd = osc_share_snapshots.SetShareSnapshot(self.app, None)

    def test_set_snapshot_name(self):
        snapshot_name = 'snapshot-name-' + uuid.uuid4().hex
        arglist = [
            self.share_snapshot.id,
            '--name', snapshot_name
        ]
        verifylist = [
            ('snapshot', self.share_snapshot.id),
            ('name', snapshot_name)
        ]
        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        result = self.cmd.take_action(parsed_args)

        self.snapshots_mock.update.assert_called_with(
            self.share_snapshot,
            display_name=parsed_args.name)
        self.assertIsNone(result)

    def test_set_snapshot_description(self):
        description = 'snapshot-description-' + uuid.uuid4().hex
        arglist = [
            self.share_snapshot.id,
            '--description', description
        ]
        verifylist = [
            ('snapshot', self.share_snapshot.id),
            ('description', description)
        ]
        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        result = self.cmd.take_action(parsed_args)

        self.snapshots_mock.update.assert_called_with(
            self.share_snapshot,
            display_description=parsed_args.description)
        self.assertIsNone(result)

    def test_set_snapshot_status(self):
        arglist = [
            self.share_snapshot.id,
            '--status', 'available'
        ]
        verifylist = [
            ('snapshot', self.share_snapshot.id),
            ('status', 'available')
        ]
        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        result = self.cmd.take_action(parsed_args)

        self.snapshots_mock.reset_state.assert_called_with(
            self.share_snapshot,
            parsed_args.status)
        self.assertIsNone(result)

    def test_set_snapshot_update_exception(self):
        snapshot_name = 'snapshot-name-' + uuid.uuid4().hex
        arglist = [
            self.share_snapshot.id,
            '--name', snapshot_name
        ]
        verifylist = [
            ('snapshot', self.share_snapshot.id),
            ('name', snapshot_name)
        ]
        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        self.snapshots_mock.update.side_effect = Exception()

        self.assertRaises(
            exceptions.CommandError,
            self.cmd.take_action,
            parsed_args)

    def test_set_snapshot_status_exception(self):
        arglist = [
            self.share_snapshot.id,
            '--status', 'available'
        ]
        verifylist = [
            ('snapshot', self.share_snapshot.id),
            ('status', 'available')
        ]
        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        self.snapshots_mock.reset_state.side_effect = Exception()

        self.assertRaises(
            exceptions.CommandError,
            self.cmd.take_action,
            parsed_args)


class TestShareSnapshotUnset(TestShareSnapshot):

    def setUp(self):
        super(TestShareSnapshotUnset, self).setUp()

        self.share_snapshot = (
            manila_fakes.FakeShareSnapshot.create_one_snapshot())

        self.snapshots_mock.get.return_value = self.share_snapshot

        self.cmd = osc_share_snapshots.UnsetShareSnapshot(self.app, None)

    def test_unset_snapshot_name(self):
        arglist = [
            self.share_snapshot.id,
            '--name'
        ]
        verifylist = [
            ('snapshot', self.share_snapshot.id),
            ('name', True)
        ]
        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        result = self.cmd.take_action(parsed_args)

        self.snapshots_mock.update.assert_called_with(
            self.share_snapshot,
            display_name=None)
        self.assertIsNone(result)

    def test_unset_snapshot_description(self):
        arglist = [
            self.share_snapshot.id,
            '--description'
        ]
        verifylist = [
            ('snapshot', self.share_snapshot.id),
            ('description', True)
        ]
        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        result = self.cmd.take_action(parsed_args)

        self.snapshots_mock.update.assert_called_with(
            self.share_snapshot,
            display_description=None)
        self.assertIsNone(result)

    def test_unset_snapshot_name_exception(self):
        arglist = [
            self.share_snapshot.id,
            '--name'
        ]
        verifylist = [
            ('snapshot', self.share_snapshot.id),
            ('name', True)
        ]
        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        self.snapshots_mock.update.side_effect = Exception()

        self.assertRaises(
            exceptions.CommandError,
            self.cmd.take_action,
            parsed_args)


class TestShareSnapshotList(TestShareSnapshot):

    def setUp(self):
        super(TestShareSnapshotList, self).setUp()

        self.share_snapshots = (
            manila_fakes.FakeShareSnapshot.create_share_snapshots(
                count=2))
        self.snapshots_list = oscutils.sort_items(
            self.share_snapshots,
            'name:asc',
            str)

        self.snapshots_mock.list.return_value = self.snapshots_list

        self.values = (oscutils.get_dict_properties(
            s._info, COLUMNS) for s in self.snapshots_list)

        self.cmd = osc_share_snapshots.ListShareSnapshot(self.app, None)

    def test_list_snapshots(self):
        arglist = []
        verifylist = []

        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        columns, data = self.cmd.take_action(parsed_args)

        self.snapshots_mock.list.assert_called_with(
            search_opts={
                'offset': None,
                'limit': None,
                'all_tenants': False,
                'name': None,
                'status': None,
                'share_id': None,
                'usage': None,
                'name~': None,
                'description~': None,
                'description': None
            })

        self.assertEqual(COLUMNS, columns)
        self.assertEqual(list(self.values), list(data))

    def test_list_snapshots_all_projects(self):
        all_tenants_list = COLUMNS.copy()
        all_tenants_list.append('Project ID')
        list_values = (oscutils.get_dict_properties(
            s._info, all_tenants_list) for s in self.snapshots_list)

        arglist = [
            '--all-projects'
        ]

        verifylist = [
            ('all_projects', True)
        ]

        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        columns, data = self.cmd.take_action(parsed_args)

        self.snapshots_mock.list.assert_called_with(
            search_opts={
                'offset': None,
                'limit': None,
                'all_tenants': True,
                'name': None,
                'status': None,
                'share_id': None,
                'usage': None,
                'name~': None,
                'description~': None,
                'description': None
            })

        self.assertEqual(all_tenants_list, columns)
        self.assertEqual(list(list_values), list(data))

    def test_list_snapshots_detail(self):
        values = (oscutils.get_dict_properties(
            s._info, COLUMNS_DETAIL) for s in self.snapshots_list)

        arglist = [
            '--detail'
        ]

        verifylist = [
            ('detail', True)
        ]

        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        columns, data = self.cmd.take_action(parsed_args)

        self.snapshots_mock.list.assert_called_with(
            search_opts={
                'offset': None,
                'limit': None,
                'all_tenants': False,
                'name': None,
                'status': None,
                'share_id': None,
                'usage': None,
                'name~': None,
                'description~': None,
                'description': None
            })

        self.assertEqual(COLUMNS_DETAIL, columns)
        self.assertEqual(list(values), list(data))

    def test_list_snapshots_api_version_exception(self):
        self.app.client_manager.share.api_version = api_versions.APIVersion(
            "2.35")

        arglist = [
            '--description', 'Description'
        ]
        verifylist = [
            ('description', 'Description')
        ]

        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        self.assertRaises(
            exceptions.CommandError,
            self.cmd.take_action,
            parsed_args)

    def test_list_snapshots_share_id(self):
        self.share = manila_fakes.FakeShare.create_one_share(
            attrs={'id': self.snapshots_list[0].id})

        self.shares_mock.get.return_value = self.share
        self.snapshots_mock.list.return_value = [self.snapshots_list[0]]

        values = (oscutils.get_dict_properties(
            s._info, COLUMNS) for s in [self.snapshots_list[0]])

        arglist = [
            '--share', self.share.id
        ]
        verifylist = [
            ('share', self.share.id)
        ]

        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        columns, data = self.cmd.take_action(parsed_args)

        self.snapshots_mock.list.assert_called_with(
            search_opts={
                'offset': None,
                'limit': None,
                'all_tenants': False,
                'name': None,
                'status': None,
                'share_id': self.share.id,
                'usage': None,
                'name~': None,
                'description~': None,
                'description': None
            })

        self.assertEqual(COLUMNS, columns)
        self.assertEqual(list(values), list(data))