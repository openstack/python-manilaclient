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


class SharesCLITest(base.OSCClientTestBase):

    def test_openstack_share_create(self):
        share_name = 'test_create_share'
        share = self.create_share(name=share_name)

        self.assertEqual(share['share_proto'], 'NFS')
        self.assertEqual(share['size'], '1')
        self.assertEqual(share['name'], share_name)

        shares_list = self.listing_result('share', 'list')
        self.assertIn(share['id'], [item['ID'] for item in shares_list])

    def test_openstack_share_list(self):
        share = self.create_share()
        shares_list = self.listing_result('share', 'list')
        self.assertTableStruct(shares_list, [
            'ID',
            'Name',
            'Size',
            'Share Proto',
            'Status',
            'Is Public',
            'Share Type Name',
            'Host',
            'Availability Zone'
        ])
        self.assertIn(share['id'], [item['ID'] for item in shares_list])

    def test_openstack_share_show(self):
        share = self.create_share()

        result = self.dict_result('share', 'show %s' % share['id'])
        self.assertEqual(share['id'], result['id'])

        listing_result = self.listing_result('share', 'show %s' % share['id'])
        self.assertTableStruct(listing_result, [
            'Field',
            'Value'
        ])

    def test_openstack_share_delete(self):
        share = self.create_share(add_cleanup=False)
        shares_list = self.listing_result('share', 'list')

        self.assertIn(share['id'], [item['ID'] for item in shares_list])

        self.openstack('share delete %s' % share['id'])
        self.check_object_deleted('share', share['id'])
        shares_list_after_delete = self.listing_result('share', 'list')

        self.assertNotIn(
            share['id'], [item['ID'] for item in shares_list_after_delete])
