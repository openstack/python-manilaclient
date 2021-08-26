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

from osc_lib import utils as osc_lib_utils

from manilaclient.osc.v2 import (share_snapshot_instance_export_locations as
                                 osc_snapshot_instance_locations)
from manilaclient.tests.unit.osc import osc_utils
from manilaclient.tests.unit.osc.v2 import fakes as manila_fakes

COLUMNS = ['ID', 'Path', 'Is Admin only']


class TestShareSnapshotInstanceExportLocation(manila_fakes.TestShare):

    def setUp(self):
        super(TestShareSnapshotInstanceExportLocation, self).setUp()

        self.share_snapshot_instances_mock = (
            self.app.client_manager.share.share_snapshot_instances)
        self.share_snapshot_instances_mock.reset_mock()

        self.share_snapshot_instances_el_mock = (
            self.app.client_manager
                .share.share_snapshot_instance_export_locations)
        self.share_snapshot_instances_el_mock.reset_mock()


class TestShareSnapshotInstanceExportLocationList(
        TestShareSnapshotInstanceExportLocation):

    def setUp(self):
        super(TestShareSnapshotInstanceExportLocationList, self).setUp()

        self.share_snapshot_instance = (
            manila_fakes.FakeShareSnapshotIntances
            .create_one_snapshot_instance())

        self.share_snapshot_instances_export_locations = (
            manila_fakes.FakeShareSnapshotInstancesExportLocations
            .create_share_snapshot_instances(count=2)
        )

        self.share_snapshot_instances_mock.get.return_value = (
            self.share_snapshot_instance)

        self.share_snapshot_instances_el_mock.list.return_value = (
            self.share_snapshot_instances_export_locations)

        self.cmd = (osc_snapshot_instance_locations
                    .ShareSnapshotInstanceExportLocationList(self.app,
                                                             None))

    def test_share_snapshot_instance_export_location_list_missing_args(self):
        arglist = []
        verifylist = []

        self.assertRaises(osc_utils.ParserException,
                          self.check_parser, self.cmd, arglist, verifylist)

    def test_share_snapshot_instance_export_location_list(self):
        values = (osc_lib_utils.get_dict_properties(
                  s._info, COLUMNS) for s in
                  self.share_snapshot_instances_export_locations)
        arglist = [
            self.share_snapshot_instance.id
        ]
        verifylist = [
            ('instance', self.share_snapshot_instance.id)
        ]

        parsed_args = self.check_parser(self.cmd, arglist, verifylist)
        columns, data = self.cmd.take_action(parsed_args)

        self.assertEqual(COLUMNS, columns)
        self.assertEqual(list(values), list(data))


class TestShareSnapshotInstanceExportLocationShow(
        TestShareSnapshotInstanceExportLocation):

    def setUp(self):
        super(TestShareSnapshotInstanceExportLocationShow, self).setUp()

        self.share_snapshot_instance = (
            manila_fakes.FakeShareSnapshotIntances
            .create_one_snapshot_instance())

        self.share_snapshot_instances_export_location = (
            manila_fakes.FakeShareSnapshotInstancesExportLocations
            .create_one_snapshot_instance()
        )

        self.share_snapshot_instances_mock.get.return_value = (
            self.share_snapshot_instance)

        self.share_snapshot_instances_el_mock.get.return_value = (
            self.share_snapshot_instances_export_location)

        self.cmd = (osc_snapshot_instance_locations
                    .ShareSnapshotInstanceExportLocationShow(self.app,
                                                             None))

        self.data = (self.share_snapshot_instances_export_location.
                     _info.values())
        self.columns = (self.share_snapshot_instances_export_location.
                        _info.keys())

    def test_share_snapshot_instance_export_location_show_missing_args(self):
        arglist = []
        verifylist = []

        self.assertRaises(osc_utils.ParserException,
                          self.check_parser, self.cmd, arglist, verifylist)

    def test_share_snapshot_instance_export_location_show(self):
        arglist = [
            self.share_snapshot_instance.id,
            self.share_snapshot_instances_export_location.id
        ]
        verifylist = [
            ('snapshot_instance', self.share_snapshot_instance.id),
            ('export_location',
             self.share_snapshot_instances_export_location.id)
        ]

        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        columns, data = self.cmd.take_action(parsed_args)

        self.share_snapshot_instances_mock.get.assert_called_with(
            self.share_snapshot_instance.id)
        self.share_snapshot_instances_el_mock.get.assert_called_with(
            self.share_snapshot_instances_export_location.id,
            snapshot_instance=self.share_snapshot_instance)
        self.assertCountEqual(self.columns, columns)
        self.assertCountEqual(self.data, data)
