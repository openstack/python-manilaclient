#   Copyright 2021 Red Hat Inc. All rights reserved.
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

from osc_lib import exceptions as osc_exceptions
from osc_lib import utils as osc_lib_utils

from manilaclient.common.apiclient import exceptions as api_exceptions
from manilaclient.common import cliutils
from manilaclient.osc.v2 import (
    share_snapshot_instances as osc_share_snapshot_instances)
from manilaclient.tests.unit.osc import osc_utils
from manilaclient.tests.unit.osc.v2 import fakes as manila_fakes

COLUMNS = ['ID', 'Snapshot ID', 'Status']

COLUMNS_DETAIL = [
    'ID',
    'Snapshot ID',
    'Status',
    'Created At',
    'Updated At',
    'Share ID',
    'Share Instance ID',
    'Progress',
    'Provider Location'
]


class TestShareSnapshotInstance(manila_fakes.TestShare):

    def setUp(self):
        super(TestShareSnapshotInstance, self).setUp()

        self.share_snapshots_mock = (
            self.app.client_manager.share.share_snapshots)
        self.share_snapshots_mock.reset_mock()

        self.share_snapshot_instances_mock = (
            self.app.client_manager.share.share_snapshot_instances)
        self.share_snapshot_instances_mock.reset_mock()

        self.share_snapshot_instances_el_mock = (
            self.app.client_manager
                .share.share_snapshot_instance_export_locations)
        self.share_snapshot_instances_el_mock.reset_mock()


class TestShareSnapshotInstanceList(TestShareSnapshotInstance):

    def setUp(self):
        super(TestShareSnapshotInstanceList, self).setUp()

        self.share_snapshot_instances = (
            manila_fakes.FakeShareSnapshotIntances
                        .create_share_snapshot_instances(count=2))

        self.share_snapshot_instances_mock.list.return_value = (
            self.share_snapshot_instances)

        self.cmd = (
            osc_share_snapshot_instances.ListShareSnapshotInstance(self.app,
                                                                   None))

    def test_share_snapshot_instance_list(self):
        values = (osc_lib_utils.get_dict_properties(
                  s._info, COLUMNS) for s in self.share_snapshot_instances)

        arglist = []
        verifylist = []

        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        columns, data = self.cmd.take_action(parsed_args)

        self.assertEqual(COLUMNS, columns)
        self.assertEqual(list(values), list(data))

    def test_share_snapshot_instance_list_detail(self):
        values = (osc_lib_utils.get_dict_properties(
            s._info, COLUMNS_DETAIL) for s in self.share_snapshot_instances)

        arglist = [
            '--detailed'
        ]

        verifylist = [
            ('detailed', True)
        ]

        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        columns, data = self.cmd.take_action(parsed_args)

        self.assertEqual(COLUMNS_DETAIL, columns)
        self.assertEqual(list(values), list(data))

    def test_share_snapshot_instance_list_snapshot_id(self):
        self.share_snapshot = (
            manila_fakes.FakeShareSnapshot.create_one_snapshot())

        self.share_snapshots_mock.get.return_value = self.share_snapshot
        self.share_snapshot_instances_mock.list.return_value = (
            [self.share_snapshot_instances[0]])

        values = (osc_lib_utils.get_dict_properties(
            s._info, COLUMNS) for s in [self.share_snapshot_instances[0]])

        arglist = [
            '--snapshot', self.share_snapshot.id
        ]
        verifylist = [
            ('snapshot', self.share_snapshot.id)
        ]

        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        columns, data = self.cmd.take_action(parsed_args)

        self.assertEqual(COLUMNS, columns)
        self.assertEqual(list(values), list(data))


class TestShareSnapshotInstanceShow(TestShareSnapshotInstance):

    def setUp(self):
        super(TestShareSnapshotInstanceShow, self).setUp()

        self.share_snapshot_instance = (
            manila_fakes.FakeShareSnapshotIntances
                        .create_one_snapshot_instance())

        self.share_snapshot_instances_mock.get.return_value = (
            self.share_snapshot_instance)

        self.share_snapshot_instances_el_list = (
            manila_fakes.FakeShareSnapshotInstancesExportLocations
            .create_share_snapshot_instances(count=2)
        )

        self.share_snapshot_instances_el_mock.list.return_value = (
            self.share_snapshot_instances_el_list)

        self.cmd = (osc_share_snapshot_instances
                    .ShowShareSnapshotInstance(self.app, None))

        self.share_snapshot_instance._info['export_locations'] = (
            cliutils.convert_dict_list_to_string(
                self.share_snapshot_instances_el_list))

        self.data = self.share_snapshot_instance._info.values()
        self.columns = self.share_snapshot_instance._info.keys()

    def test_share_snapshot_instance_show_missing_args(self):
        arglist = []
        verifylist = []

        self.assertRaises(osc_utils.ParserException,
                          self.check_parser, self.cmd, arglist, verifylist)

    def test_share_snapshot_instance_show(self):
        arglist = [
            self.share_snapshot_instance.id
        ]
        verifylist = [
            ('snapshot_instance', self.share_snapshot_instance.id)
        ]
        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        columns, data = self.cmd.take_action(parsed_args)
        self.share_snapshot_instances_mock.get.assert_called_with(
            self.share_snapshot_instance.id)
        self.assertCountEqual(self.columns, columns)
        self.assertCountEqual(self.data, data)


class TestShareSnapshotInstanceSet(TestShareSnapshotInstance):

    def setUp(self):
        super(TestShareSnapshotInstanceSet, self).setUp()

        self.share_snapshot_instance = (
            manila_fakes.FakeShareSnapshotIntances
                        .create_one_snapshot_instance())

        self.snapshot_instance_status = 'available'

        self.cmd = (osc_share_snapshot_instances
                    .SetShareSnapshotInstance(self.app, None))

    def test_share_snapshot_instance_set_missing_args(self):
        arglist = []
        verifylist = []

        self.assertRaises(osc_utils.ParserException,
                          self.check_parser, self.cmd, arglist, verifylist)

    def test_share_snapshot_instance_set_instance_not_found(self):
        arglist = [
            self.share_snapshot_instance.id,
            '--status', self.snapshot_instance_status
        ]
        verifylist = [
            ('snapshot_instance', self.share_snapshot_instance.id),
            ('status', self.snapshot_instance_status)
        ]

        self.share_snapshot_instances_mock.reset_state.side_effect = (
            api_exceptions.NotFound())

        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        self.assertRaises(osc_exceptions.CommandError,
                          self.cmd.take_action, parsed_args)

    def test_share_snapshot_instance_set(self):
        arglist = [
            self.share_snapshot_instance.id,
            '--status', self.snapshot_instance_status
        ]
        verifylist = [
            ('snapshot_instance', self.share_snapshot_instance.id),
            ('status', self.snapshot_instance_status)
        ]
        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        self.cmd.take_action(parsed_args)
        self.share_snapshot_instances_mock.reset_state.assert_called_with(
            self.share_snapshot_instance.id, self.snapshot_instance_status)
