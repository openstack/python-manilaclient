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


from manilaclient.tests.functional.osc import base


class AvailabilityZonesCLITest(base.OSCClientTestBase):

    def test_openstack_share_availability_zones_list(self):
        azs = self.listing_result('share', 'availability zone list')
        self.assertTableStruct(azs, [
            'Id',
            'Name',
            'Created At',
            'Updated At'
        ])
        self.assertTrue(len(azs) > 0)
