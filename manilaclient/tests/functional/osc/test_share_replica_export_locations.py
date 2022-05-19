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

import json
from manilaclient.tests.functional.osc import base
from tempest.lib.common.utils import data_utils


class ShareReplicaExportLocationsCLITest(base.OSCClientTestBase):

    def test_openstack_share_replica_export_location_list(self):
        slug = 'replica-supported'
        share_type = self.create_share_type(
            data_utils.rand_name(slug), 'False', extra_specs={
                'replication_type': 'readable'})
        share = self.create_share(share_type=share_type['name'])
        replica = self.create_share_replica(share['id'], wait=True)
        rep_exp_loc_list = self.listing_result(
            'share replica export location', f'list {replica["id"]}')
        self.assertTableStruct(rep_exp_loc_list, [
            'ID',
            'Availability Zone',
            'Replica State',
            'Preferred',
            'Path'
        ])
        exp_loc_list = self.openstack(
            f'share replica show {replica["id"]} -f json')
        exp_loc_list = json.loads(exp_loc_list)

        self.assertIn(exp_loc_list.get('export_locations')[0]['id'],
                      [item['ID'] for item in rep_exp_loc_list])

    def test_openstack_share_replica_export_location_show(self):
        slug = 'replica-supported'
        share_type = self.create_share_type(
            data_utils.rand_name(slug), 'False', extra_specs={
                'replication_type': 'readable'})
        share = self.create_share(share_type=share_type['name'])
        replica = self.create_share_replica(share['id'], wait=True)
        rep_exp_loc_obj = self.get_share_replica_export_locations(
            replica['id'])[0]
        exp_loc_list = self.openstack(
            f'share replica show {replica["id"]} -f json')
        exp_loc_list = json.loads(exp_loc_list)
        result = self.dict_result(
            'share replica export location',
            f'show {replica["id"]} {rep_exp_loc_obj["ID"]}')
        export_location = exp_loc_list['export_locations'][0]
        self.assertEqual(result['id'], export_location['id'])
