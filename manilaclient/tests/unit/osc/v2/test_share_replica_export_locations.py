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
from osc_lib import utils as oscutils

from manilaclient.osc.v2 import (
    share_replica_export_locations as osc_replica_el
)

from manilaclient.tests.unit.osc.v2 import fakes as manila_fakes


class TestShareReplica(manila_fakes.TestShare):

    def setUp(self):
        super(TestShareReplica, self).setUp()

        self.replicas_mock = self.app.client_manager.share.share_replicas
        self.replicas_mock.reset_mock()

        self.export_locations_mock = (
            self.app.client_manager.share.share_replica_export_locations)
        self.export_locations_mock.reset_mock()


class TestShareReplicaExportLocationList(TestShareReplica):

    columns = [
        'ID',
        'Availability Zone',
        'Replica State',
        'Preferred',
        'Path'
    ]

    def setUp(self):
        super(TestShareReplicaExportLocationList, self).setUp()

        self.share_replica = (
            manila_fakes.FakeShareReplica.create_one_replica())

        self.replicas_mock.get.return_value = self.share_replica

        self.export_locations = ([
            manila_fakes.FakeShareExportLocation.create_one_export_location()
        ])

        self.export_locations_mock.list.return_value = self.export_locations
        self.values = (oscutils.get_dict_properties(
            e._info, self.columns) for e in self.export_locations)

        self.cmd = osc_replica_el.ShareReplicaListExportLocation(
            self.app, None)

    def test_replica_export_locations_list(self):
        arglist = [
            self.share_replica.id
        ]
        verifylist = [
            ('replica', self.share_replica.id)
        ]

        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        columns, data = self.cmd.take_action(parsed_args)

        self.replicas_mock.get.assert_called_with(self.share_replica.id)
        self.export_locations_mock.list.assert_called_with(
            self.share_replica)

        self.assertEqual(self.columns, columns)
        self.assertCountEqual(self.values, data)


class TestShareReplicaExportLocationShow(TestShareReplica):

    def setUp(self):
        super(TestShareReplicaExportLocationShow, self).setUp()

        self.share_replica = (
            manila_fakes.FakeShareReplica.create_one_replica())

        self.replicas_mock.get.return_value = self.share_replica

        self.export_location = (
            manila_fakes.FakeShareExportLocation.create_one_export_location())

        self.export_locations_mock.get.return_value = self.export_location

        self.cmd = osc_replica_el.ShareReplicaShowExportLocation(
            self.app, None)

    def test_replica_export_locations_show(self):
        arglist = [
            self.share_replica.id,
            self.export_location.id
        ]
        verifylist = [
            ('replica', self.share_replica.id),
            ('export_location', self.export_location.id)
        ]

        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        columns, data = self.cmd.take_action(parsed_args)

        self.replicas_mock.get.assert_called_with(self.share_replica.id)
        self.export_locations_mock.get.assert_called_with(
            self.share_replica,
            self.export_location.id)

        self.assertCountEqual(
            tuple(self.export_location._info.keys()),
            columns)
        self.assertCountEqual(self.export_location._info.values(), data)
