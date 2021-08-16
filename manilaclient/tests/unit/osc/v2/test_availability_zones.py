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

from manilaclient.osc.v2 import availability_zones as osc_availability_zones
from manilaclient.tests.unit.osc.v2 import fakes as manila_fakes


class TestAvailabilityZones(manila_fakes.TestShare):

    def setUp(self):
        super(TestAvailabilityZones, self).setUp()

        self.zones_mock = self.app.client_manager.share.availability_zones
        self.zones_mock.reset_mock()


class TestShareAvailabilityZoneList(TestAvailabilityZones):

    availability_zones = manila_fakes.FakeShareAvailabilityZones.\
        create_share_availability_zones()
    COLUMNS = ("Id", "Name", "Created At", "Updated At")

    def setUp(self):
        super(TestShareAvailabilityZoneList, self).setUp()

        self.zones_mock.list.return_value = self.availability_zones

        # Get the command object to test
        self.cmd = osc_availability_zones.ShareAvailabilityZoneList(
            self.app, None)

        self.values = (oscutils.get_dict_properties(
            s._info, self.COLUMNS) for s in self.availability_zones)

    def test_share_list_availability_zone(self):
        arglist = []
        verifylist = []
        parsed_args = self.check_parser(self.cmd, arglist, verifylist)
        columns, data = self.cmd.take_action(parsed_args)

        self.assertEqual(self.COLUMNS, columns)
        self.assertCountEqual(list(self.values), list(data))
