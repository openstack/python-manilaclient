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

import argparse
from unittest import mock
import uuid

from openstackclient.tests.unit.identity.v3 import fakes as identity_fakes
from osc_lib import exceptions as osc_exceptions

from manilaclient.common.apiclient import exceptions
from manilaclient.common import cliutils
from manilaclient.osc.v2 import share as osc_shares
from manilaclient.tests.unit.osc import osc_utils
from manilaclient.tests.unit.osc.v2 import fakes as manila_fakes


class TestShare(manila_fakes.TestShare):

    def setUp(self):
        super(TestShare, self).setUp()

        self.shares_mock = self.app.client_manager.share.shares
        self.shares_mock.reset_mock()

        self.projects_mock = self.app.client_manager.identity.projects
        self.projects_mock.reset_mock()

        self.users_mock = self.app.client_manager.identity.users
        self.users_mock.reset_mock()

    def setup_shares_mock(self, count):
        shares = manila_fakes.FakeShare.create_shares(count=count)

        self.shares_mock.get = manila_fakes.FakeShare.get_shares(
            shares,
            0)
        return shares


class TestShareCreate(TestShare):

    def setUp(self):
        super(TestShareCreate, self).setUp()

        self.new_share = manila_fakes.FakeShare.create_one_share()
        self.shares_mock.create.return_value = self.new_share

        self.share_types_mock = self.app.client_manager.share.share_types
        self.share_types_mock.reset_mock()
        self.share_type = manila_fakes.FakeShareType.create_one_sharetype()
        self.share_types_mock.get.return_value = self.share_type

        # Get the command object to test
        self.cmd = osc_shares.CreateShare(self.app, None)

        self.datalist = tuple(self.new_share._info.values())
        self.columns = tuple(self.new_share._info.keys())

    def test_share_create_required_args(self):
        """Verifies required arguments."""

        arglist = [
            self.new_share.share_proto,
            str(self.new_share.size),
            '--share-type', self.share_type.id,
        ]
        verifylist = [
            ('share_proto', self.new_share.share_proto),
            ('size', self.new_share.size),
            ('share_type', self.share_type.id)
        ]

        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        columns, data = self.cmd.take_action(parsed_args)

        self.shares_mock.create.assert_called_with(
            availability_zone=None,
            description=None,
            is_public=False,
            metadata={},
            name=None,
            share_group_id=None,
            share_network=None,
            share_proto=self.new_share.share_proto,
            share_type=self.share_type.id,
            size=self.new_share.size,
            snapshot_id=None
        )

        self.assertCountEqual(self.columns, columns)
        self.assertCountEqual(self.datalist, data)

    def test_share_create_missing_required_arg(self):
        """Verifies missing required arguments."""

        arglist = [
            self.new_share.share_proto,
        ]
        verifylist = [
            ('share_proto', self.new_share.share_proto)
        ]
        self.assertRaises(osc_utils.ParserException,
                          self.check_parser, self.cmd, arglist, verifylist)

    def test_share_create_metadata(self):
        arglist = [
            self.new_share.share_proto,
            str(self.new_share.size),
            '--share-type', self.share_type.id,
            '--property', 'Manila=zorilla',
            '--property', 'Zorilla=manila'
        ]
        verifylist = [
            ('share_proto', self.new_share.share_proto),
            ('size', self.new_share.size),
            ('share_type', self.share_type.id),
            ('property', {'Manila': 'zorilla', 'Zorilla': 'manila'}),
        ]
        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        columns, data = self.cmd.take_action(parsed_args)

        self.shares_mock.create.assert_called_with(
            availability_zone=None,
            description=None,
            is_public=False,
            metadata={'Manila': 'zorilla', 'Zorilla': 'manila'},
            name=None,
            share_group_id=None,
            share_network=None,
            share_proto=self.new_share.share_proto,
            share_type=self.share_type.id,
            size=self.new_share.size,
            snapshot_id=None
        )

        self.assertCountEqual(self.columns, columns)
        self.assertCountEqual(self.datalist, data)

    # TODO(vkmc) Add test with snapshot when
    # we implement snapshot support in OSC
    # def test_share_create_with_snapshot(self):

    def test_create_share_with_no_existing_share_type(self):
        arglist = [
            self.new_share.share_proto,
            str(self.new_share.size),
        ]
        verifylist = [
            ('share_proto', self.new_share.share_proto),
            ('size', self.new_share.size),
        ]

        parsed_args = self.check_parser(self.cmd, arglist, verifylist)
        self.share_types_mock.get.side_effect = osc_exceptions.CommandError()

        self.assertRaises(
            osc_exceptions.CommandError,
            self.cmd.take_action,
            parsed_args)


class TestShareDelete(TestShare):

    def setUp(self):
        super(TestShareDelete, self).setUp()

        self.shares_mock.delete = mock.Mock()
        self.shares_mock.delete.return_value = None

        # Get the command object to test
        self.cmd = osc_shares.DeleteShare(self.app, None)

    def test_share_delete_one(self):
        shares = self.setup_shares_mock(count=1)

        arglist = [
            shares[0].name
        ]
        verifylist = [
            ("force", False),
            ("share_group", None),
            ('shares', [shares[0].name])
        ]

        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        result = self.cmd.take_action(parsed_args)
        self.shares_mock.delete.assert_called_with(shares[0], None)
        self.assertIsNone(result)

    def test_share_delete_many(self):
        shares = self.setup_shares_mock(count=3)

        arglist = [v.id for v in shares]
        verifylist = [
            ("force", False),
            ("share_group", None),
            ('shares', arglist),
        ]
        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        result = self.cmd.take_action(parsed_args)

        calls = [mock.call(s, None) for s in shares]
        self.shares_mock.delete.assert_has_calls(calls)
        self.assertIsNone(result)

    def test_share_delete_with_force(self):
        shares = self.setup_shares_mock(count=1)

        arglist = [
            '--force',
            shares[0].name,
        ]
        verifylist = [
            ('force', True),
            ("share_group", None),
            ('shares', [shares[0].name]),
        ]
        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        result = self.cmd.take_action(parsed_args)

        self.shares_mock.force_delete.assert_called_once_with(shares[0])
        self.assertIsNone(result)

    def test_share_delete_wrong_name(self):
        shares = self.setup_shares_mock(count=1)

        arglist = [
            shares[0].name + '-wrong-name'
        ]
        verifylist = [
            ("force", False),
            ("share_group", None),
            ('shares', [shares[0].name + '-wrong-name'])
        ]

        parsed_args = self.check_parser(self.cmd, arglist, verifylist)
        result = self.cmd.take_action(parsed_args)

        self.assertIsNone(result)

        self.shares_mock.delete.side_effect = exceptions.CommandError()
        self.assertRaises(
            osc_exceptions.CommandError, self.cmd.take_action, parsed_args)

    def test_share_delete_no_name(self):
        # self.setup_shares_mock(count=1)

        arglist = []
        verifylist = [
            ("force", False),
            ("share_group", None),
            ('shares', '')
        ]

        self.assertRaises(osc_utils.ParserException,
                          self.check_parser, self.cmd, arglist, verifylist)


class TestShareList(TestShare):

    project = identity_fakes.FakeProject.create_one_project()
    user = identity_fakes.FakeUser.create_one_user()

    columns = [
        'ID',
        'Name',
        'Size',
        'Share Proto',
        'Status',
        'Is Public',
        'Share Type Name',
        'Host',
        'Availability Zone'
    ]

    def setUp(self):
        super(TestShareList, self).setUp()

        self.new_share = manila_fakes.FakeShare.create_one_share()
        self.shares_mock.list.return_value = [self.new_share]

        self.users_mock.get.return_value = self.user

        self.projects_mock.get.return_value = self.project

        # Get the command object to test
        self.cmd = osc_shares.ListShare(self.app, None)

    def _get_data(self):
        data = ((
            self.new_share.id,
            self.new_share.name,
            self.new_share.size,
            self.new_share.share_proto,
            self.new_share.status,
            self.new_share.is_public,
            self.new_share.share_type_name,
            self.new_share.host,
            self.new_share.availability_zone,
        ),)
        return data

    def _get_search_opts(self):
        search_opts = {
            'all_tenants': False,
            'is_public': False,
            'metadata': {},
            'extra_specs': {},
            'limit': None,
            'name': None,
            'status': None,
            'host': None,
            'share_server_id': None,
            'share_network_id': None,
            'share_type_id': None,
            'snapshot_id': None,
            'share_group_id': None,
            'project_id': None,
            'user_id': None,
            'offset': None,
        }
        return search_opts

    def test_share_list_no_options(self):
        arglist = []
        verifylist = [
            ('long', False),
            ('all_projects', False),
            ('name', None),
            ('status', None),
        ]
        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        cmd_columns, cmd_data = self.cmd.take_action(parsed_args)

        search_opts = {
            'all_tenants': False,
            'is_public': False,
            'metadata': {},
            'extra_specs': {},
            'limit': None,
            'name': None,
            'status': None,
            'host': None,
            'share_server_id': None,
            'share_network_id': None,
            'share_type_id': None,
            'snapshot_id': None,
            'share_group_id': None,
            'project_id': None,
            'user_id': None,
            'offset': None,
        }

        self.shares_mock.list.assert_called_once_with(
            search_opts=search_opts,
        )

        self.assertEqual(self.columns, cmd_columns)

        data = self._get_data()

        self.assertEqual(data, tuple(cmd_data))

    def test_share_list_project(self):
        arglist = [
            '--project', self.project.name,
        ]
        verifylist = [
            ('project', self.project.name),
            ('long', False),
            ('all_projects', False),
            ('status', None),
        ]
        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        cmd_columns, cmd_data = self.cmd.take_action(parsed_args)

        search_opts = {
            'all_tenants': False,
            'is_public': False,
            'metadata': {},
            'extra_specs': {},
            'limit': None,
            'name': None,
            'status': None,
            'host': None,
            'share_server_id': None,
            'share_network_id': None,
            'share_type_id': None,
            'snapshot_id': None,
            'share_group_id': None,
            'project_id': None,
            'user_id': None,
            'offset': None,
        }

        search_opts['project_id'] = self.project.id
        search_opts['all_tenants'] = True

        self.shares_mock.list.assert_called_once_with(
            search_opts=search_opts,
        )

        self.assertEqual(self.columns, cmd_columns)

        data = self._get_data()

        self.assertEqual(data, tuple(cmd_data))

    def test_share_list_project_domain(self):
        arglist = [
            '--project', self.project.name,
            '--project-domain', self.project.domain_id,
        ]
        verifylist = [
            ('project', self.project.name),
            ('project_domain', self.project.domain_id),
            ('long', False),
            ('all_projects', False),
            ('status', None),
        ]
        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        cmd_columns, cmd_data = self.cmd.take_action(parsed_args)

        search_opts = {
            'all_tenants': False,
            'is_public': False,
            'metadata': {},
            'extra_specs': {},
            'limit': None,
            'name': None,
            'status': None,
            'host': None,
            'share_server_id': None,
            'share_network_id': None,
            'share_type_id': None,
            'snapshot_id': None,
            'share_group_id': None,
            'project_id': None,
            'user_id': None,
            'offset': None,
        }

        search_opts['project_id'] = self.project.id
        search_opts['all_tenants'] = True

        self.shares_mock.list.assert_called_once_with(
            search_opts=search_opts,
        )

        self.assertEqual(self.columns, cmd_columns)

        data = self._get_data()

        self.assertEqual(data, tuple(cmd_data))

    def test_share_list_user(self):
        arglist = [
            '--user', self.user.name,
        ]
        verifylist = [
            ('user', self.user.name),
            ('long', False),
            ('all_projects', False),
            ('status', None),
        ]
        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        cmd_columns, cmd_data = self.cmd.take_action(parsed_args)

        search_opts = {
            'all_tenants': False,
            'is_public': False,
            'metadata': {},
            'extra_specs': {},
            'limit': None,
            'name': None,
            'status': None,
            'host': None,
            'share_server_id': None,
            'share_network_id': None,
            'share_type_id': None,
            'snapshot_id': None,
            'share_group_id': None,
            'project_id': None,
            'user_id': None,
            'offset': None,
        }

        search_opts['user_id'] = self.user.id

        self.shares_mock.list.assert_called_once_with(
            search_opts=search_opts,
        )
        self.assertEqual(self.columns, cmd_columns)

        data = self._get_data()

        self.assertEqual(data, tuple(cmd_data))

    def test_share_list_user_domain(self):
        arglist = [
            '--user', self.user.name,
            '--user-domain', self.user.domain_id,
        ]
        verifylist = [
            ('user', self.user.name),
            ('user_domain', self.user.domain_id),
            ('long', False),
            ('all_projects', False),
            ('status', None),
        ]
        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        cmd_columns, cmd_data = self.cmd.take_action(parsed_args)

        search_opts = {
            'all_tenants': False,
            'is_public': False,
            'metadata': {},
            'extra_specs': {},
            'limit': None,
            'name': None,
            'status': None,
            'host': None,
            'share_server_id': None,
            'share_network_id': None,
            'share_type_id': None,
            'snapshot_id': None,
            'share_group_id': None,
            'project_id': None,
            'user_id': None,
            'offset': None,
        }

        search_opts['user_id'] = self.user.id

        self.shares_mock.list.assert_called_once_with(
            search_opts=search_opts,
        )

        self.assertEqual(self.columns, cmd_columns)

        data = self._get_data()

        self.assertEqual(data, tuple(cmd_data))

    def test_share_list_name(self):
        arglist = [
            '--name', self.new_share.name,
        ]
        verifylist = [
            ('long', False),
            ('all_projects', False),
            ('name', self.new_share.name),
            ('status', None),
        ]
        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        cmd_columns, cmd_data = self.cmd.take_action(parsed_args)

        search_opts = {
            'all_tenants': False,
            'is_public': False,
            'metadata': {},
            'extra_specs': {},
            'limit': None,
            'name': None,
            'status': None,
            'host': None,
            'share_server_id': None,
            'share_network_id': None,
            'share_type_id': None,
            'snapshot_id': None,
            'share_group_id': None,
            'project_id': None,
            'user_id': None,
            'offset': None,
        }

        search_opts['name'] = self.new_share.name

        self.shares_mock.list.assert_called_once_with(
            search_opts=search_opts,
        )

        self.assertEqual(self.columns, cmd_columns)

        data = self._get_data()

        self.assertEqual(data, tuple(cmd_data))

    def test_share_list_status(self):
        arglist = [
            '--status', self.new_share.status,
        ]
        verifylist = [
            ('long', False),
            ('all_projects', False),
            ('name', None),
            ('status', self.new_share.status),
        ]
        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        cmd_columns, cmd_data = self.cmd.take_action(parsed_args)

        search_opts = {
            'all_tenants': False,
            'is_public': False,
            'metadata': {},
            'extra_specs': {},
            'limit': None,
            'name': None,
            'status': None,
            'host': None,
            'share_server_id': None,
            'share_network_id': None,
            'share_type_id': None,
            'snapshot_id': None,
            'share_group_id': None,
            'project_id': None,
            'user_id': None,
            'offset': None,
        }

        search_opts['status'] = self.new_share.status

        self.shares_mock.list.assert_called_once_with(
            search_opts=search_opts,
        )

        self.assertEqual(self.columns, cmd_columns)

        data = self._get_data()

        self.assertEqual(data, tuple(cmd_data))

    def test_share_list_all_tenants(self):
        arglist = [
            '--all-projects',
        ]
        verifylist = [
            ('long', False),
            ('all_projects', True),
            ('name', None),
            ('status', None),
        ]
        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        cmd_columns, cmd_data = self.cmd.take_action(parsed_args)

        search_opts = {
            'all_tenants': False,
            'is_public': False,
            'metadata': {},
            'extra_specs': {},
            'limit': None,
            'name': None,
            'status': None,
            'host': None,
            'share_server_id': None,
            'share_network_id': None,
            'share_type_id': None,
            'snapshot_id': None,
            'share_group_id': None,
            'project_id': None,
            'user_id': None,
            'offset': None,
        }

        search_opts['all_tenants'] = True

        self.shares_mock.list.assert_called_once_with(
            search_opts=search_opts,
        )

        self.assertEqual(self.columns, cmd_columns)

        data = self._get_data()

        self.assertEqual(data, tuple(cmd_data))

    def test_share_list_long(self):
        arglist = [
            '--long',
        ]
        verifylist = [
            ('long', True),
            ('all_projects', False),
        ]

        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        cmd_columns, cmd_data = self.cmd.take_action(parsed_args)

        search_opts = {
            'all_tenants': False,
            'is_public': False,
            'metadata': {},
            'extra_specs': {},
            'limit': None,
            'name': None,
            'status': None,
            'host': None,
            'share_server_id': None,
            'share_network_id': None,
            'share_type_id': None,
            'snapshot_id': None,
            'share_group_id': None,
            'project_id': None,
            'user_id': None,
            'offset': None,
        }

        self.shares_mock.list.assert_called_once_with(
            search_opts=search_opts,
        )

        collist = [
            'ID',
            'Name',
            'Size',
            'Share Protocol',
            'Status',
            'Is Public',
            'Share Type Name',
            'Availability Zone',
            'Description',
            'Share Network ID',
            'Share Server ID',
            'Share Type',
            'Share Group ID',
            'Host',
            'User ID',
            'Project ID',
            'Access Rules Status',
            'Source Snapshot ID',
            'Supports Creating Snapshots',
            'Supports Cloning Snapshots',
            'Supports Mounting snapshots',
            'Supports Reverting to Snapshot',
            'Migration Task Status',
            'Source Share Group Snapshot Member ID',
            'Replication Type',
            'Has Replicas',
            'Created At',
            'Properties',
        ]
        self.assertEqual(collist, cmd_columns)

        data = ((
            self.new_share.id,
            self.new_share.name,
            self.new_share.size,
            self.new_share.share_proto,
            self.new_share.status,
            self.new_share.is_public,
            self.new_share.share_type_name,
            self.new_share.availability_zone,
            self.new_share.description,
            self.new_share.share_network_id,
            self.new_share.share_server_id,
            self.new_share.share_type,
            self.new_share.share_group_id,
            self.new_share.host,
            self.new_share.user_id,
            self.new_share.project_id,
            self.new_share.access_rules_status,
            self.new_share.snapshot_id,
            self.new_share.snapshot_support,
            self.new_share.create_share_from_snapshot_support,
            self.new_share.mount_snapshot_support,
            self.new_share.revert_to_snapshot_support,
            self.new_share.task_state,
            self.new_share.source_share_group_snapshot_member_id,
            self.new_share.replication_type,
            self.new_share.has_replicas,
            self.new_share.created_at,
            self.new_share.metadata
        ),)

        self.assertEqual(data, tuple(cmd_data))

    def test_share_list_with_marker_and_limit(self):
        arglist = [
            "--marker", self.new_share.id,
            "--limit", "2",
        ]
        verifylist = [
            ('long', False),
            ('all_projects', False),
            ('name', None),
            ('status', None),
            ('marker', self.new_share.id),
            ('limit', 2),
        ]
        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        cmd_columns, cmd_data = self.cmd.take_action(parsed_args)

        self.assertEqual(self.columns, cmd_columns)

        search_opts = {
            'all_tenants': False,
            'is_public': False,
            'metadata': {},
            'extra_specs': {},
            'limit': 2,
            'name': None,
            'status': None,
            'host': None,
            'share_server_id': None,
            'share_network_id': None,
            'share_type_id': None,
            'snapshot_id': None,
            'share_group_id': None,
            'project_id': None,
            'user_id': None,
            'offset': self.new_share.id
        }

        data = self._get_data()

        self.shares_mock.list.assert_called_once_with(
            search_opts=search_opts
        )
        self.assertEqual(data, tuple(cmd_data))

    def test_share_list_negative_limit(self):
        arglist = [
            "--limit", "-2",
        ]
        verifylist = [
            ("limit", -2),
        ]
        self.assertRaises(argparse.ArgumentTypeError, self.check_parser,
                          self.cmd, arglist, verifylist)


class TestShareShow(TestShare):

    def setUp(self):
        super(TestShareShow, self).setUp()

        self._share = manila_fakes.FakeShare.create_one_share()
        self.shares_mock.get.return_value = self._share

        self._export_location = (
            manila_fakes.FakeShareExportLocation.create_one_export_location())

        # Get the command object to test
        self.cmd = osc_shares.ShowShare(self.app, None)

    def test_share_show(self):
        arglist = [
            self._share.id
        ]
        verifylist = [
            ("share", self._share.id)
        ]
        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        cliutils.transform_export_locations_to_string_view = mock.Mock()
        cliutils.transform_export_locations_to_string_view.return_value = dict(
            self._export_location)

        columns, data = self.cmd.take_action(parsed_args)
        self.shares_mock.get.assert_called_with(self._share.id)

        self.assertEqual(
            manila_fakes.FakeShare.get_share_columns(self._share),
            columns)

        self.assertEqual(
            manila_fakes.FakeShare.get_share_data(self._share),
            data)


class TestShareSet(TestShare):

    def setUp(self):
        super(TestShareSet, self).setUp()

        self._share = manila_fakes.FakeShare.create_one_share()
        self.shares_mock.get.return_value = self._share

        # Get the command object to test
        self.cmd = osc_shares.SetShare(self.app, None)

    def test_share_set_property(self):
        arglist = [
            '--property', 'Zorilla=manila',
            self._share.id,
        ]
        verifylist = [
            ('property', {'Zorilla': 'manila'}),
            ('share', self._share.id)
        ]

        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        self.cmd.take_action(parsed_args)
        self.shares_mock.set_metadata.assert_called_with(
            self._share.id,
            {'Zorilla': 'manila'})

    def test_share_set_name(self):
        new_name = uuid.uuid4().hex
        arglist = [
            '--name', new_name,
            self._share.id,
        ]
        verifylist = [
            ('name', new_name),
            ('share', self._share.id)
        ]

        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        self.cmd.take_action(parsed_args)
        self.shares_mock.update.assert_called_with(
            self._share.id,
            display_name=parsed_args.name)

    def test_share_set_description(self):
        new_description = uuid.uuid4().hex
        arglist = [
            '--description', new_description,
            self._share.id,
        ]
        verifylist = [
            ('description', new_description),
            ('share', self._share.id)
        ]

        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        self.cmd.take_action(parsed_args)
        self.shares_mock.update.assert_called_with(
            self._share.id,
            display_description=parsed_args.description)

    def test_share_set_visibility(self):
        arglist = [
            '--public', 'true',
            self._share.id,
        ]
        verifylist = [
            ('public', 'true'),
            ('share', self._share.id)
        ]

        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        self.cmd.take_action(parsed_args)
        self.shares_mock.update.assert_called_with(
            self._share.id,
            is_public='true')

    def test_share_set_visibility_exception(self):
        arglist = [
            '--public', 'not_a_boolean_value',
            self._share.id,
        ]
        verifylist = [
            ('public', 'not_a_boolean_value'),
            ('share', self._share.id)
        ]

        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        self.cmd.take_action(parsed_args)
        self.shares_mock.update.assert_called_with(
            self._share.id,
            is_public='not_a_boolean_value')

        # '--public' takes only boolean value, would raise a BadRequest
        self.shares_mock.update.side_effect = exceptions.BadRequest()
        self.assertRaises(
            osc_exceptions.CommandError, self.cmd.take_action, parsed_args)

    def test_share_set_property_exception(self):
        arglist = [
            '--property', 'key=',
            self._share.id,
        ]
        verifylist = [
            ('property', {'key': ''}),
            ('share', self._share.id)
        ]

        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        self.cmd.take_action(parsed_args)
        self.shares_mock.set_metadata.assert_called_with(
            self._share.id,
            {'key': ''})

        # '--property' takes key=value arguments
        # missing a value would raise a BadRequest
        self.shares_mock.set_metadata.side_effect = exceptions.BadRequest()
        self.assertRaises(
            osc_exceptions.CommandError, self.cmd.take_action, parsed_args)


class TestShareUnset(TestShare):

    def setUp(self):
        super(TestShareUnset, self).setUp()

        self._share = manila_fakes.FakeShare.create_one_share()
        self.shares_mock.get.return_value = self._share

        # Get the command objects to test
        self.cmd = osc_shares.UnsetShare(self.app, None)

    def test_share_unset_property(self):
        arglist = [
            '--property', 'Manila',
            self._share.id,
        ]
        verifylist = [
            ('property', ['Manila']),
            ('share', self._share.id)
        ]

        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        self.cmd.take_action(parsed_args)
        self.shares_mock.delete_metadata.assert_called_with(
            self._share.id,
            parsed_args.property)

    def test_share_unset_name(self):
        arglist = [
            '--name',
            self._share.id,
        ]
        verifylist = [
            ('name', True),
            ('share', self._share.id)
        ]

        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        self.cmd.take_action(parsed_args)
        self.shares_mock.update.assert_called_with(
            self._share.id,
            display_name=None)

    def test_share_unset_description(self):
        arglist = [
            '--description',
            self._share.id,
        ]
        verifylist = [
            ('description', True),
            ('share', self._share.id)
        ]

        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        self.cmd.take_action(parsed_args)
        self.shares_mock.update.assert_called_with(
            self._share.id,
            display_description=None)

    def test_share_unset_name_exception(self):
        arglist = [
            '--name',
            self._share.id,
        ]
        verifylist = [
            ('name', True),
            ('share', self._share.id)
        ]

        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        self.shares_mock.update.side_effect = exceptions.BadRequest()
        self.assertRaises(
            osc_exceptions.CommandError, self.cmd.take_action, parsed_args)

    def test_share_unset_property_exception(self):
        arglist = [
            '--property', 'Manila',
            self._share.id,
        ]
        verifylist = [
            ('property', ['Manila']),
            ('share', self._share.id)
        ]

        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        self.cmd.take_action(parsed_args)
        self.shares_mock.delete_metadata.assert_called_with(
            self._share.id,
            parsed_args.property)

        # 404 Not Found would be raised, if property 'Manila' doesn't exist
        self.shares_mock.delete_metadata.side_effect = exceptions.NotFound()
        self.assertRaises(
            osc_exceptions.CommandError, self.cmd.take_action, parsed_args)


class TestResizeShare(TestShare):

    def setUp(self):
        super(TestResizeShare, self).setUp()

        self._share = manila_fakes.FakeShare.create_one_share(
            attrs={'size': 2})
        self.shares_mock.get.return_value = self._share

        # Get the command objects to test
        self.cmd = osc_shares.ResizeShare(self.app, None)

    def test_share_shrink(self):
        arglist = [
            self._share.id,
            '1'
        ]
        verifylist = [
            ('share', self._share.id),
            ('new_size', 1)
        ]

        parsed_args = self.check_parser(self.cmd, arglist, verifylist)
        self.cmd.take_action(parsed_args)
        self.shares_mock.shrink.assert_called_with(
            self._share,
            1
        )

    def test_share_shrink_exception(self):
        arglist = [
            self._share.id,
            '1'
        ]
        verifylist = [
            ('share', self._share.id),
            ('new_size', 1)
        ]
        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        self.shares_mock.shrink.side_effect = Exception()
        self.assertRaises(
            osc_exceptions.CommandError,
            self.cmd.take_action,
            parsed_args)

    def test_share_extend(self):
        arglist = [
            self._share.id,
            '3'
        ]
        verifylist = [
            ('share', self._share.id),
            ('new_size', 3)
        ]

        parsed_args = self.check_parser(self.cmd, arglist, verifylist)
        self.cmd.take_action(parsed_args)
        self.shares_mock.extend.assert_called_with(
            self._share,
            3
        )

    def test_share_extend_exception(self):
        arglist = [
            self._share.id,
            '3'
        ]
        verifylist = [
            ('share', self._share.id),
            ('new_size', 3)
        ]

        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        self.shares_mock.extend.side_effect = Exception()
        self.assertRaises(
            osc_exceptions.CommandError,
            self.cmd.take_action,
            parsed_args)

    def test_share_resize_already_required_size(self):
        arglist = [
            self._share.id,
            '2'
        ]
        verifylist = [
            ('share', self._share.id),
            ('new_size', 2)
        ]

        parsed_args = self.check_parser(self.cmd, arglist, verifylist)
        self.assertRaises(
            osc_exceptions.CommandError,
            self.cmd.take_action,
            parsed_args
        )

    def test_share_missing_args(self):
        arglist = [
            self._share.id
        ]
        verifylist = [
            ('share', self._share.id)
        ]

        self.assertRaises(osc_utils.ParserException,
                          self.check_parser, self.cmd, arglist, verifylist)
