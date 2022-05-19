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
            api_versions.MAX_VERSION)

        self.export_locations_mock = (
            self.app.client_manager.share.share_snapshot_export_locations)
        self.export_locations_mock.reset_mock()


class TestShareSnapshotCreate(TestShareSnapshot):

    def setUp(self):
        super(TestShareSnapshotCreate, self).setUp()

        self.share = manila_fakes.FakeShare.create_one_share()
        self.shares_mock.create.return_value = self.share

        self.shares_mock.get.return_value = self.share

        self.share_snapshot = (
            manila_fakes.FakeShareSnapshot.create_one_snapshot(
                attrs={'status': 'available'}
            ))
        self.snapshots_mock.get.return_value = self.share_snapshot
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

    def test_share_snapshot_create_wait(self):
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

        self.snapshots_mock.create.assert_called_with(
            share=self.share,
            force=False,
            name=None,
            description=None
        )

        self.snapshots_mock.get.assert_called_with(
            self.share_snapshot.id)
        self.assertCountEqual(self.columns, columns)
        self.assertCountEqual(self.data, data)

    @mock.patch('manilaclient.osc.v2.share_snapshots.LOG')
    def test_share_snapshot_create_wait_error(self, mock_logger):
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

            self.snapshots_mock.create.assert_called_with(
                share=self.share,
                force=False,
                name=None,
                description=None
            )

            mock_logger.error.assert_called_with(
                "ERROR: Share snapshot is in error state.")

            self.snapshots_mock.get.assert_called_with(
                self.share_snapshot.id)
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

    def test_share_snapshot_delete_wait(self):
        arglist = [
            self.share_snapshot.id,
            '--wait'
        ]
        verifylist = [
            ('snapshot', [self.share_snapshot.id]),
            ('wait', True)
        ]

        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        with mock.patch('osc_lib.utils.wait_for_delete', return_value=True):
            result = self.cmd.take_action(parsed_args)

            self.snapshots_mock.delete.assert_called_with(self.share_snapshot)
            self.assertIsNone(result)

    def test_share_snapshot_delete_wait_error(self):
        arglist = [
            self.share_snapshot.id,
            '--wait'
        ]
        verifylist = [
            ('snapshot', [self.share_snapshot.id]),
            ('wait', True)
        ]

        parsed_args = self.check_parser(self.cmd, arglist, verifylist)
        with mock.patch('osc_lib.utils.wait_for_delete', return_value=False):
            self.assertRaises(
                exceptions.CommandError,
                self.cmd.take_action,
                parsed_args
            )


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
        self.export_locations_mock.list.return_value = [self.export_location]

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

        cliutils.convert_dict_list_to_string = mock.Mock()
        cliutils.convert_dict_list_to_string.return_value = (
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


class TestShareSnapshotAdopt(TestShareSnapshot):

    def setUp(self):
        super(TestShareSnapshotAdopt, self).setUp()

        self.share = manila_fakes.FakeShare.create_one_share()
        self.shares_mock.get.return_value = self.share

        self.share_snapshot = (
            manila_fakes.FakeShareSnapshot.create_one_snapshot(
                attrs={
                    'status': 'available'
                }
            ))

        self.snapshots_mock.get.return_value = self.share_snapshot
        self.export_location = (
            manila_fakes.FakeShareExportLocation.create_one_export_location())

        self.snapshots_mock.manage.return_value = self.share_snapshot

        self.cmd = osc_share_snapshots.AdoptShareSnapshot(self.app, None)

        self.data = tuple(self.share_snapshot._info.values())
        self.columns = tuple(self.share_snapshot._info.keys())

    def test_share_snapshot_adopt_missing_args(self):
        arglist = []
        verifylist = []

        self.assertRaises(osc_utils.ParserException,
                          self.check_parser, self.cmd, arglist, verifylist)

    def test_snapshot_adopt(self):
        arglist = [
            self.share.id,
            self.export_location.fake_path
        ]
        verifylist = [
            ('share', self.share.id),
            ('provider_location', self.export_location.fake_path)
        ]

        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        columns, data = self.cmd.take_action(parsed_args)

        self.snapshots_mock.manage.assert_called_with(
            share=self.share,
            provider_location=self.export_location.fake_path,
            driver_options={},
            name=None,
            description=None
        )

        self.assertCountEqual(self.columns, columns)
        self.assertCountEqual(self.data, data)

    def test_snapshot_adopt_name(self):
        name = 'name-' + uuid.uuid4().hex
        arglist = [
            self.share.id,
            self.export_location.fake_path,
            '--name', name,
        ]
        verifylist = [
            ('share', self.share.id),
            ('provider_location', self.export_location.fake_path),
            ('name', name)
        ]

        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        columns, data = self.cmd.take_action(parsed_args)

        self.snapshots_mock.manage.assert_called_with(
            share=self.share,
            provider_location=self.export_location.fake_path,
            driver_options={},
            name=name,
            description=None
        )

        self.assertCountEqual(self.columns, columns)
        self.assertCountEqual(self.data, data)

    def test_snapshot_adopt_driver_option(self):
        arglist = [
            self.share.id,
            self.export_location.fake_path,
            '--driver-option', 'key1=value1',
            '--driver-option', 'key2=value2'
        ]
        verifylist = [
            ('share', self.share.id),
            ('provider_location', self.export_location.fake_path),
            ('driver_option', {'key1': 'value1', 'key2': 'value2'})
        ]

        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        columns, data = self.cmd.take_action(parsed_args)

        self.snapshots_mock.manage.assert_called_with(
            share=self.share,
            provider_location=self.export_location.fake_path,
            driver_options={
                'key1': 'value1',
                'key2': 'value2'
            },
            name=None,
            description=None
        )

        self.assertCountEqual(self.columns, columns)
        self.assertCountEqual(self.data, data)

    def test_snapshot_adopt_wait(self):
        arglist = [
            self.share.id,
            self.export_location.fake_path,
            '--wait'
        ]
        verifylist = [
            ('share', self.share.id),
            ('provider_location', self.export_location.fake_path),
            ('wait', True)
        ]

        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        columns, data = self.cmd.take_action(parsed_args)
        self.snapshots_mock.get.assert_called_with(self.share_snapshot.id)
        self.snapshots_mock.manage.assert_called_with(
            share=self.share,
            provider_location=self.export_location.fake_path,
            driver_options={},
            name=None,
            description=None
        )

        self.assertCountEqual(self.columns, columns)
        self.assertCountEqual(self.data, data)

    def test_snapshot_adopt_wait_error(self):
        arglist = [
            self.share.id,
            self.export_location.fake_path,
            '--wait'
        ]
        verifylist = [
            ('share', self.share.id),
            ('provider_location', self.export_location.fake_path),
            ('wait', True)
        ]

        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        with mock.patch('osc_lib.utils.wait_for_status', return_value=False):
            columns, data = self.cmd.take_action(parsed_args)
            self.snapshots_mock.get.assert_called_with(self.share_snapshot.id)
            self.snapshots_mock.manage.assert_called_with(
                share=self.share,
                provider_location=self.export_location.fake_path,
                driver_options={},
                name=None,
                description=None
            )
            self.assertCountEqual(self.columns, columns)
            self.assertCountEqual(self.data, data)


class TestShareSnapshotAbandon(TestShareSnapshot):

    def setUp(self):
        super(TestShareSnapshotAbandon, self).setUp()

        self.share_snapshot = (
            manila_fakes.FakeShareSnapshot.create_one_snapshot(
                attrs={'status': 'available'}
            ))

        self.snapshots_mock.get.return_value = self.share_snapshot

        self.cmd = osc_share_snapshots.AbandonShareSnapshot(self.app, None)

    def test_share_snapshot_abandon_missing_args(self):
        arglist = []
        verifylist = []

        self.assertRaises(osc_utils.ParserException,
                          self.check_parser, self.cmd, arglist, verifylist)

    def test_share_snapshot_abandon(self):
        arglist = [
            self.share_snapshot.id
        ]
        verifylist = [
            ('snapshot', [self.share_snapshot.id])
        ]

        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        result = self.cmd.take_action(parsed_args)

        self.snapshots_mock.unmanage.assert_called_with(self.share_snapshot)
        self.assertIsNone(result)

    def test_share_snapshot_abandon_multiple(self):
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

        self.assertEqual(self.snapshots_mock.unmanage.call_count,
                         len(share_snapshots))
        self.assertIsNone(result)

    def test_share_snapshot_abandon_wait(self):
        arglist = [
            self.share_snapshot.id,
            '--wait'
        ]
        verifylist = [
            ('snapshot', [self.share_snapshot.id]),
            ('wait', True)
        ]

        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        with mock.patch('osc_lib.utils.wait_for_delete', return_value=True):
            result = self.cmd.take_action(parsed_args)
            self.snapshots_mock.unmanage.assert_called_with(
                self.share_snapshot)
            self.assertIsNone(result)

    def test_share_snapshot_abandon_wait_error(self):
        arglist = [
            self.share_snapshot.id,
            '--wait'
        ]
        verifylist = [
            ('snapshot', [self.share_snapshot.id]),
            ('wait', True)
        ]

        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        with mock.patch('osc_lib.utils.wait_for_delete', return_value=False):
            self.assertRaises(
                exceptions.CommandError,
                self.cmd.take_action,
                parsed_args)


class TestShareSnapshotAccessAllow(TestShareSnapshot):

    def setUp(self):
        super(TestShareSnapshotAccessAllow, self).setUp()

        self.share_snapshot = (
            manila_fakes.FakeShareSnapshot.create_one_snapshot())

        self.snapshots_mock.get.return_value = self.share_snapshot

        self.access_rule = (
            manila_fakes.FakeSnapshotAccessRule.create_one_access_rule())
        self.snapshots_mock.allow.return_value = self.access_rule._info

        self.cmd = osc_share_snapshots.ShareSnapshotAccessAllow(
            self.app, None)

    def test_share_snapshot_access_allow(self):
        arglist = [
            self.share_snapshot.id,
            'user',
            'demo'
        ]
        verifylist = [
            ('snapshot', self.share_snapshot.id),
            ('access_type', 'user'),
            ('access_to', 'demo')
        ]

        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        columns, data = self.cmd.take_action(parsed_args)

        self.snapshots_mock.allow.assert_called_with(
            snapshot=self.share_snapshot,
            access_type='user',
            access_to='demo'
        )
        self.assertEqual(tuple(self.access_rule._info.keys()), columns)
        self.assertCountEqual(self.access_rule._info.values(), data)

    def test_share_snapshot_access_allow_exception(self):
        arglist = [
            self.share_snapshot.id,
            'user',
            'demo'
        ]
        verifylist = [
            ('snapshot', self.share_snapshot.id),
            ('access_type', 'user'),
            ('access_to', 'demo')
        ]

        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        self.snapshots_mock.allow.side_effect = exceptions.CommandError()
        self.assertRaises(exceptions.CommandError,
                          self.cmd.take_action,
                          parsed_args)


class TestShareSnapshotAccessDeny(TestShareSnapshot):

    def setUp(self):
        super(TestShareSnapshotAccessDeny, self).setUp()

        self.share_snapshot = (
            manila_fakes.FakeShareSnapshot.create_one_snapshot())

        self.snapshots_mock.get.return_value = self.share_snapshot

        self.access_rule = (
            manila_fakes.FakeSnapshotAccessRule.create_one_access_rule())

        self.cmd = osc_share_snapshots.ShareSnapshotAccessDeny(
            self.app, None)

    def test_share_snapshot_access_deny(self):
        arglist = [
            self.share_snapshot.id,
            self.access_rule.id,
        ]
        verifylist = [
            ('snapshot', self.share_snapshot.id),
            ('id', [self.access_rule.id]),
        ]

        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        result = self.cmd.take_action(parsed_args)

        self.snapshots_mock.deny.assert_called_with(
            snapshot=self.share_snapshot,
            id=self.access_rule.id
        )
        self.assertIsNone(result)

    def test_share_snapshot_access_deny_multiple(self):
        access_rules = (
            manila_fakes.FakeSnapshotAccessRule.create_access_rules(
                count=2))

        arglist = [
            self.share_snapshot.id,
            access_rules[0].id,
            access_rules[1].id,
        ]
        verifylist = [
            ('snapshot', self.share_snapshot.id),
            ('id', [access_rules[0].id, access_rules[1].id]),
        ]

        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        result = self.cmd.take_action(parsed_args)

        self.assertEqual(self.snapshots_mock.deny.call_count,
                         len(access_rules))
        self.assertIsNone(result)

    def test_share_snapshot_access_deny_exception(self):
        arglist = [
            self.share_snapshot.id,
            self.access_rule.id,
        ]
        verifylist = [
            ('snapshot', self.share_snapshot.id),
            ('id', [self.access_rule.id]),
        ]

        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        self.snapshots_mock.deny.side_effect = exceptions.CommandError()
        self.assertRaises(exceptions.CommandError,
                          self.cmd.take_action,
                          parsed_args)


class TestShareSnapshotAccessList(TestShareSnapshot):

    access_rules_columns = [
        'id',
        'access_type',
        'access_to',
        'state',
    ]

    def setUp(self):
        super(TestShareSnapshotAccessList, self).setUp()

        self.share_snapshot = (
            manila_fakes.FakeShareSnapshot.create_one_snapshot())

        self.snapshots_mock.get.return_value = self.share_snapshot

        self.access_rules = (
            manila_fakes.FakeSnapshotAccessRule.create_access_rules(
                count=2))

        self.snapshots_mock.access_list.return_value = self.access_rules
        self.cmd = osc_share_snapshots.ShareSnapshotAccessList(
            self.app, None)

        self.values = (oscutils.get_dict_properties(
            a._info, self.access_rules_columns) for a in self.access_rules)

    def test_share_snapshot_access_list(self):
        arglist = [
            self.share_snapshot.id
        ]
        verifylist = [
            ('snapshot', self.share_snapshot.id)
        ]

        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        columns, data = self.cmd.take_action(parsed_args)

        self.snapshots_mock.access_list.assert_called_with(
            self.share_snapshot)

        self.assertEqual(self.access_rules_columns, columns)
        self.assertCountEqual(self.values, data)


class TestShareSnapshotExportLocationList(TestShareSnapshot):

    columns = ["id", "path"]

    def setUp(self):
        super(TestShareSnapshotExportLocationList, self).setUp()

        self.share_snapshot = (
            manila_fakes.FakeShareSnapshot.create_one_snapshot())

        self.snapshots_mock.get.return_value = self.share_snapshot

        self.export_locations = (
            manila_fakes.FakeSnapshotExportLocation.create_export_locations()
        )

        self.export_locations_mock.list.return_value = self.export_locations
        self.values = (oscutils.get_dict_properties(
            e._info, self.columns) for e in self.export_locations)

        self.cmd = osc_share_snapshots.ShareSnapshotListExportLocation(
            self.app, None)

    def test_snapshot_export_locations_list(self):
        arglist = [
            self.share_snapshot.id
        ]
        verifylist = [
            ('snapshot', self.share_snapshot.id)
        ]

        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        columns, data = self.cmd.take_action(parsed_args)

        self.export_locations_mock.list.assert_called_with(
            snapshot=self.share_snapshot)

        self.assertEqual(self.columns, columns)
        self.assertCountEqual(self.values, data)


class TestShareSnapshotExportLocationShow(TestShareSnapshot):

    def setUp(self):
        super(TestShareSnapshotExportLocationShow, self).setUp()

        self.share_snapshot = (
            manila_fakes.FakeShareSnapshot.create_one_snapshot())

        self.snapshots_mock.get.return_value = self.share_snapshot

        self.export_location = (
            manila_fakes.FakeSnapshotExportLocation.create_one_export_location()  # noqa E501
        )

        self.export_locations_mock.get.return_value = self.export_location

        self.cmd = osc_share_snapshots.ShareSnapshotShowExportLocation(
            self.app, None)

    def test_snapshot_export_locations_list(self):
        arglist = [
            self.share_snapshot.id,
            self.export_location.id
        ]
        verifylist = [
            ('snapshot', self.share_snapshot.id),
            ('export_location', self.export_location.id)
        ]

        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        columns, data = self.cmd.take_action(parsed_args)

        self.export_locations_mock.get.assert_called_with(
            export_location=self.export_location.id,
            snapshot=self.share_snapshot)

        self.assertEqual(tuple(self.export_location._info.keys()), columns)
        self.assertCountEqual(self.export_location._info.values(), data)
