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


class ShareNetworksCLITest(base.OSCClientTestBase):

    def test_openstack_share_network_create(self):
        share_network_name = 'test_create_share_network'
        share_network = self.create_share_network(name=share_network_name)

        self.assertEqual(share_network['name'], share_network_name)

        share_network_list = self.listing_result('share network', 'list')
        self.assertIn(share_network['id'],
                      [item['ID'] for item in share_network_list])

    def test_openstack_share_network_list(self):
        share_network = self.create_share_network()
        share_network_list = self.listing_result('share network', 'list')
        self.assertTableStruct(share_network_list, [
            'ID',
            'Name',
        ])
        self.assertIn(share_network['id'],
                      [item['ID'] for item in share_network_list])

    def test_openstack_share_network_show(self):
        share_network = self.create_share_network()

        result = self.dict_result('share network',
                                  'show %s' % share_network['id'])
        self.assertEqual(share_network['id'], result['id'])

        listing_result = self.listing_result('share network',
                                             'show %s' % share_network['id'])
        self.assertTableStruct(listing_result, [
            'Field',
            'Value'
        ])

    def test_openstack_share_network_delete(self):
        share_network = self.create_share_network(add_cleanup=False)
        share_network_list = self.listing_result('share network', 'list')

        self.assertIn(share_network['id'],
                      [item['ID'] for item in share_network_list])

        self.openstack('share network delete %s' % share_network['id'])
        self.check_object_deleted('share network', share_network['id'])
        share_network_list_after_delete = self.listing_result('share network',
                                                              'list')

        self.assertNotIn(
            share_network['id'],
            [item['ID'] for item in share_network_list_after_delete])

    def test_openstack_share_network_set(self):
        share_network = self.create_share_network()
        self.openstack('share network set %s --name %s'
                       % (share_network['id'], 'new_name'))
        result = self.dict_result('share network', 'show %s' %
                                  share_network['id'])
        self.assertEqual(share_network['id'], result['id'])
        self.assertEqual('new_name', result['name'])

    def test_openstack_share_network_unset(self):
        share_network = self.create_share_network(name='test_name')
        result1 = self.dict_result('share network', 'show %s' %
                                   share_network['id'])
        self.assertEqual(share_network['id'], result1['id'])
        self.assertEqual(share_network['name'], result1['name'])

        self.openstack('share network unset %s --name'
                       % (share_network['id']))
        result2 = self.dict_result('share network', 'show %s' %
                                   share_network['id'])
        self.assertEqual(share_network['id'], result2['id'])
        self.assertEqual('None', result2['name'])
