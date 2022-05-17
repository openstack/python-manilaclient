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

from manilaclient.tests.functional.osc import base


class SharesGroupTypeAccessCLITest(base.OSCClientTestBase):

    def test_share_group_type_access_create(self):
        share_group_type_name = self.create_share_group_type(
            share_types='dhss_false', public=False)['name']

        access_list = self.listing_result(
            'share', f'group type access list {share_group_type_name}')
        self.assertEqual(0, len(access_list))

        cmd_output = jsonutils.loads(self.openstack('token issue -f json '))
        auth_project_id = cmd_output['project_id']

        self.share_group_type_access_create(
            share_group_type_name, auth_project_id)

        share_group_type_access_list = self.listing_result(
            'share', f'group type access list {share_group_type_name}')

        self.assertEqual(1, len(share_group_type_access_list))

    def test_share_group_type_access_delete(self):
        share_group_type_name = self.create_share_group_type(
            share_types='dhss_false', public=False)['name']

        access_list = self.listing_result(
            'share', f'group type access list {share_group_type_name}')
        self.assertEqual(0, len(access_list))

        cmd_output = jsonutils.loads(self.openstack('token issue -f json '))
        auth_project_id = cmd_output['project_id']

        # Create using name to ensure that we are "translating" the
        # name into the actual ID in the CLI
        self.share_group_type_access_create(
            share_group_type_name, auth_project_id)

        share_group_type_access_list = self.listing_result(
            'share', f'group type access list {share_group_type_name}')

        self.assertEqual(1, len(share_group_type_access_list))
        self.assertEqual(
            share_group_type_access_list[0]['Project ID'], auth_project_id)

        self.share_group_type_access_delete(
            share_group_type_name, auth_project_id)

        access_list = self.listing_result(
            'share', f'group type access list {share_group_type_name}')
        self.assertEqual(0, len(access_list))

    def test_share_group_type_access_list(self):
        share_group_type_name = self.create_share_group_type(
            share_types='dhss_false', public=False)['name']

        access_list = self.listing_result(
            'share', f'group type access list {share_group_type_name}')
        self.assertEqual(0, len(access_list))

        cmd_output = jsonutils.loads(self.openstack('token issue -f json '))
        auth_project_id = cmd_output['project_id']

        self.share_group_type_access_create(
            share_group_type_name, auth_project_id)

        share_group_type_access_list = self.listing_result(
            'share', f'group type access list {share_group_type_name}')

        self.assertEqual(1, len(share_group_type_access_list))
        self.assertTableStruct(access_list, ['Project ID'])
