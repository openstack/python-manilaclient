# Copyright 2021 NetApp, Inc.
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

from osc_lib import utils as osc_lib_utils

from manilaclient.osc.v2 \
    import share_instance_export_locations \
    as osc_share_instance_export_locations

from manilaclient.tests.unit.osc import osc_utils
from manilaclient.tests.unit.osc.v2 import fakes as manila_fakes


class TestShareInstanceExportLocation(manila_fakes.TestShare):

    def setUp(self):
        super(TestShareInstanceExportLocation, self).setUp()

        self.instances_mock = self.app.client_manager.share.share_instances
        self.instances_mock.reset_mock()

        self.instance_export_locations_mock = (
            self.app.client_manager.share.share_instance_export_locations
        )

        self.instance_export_locations_mock.reset_mock()


class TestShareInstanceExportLocationList(TestShareInstanceExportLocation):

    column_headers = [
        'ID',
        'Path',
        'Is Admin Only',
        'Preferred',
    ]

    def setUp(self):
        super(TestShareInstanceExportLocationList, self).setUp()

        self.instance = (
            manila_fakes.FakeShareInstance.create_one_share_instance()
        )
        self.instances_mock.get.return_value = self.instance

        self.instance_export_locations = (
            manila_fakes.FakeShareExportLocation.
            create_share_export_locations()
        )
        self.instance_export_locations_mock.list.return_value = \
            self.instance_export_locations

        self.data = (osc_lib_utils.get_dict_properties(
            i._info, self.column_headers)
            for i in self.instance_export_locations)

        self.cmd = (
            osc_share_instance_export_locations.
            ShareInstanceListExportLocation(self.app, None)
        )

    def test_share_instance_export_locations_list_missing_args(self):
        arglist = []
        verifylist = []

        self.assertRaises(
            osc_utils.ParserException,
            self.check_parser, self.cmd, arglist, verifylist)

    def test_share_instance_export_locations_list(self):
        arglist = [
            self.instance.id
        ]

        verifylist = [
            ('instance', self.instance.id)
        ]

        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        columns, data = self.cmd.take_action(parsed_args)

        self.instances_mock.get.assert_called_with(
            self.instance.id
        )

        self.instance_export_locations_mock.list.assert_called_with(
            self.instance,
            search_opts=None
        )

        self.assertCountEqual(self.column_headers, columns)
        self.assertCountEqual(self.data, data)


class TestShareInstanceExportLocationShow(TestShareInstanceExportLocation):

    def setUp(self):
        super(TestShareInstanceExportLocationShow, self).setUp()

        self.share_instance_export_locations = (
            manila_fakes.FakeShareExportLocation.
            create_one_export_location()
        )
        self.instance_export_locations_mock.get.return_value = \
            self.share_instance_export_locations

        self.instance = (
            manila_fakes.FakeShareInstance.create_one_share_instance()
        )
        self.instances_mock.get.return_value = self.instance

        self.cmd = (
            osc_share_instance_export_locations.
            ShareInstanceShowExportLocation(self.app, None)
        )

        self.data = tuple(self.share_instance_export_locations._info.values())
        self.columns = tuple(self.share_instance_export_locations._info.keys())

    def test_share_instance_export_locations_show_missing_args(self):
        arglist = []
        verifylist = []

        self.assertRaises(
            osc_utils.ParserException,
            self.check_parser, self.cmd, arglist, verifylist)

    def test_share_instance_export_locations_show(self):
        arglist = [
            self.instance.id,
            self.share_instance_export_locations.id,
        ]

        verifylist = [
            ('instance', self.instance.id),
            ('export_location', self.share_instance_export_locations.id)
        ]

        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        columns, data = self.cmd.take_action(parsed_args)

        self.instances_mock.get.assert_called_with(
            self.instance.id
        )

        self.instance_export_locations_mock.get.assert_called_with(
            self.instance.id,
            self.share_instance_export_locations.id
        )

        self.assertCountEqual(self.columns, columns)
        self.assertCountEqual(self.data, data)
