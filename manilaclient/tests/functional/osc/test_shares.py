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
from tempest.lib.common.utils import data_utils


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

    def test_openstack_share_set(self):
        share = self.create_share()
        self.openstack(f'share set {share["id"]} --name new_name '
                       f'--property key=value')
        result = self.dict_result('share', f'show {share["id"]}')
        self.assertEqual(share['id'], result['id'])
        self.assertEqual('new_name', result['name'])
        self.assertEqual("key='value'", result['properties'])

    def test_openstack_share_unset(self):
        share = self.create_share(name='test_name', properties={
            'foo': 'bar', 'test_key': 'test_value'})
        result1 = self.dict_result('share', f'show {share["id"]}')
        self.assertEqual(share['id'], result1['id'])
        self.assertEqual(share['name'], result1['name'])
        self.assertEqual("foo='bar', test_key='test_value'",
                         result1['properties'])

        self.openstack(f'share unset {share["id"]} --name --property test_key')
        result2 = self.dict_result('share', f'show {share["id"]}')
        self.assertEqual(share['id'], result2['id'])
        self.assertEqual('None', result2['name'])
        self.assertEqual("foo='bar'", result2['properties'])

    def test_openstack_share_resize(self):
        share = self.create_share()
        self.openstack(f'share resize {share["id"]} 10 --wait ')
        result = self.dict_result('share', f'show {share["id"]}')
        self.assertEqual('10', result['size'])

    def test_openstack_share_revert(self):
        slug = "revert_test"
        share_type = self.create_share_type(
            name=data_utils.rand_name(slug),
            snapshot_support=True,
            revert_to_snapshot_support=True)
        share = self.create_share(share_type=share_type['id'], size=10)
        snapshot = self.create_snapshot(share['id'], wait=True)
        self.assertEqual(snapshot['size'], share['size'])
        self.openstack(f'share resize {share["id"]} 15 --wait')
        result1 = self.dict_result('share', f'show {share["id"]}')
        self.assertEqual('15', result1["size"])

        self.openstack(f'share revert {snapshot["id"]} --wait')

        result2 = self.dict_result('share', f'show {share["id"]}')

        self.assertEqual('10', result2['size'])

    def test_openstack_share_abandon_adopt(self):
        share = self.create_share(add_cleanup=False)
        shares_list = self.listing_result('share', 'list')
        self.assertIn(share['id'], [item['ID'] for item in shares_list])
        export_location_obj = self.get_share_export_locations(share['id'])[0]
        export_location = export_location_obj['Path']
        source = self.dict_result('share', f'show {share["id"]}')
        host = source['host']
        protocol = source['share_proto']
        share_type = source['share_type']
        self.openstack(f'share abandon {share["id"]} --wait')

        # verify abandonded
        self.check_object_deleted('share', share['id'])
        shares_list_after_delete = self.listing_result('share', 'list')
        self.assertNotIn(
            share['id'], [item['ID'] for item in shares_list_after_delete])

        result = self.dict_result(
            'share', f'adopt {host} {protocol} {export_location} '
                     f'--share-type {share_type} --wait')

        # verify adopted
        self.assertEqual(host, result['host'])
        self.assertEqual(protocol, result['share_proto'])
        self.openstack(f'share delete {result["id"]} --wait')
