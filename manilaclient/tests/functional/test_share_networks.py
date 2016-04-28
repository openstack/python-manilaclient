# Copyright 2015 Mirantis Inc.
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

import ddt
import six
from tempest.lib.common.utils import data_utils
from tempest.lib import exceptions as tempest_lib_exc

from manilaclient.tests.functional import base


@ddt.ddt
class ShareNetworksReadWriteTest(base.BaseTestCase):

    @classmethod
    def setUpClass(cls):
        super(ShareNetworksReadWriteTest, cls).setUpClass()
        cls.name = data_utils.rand_name('autotest')
        cls.description = 'fake_description'
        cls.neutron_net_id = 'fake_neutron_net_id'
        cls.neutron_subnet_id = 'fake_neutron_subnet_id'

        cls.sn = cls.create_share_network(
            name=cls.name,
            description=cls.description,
            neutron_net_id=cls.neutron_net_id,
            neutron_subnet_id=cls.neutron_subnet_id,
        )

    @ddt.data(
        {'name': data_utils.rand_name('autotest_share_network_name')},
        {'description': 'fake_description'},
        {'nova_net_id': 'fake_nova_net_id'},
        {'neutron_net_id': 'fake_neutron_net_id',
         'neutron_subnet_id': 'fake_neutron_subnet_id'},
    )
    def test_create_delete_share_network(self, net_data):
        sn = self.create_share_network(cleanup_in_class=False, **net_data)

        expected_data = {
            'name': 'None',
            'description': 'None',
            'nova_net_id': 'None',
            'neutron_net_id': 'None',
            'neutron_subnet_id': 'None',
        }
        expected_data.update(net_data)

        for k, v in expected_data.items():
            self.assertEqual(v, sn[k])

        self.admin_client.delete_share_network(sn['id'])
        self.admin_client.wait_for_share_network_deletion(sn['id'])

    def test_get_share_network_with_neutron_data(self):
        get = self.admin_client.get_share_network(self.sn['id'])

        self.assertEqual(self.name, get['name'])
        self.assertEqual(self.description, get['description'])
        self.assertEqual(self.neutron_net_id, get['neutron_net_id'])
        self.assertEqual(self.neutron_subnet_id, get['neutron_subnet_id'])

        # We did not set Nova data, so, we expect these fields to be set
        # to None.
        self.assertEqual('None', get['nova_net_id'])

    def test_get_share_network_with_nova_data(self):
        name = data_utils.rand_name('autotest')
        description = 'fake_description'
        nova_net_id = 'fake_nova_net_id'

        create = self.create_share_network(
            name=name,
            description=description,
            nova_net_id=nova_net_id,
            cleanup_in_class=False)

        self.assertEqual(name, create['name'])
        self.assertEqual(description, create['description'])
        self.assertEqual(nova_net_id, create['nova_net_id'])

        # We did not set Neutron data, so, we expect these fields to be set
        # to None.
        self.assertEqual('None', create['neutron_net_id'])
        self.assertEqual('None', create['neutron_subnet_id'])

    @ddt.data(
        {'name': data_utils.rand_name('autotest_share_network_name')},
        {'description': 'fake_description'},
        {'nova_net_id': 'fake_nova_net_id'},
        {'neutron_net_id': 'fake_neutron_net_id',
         'neutron_subnet_id': 'fake_neutron_subnet_id'},
        {'name': '""'},
        {'description': '""'},
        {'nova_net_id': '""'},
        {'neutron_net_id': '""'},
        {'neutron_subnet_id': '""'},
    )
    def test_create_update_share_network(self, net_data):
        sn = self.create_share_network(cleanup_in_class=False)

        update = self.admin_client.update_share_network(sn['id'], **net_data)

        expected_data = {
            'name': 'None',
            'description': 'None',
            'nova_net_id': 'None',
            'neutron_net_id': 'None',
            'neutron_subnet_id': 'None',
        }
        update_values = dict([(k, v) for k, v in six.iteritems(net_data)
                              if v != '""'])
        expected_data.update(update_values)

        for k, v in expected_data.items():
            self.assertEqual(v, update[k])

        self.admin_client.delete_share_network(sn['id'])
        self.admin_client.wait_for_share_network_deletion(sn['id'])

    @ddt.data(True, False)
    def test_list_share_networks(self, all_tenants):
        share_networks = self.admin_client.list_share_networks(all_tenants)

        self.assertTrue(
            any(self.sn['id'] == sn['id'] for sn in share_networks))
        for sn in share_networks:
            self.assertEqual(2, len(sn))
            self.assertIn('id', sn)
            self.assertIn('name', sn)

    def test_list_share_networks_select_column(self):
        share_networks = self.admin_client.list_share_networks(columns="id")
        self.assertTrue(any(s['Id'] is not None for s in share_networks))
        self.assertTrue(all('Name' not in s for s in share_networks))
        self.assertTrue(all('name' not in s for s in share_networks))

    def _list_share_networks_with_filters(self, filters):
        share_networks = self.admin_client.list_share_networks(filters=filters)

        self.assertTrue(len(share_networks) > 0)
        self.assertTrue(
            any(self.sn['id'] == sn['id'] for sn in share_networks))
        for sn in share_networks:
            try:
                get = self.admin_client.get_share_network(sn['id'])
            except tempest_lib_exc.NotFound:
                # NOTE(vponomaryov): Case when some share network was deleted
                # between our 'list' and 'get' requests. Skip such case.
                continue
            for k, v in filters.items():
                self.assertIn(k, get)
                self.assertEqual(v, get[k])

    def test_list_share_networks_filter_by_project_id(self):
        project_id = self.admin_client.get_project_id(
            self.admin_client.tenant_name)
        filters = {'project_id': project_id}
        self._list_share_networks_with_filters(filters)

    def test_list_share_networks_filter_by_name(self):
        filters = {'name': self.name}
        self._list_share_networks_with_filters(filters)

    def test_list_share_networks_filter_by_neutron_net_id(self):
        filters = {'neutron_net_id': self.neutron_net_id}
        self._list_share_networks_with_filters(filters)

    def test_list_share_networks_filter_by_neutron_subnet_id(self):
        filters = {'neutron_subnet_id': self.neutron_subnet_id}
        self._list_share_networks_with_filters(filters)
