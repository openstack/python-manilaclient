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

from oslo_serialization import jsonutils

from tempest.lib.common.utils import data_utils

from manilaclient.tests.functional.osc import base


class SharesGroupTypesCLITest(base.OSCClientTestBase):

    def test_share_group_type_create(self):
        share_group_type_name = 'test_share_group_type_create'
        share_group_type = self.create_share_group_type(
            name=share_group_type_name, share_types='dhss_false')

        self.assertEqual(share_group_type['name'], share_group_type_name)
        self.assertIsNotNone(share_group_type['share_types'])

        shares_group_type_list = self.listing_result(
            'share', 'group type list')
        self.assertIn(
            share_group_type['id'],
            [item['ID'] for item in shares_group_type_list])

    def test_openstack_share_group_type_list(self):
        share_group_type_name = data_utils.rand_name(
            'test_share_group_type_create')
        share_group_type = self.create_share_group_type(
            name=share_group_type_name, share_types='dhss_false')

        shares_group_type_list = self.listing_result(
            'share', 'group type list')
        self.assertTableStruct(shares_group_type_list, [
            'ID',
            'Name',
            'Share Types',
            'Visibility',
            'Is Default',
            'Group Specs'
        ])
        self.assertIn(
            share_group_type['id'],
            [item['ID'] for item in shares_group_type_list])

    def test_openstack_share_group_type_show(self):
        share_group_type_name = data_utils.rand_name(
            'test_share_group_type_create')
        share_type_name = 'dhss_false'
        share_group_type = self.create_share_group_type(
            name=share_group_type_name, share_types=share_type_name)

        shares_group_type_show = self.dict_result(
            'share', f'group type show {share_group_type_name}')
        share_type_id = self.dict_result(
            'share', f'type show {share_type_name}')['id']

        expected_sgt_values = {
            'id': share_group_type['id'],
            'name': share_group_type_name,
            'share_types': share_type_id,
            'visibility': 'public',
            'is_default': 'False',
            'group_specs': ''
        }

        for k, v in shares_group_type_show.items():
            self.assertEqual(expected_sgt_values[k], shares_group_type_show[k])

    def test_openstack_share_group_type_set(self):
        share_group_type_name = data_utils.rand_name(
            'test_share_group_type_create')
        share_type_name = 'dhss_false'
        share_group_type = self.create_share_group_type(
            name=share_group_type_name, share_types=share_type_name)
        shares_group_type_show = self.openstack(
            f'share group type show {share_group_type_name} -f json')
        shares_group_type_show = jsonutils.loads(shares_group_type_show)

        expected_sgt_values = {
            'id': share_group_type['id'],
            'group_specs': {}
        }

        for k, v in expected_sgt_values.items():
            self.assertEqual(expected_sgt_values[k], shares_group_type_show[k]
                             )

        group_snap_key = 'snapshot_support'
        group_snap_value = 'False'
        group_specs = f"{group_snap_key}={group_snap_value}"

        self.dict_result(
            'share',
            f'group type set {share_group_type_name} '
            f'--group-specs {group_specs}')

        shares_group_type_show = self.openstack(
            f'share group type show {share_group_type_name} -f json')
        shares_group_type_show = jsonutils.loads(shares_group_type_show)

        expected_sgt_values = {
            'id': share_group_type['id'],
            'group_specs': {
                group_snap_key: group_snap_value
            }
        }

        for k, v in expected_sgt_values.items():
            self.assertEqual(expected_sgt_values[k], shares_group_type_show[k])

    def test_openstack_share_group_type_unset(self):
        share_group_type_name = data_utils.rand_name(
            'test_share_group_type_create')
        group_snap_key = 'snapshot_support'
        group_snap_value = 'False'
        group_specs = f"{group_snap_key}={group_snap_value}"
        share_group_type = self.create_share_group_type(
            name=share_group_type_name, share_types='dhss_false',
            group_specs=group_specs)
        shares_group_type_show = self.openstack(
            f'share group type show {share_group_type_name} -f json')
        shares_group_type_show = jsonutils.loads(shares_group_type_show)

        expected_sgt_values = {
            'id': share_group_type['id'],
            'group_specs': {
                group_snap_key: group_snap_value
            }
        }

        for k, v in expected_sgt_values.items():
            self.assertEqual(expected_sgt_values[k], shares_group_type_show[k]
                             )

        self.dict_result(
            'share',
            f'group type unset {share_group_type_name} '
            f'{group_snap_key}')

        shares_group_type_show = self.openstack(
            f'share group type show {share_group_type_name} -f json')
        shares_group_type_show = jsonutils.loads(shares_group_type_show)

        expected_sgt_values = {
            'id': share_group_type['id'],
            'group_specs': {}
        }

        for k, v in expected_sgt_values.items():
            self.assertEqual(expected_sgt_values[k], shares_group_type_show[k])
