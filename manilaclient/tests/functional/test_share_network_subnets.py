# Copyright 2019 NetApp
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
from manilaclient.tests.functional import base
from manilaclient.tests.functional import utils
from tempest.lib.common.utils import data_utils
from tempest.lib import exceptions


@ddt.ddt
@utils.skip_if_microversion_not_supported('2.51')
class ShareNetworkSubnetsReadWriteTest(base.BaseTestCase):

    def setUp(self):
        super(ShareNetworkSubnetsReadWriteTest, self).setUp()
        self.name = data_utils.rand_name('autotest')
        self.description = 'fake_description'
        self.neutron_net_id = 'fake_neutron_net_id'
        self.neutron_subnet_id = 'fake_neutron_subnet_id'

        self.sn = self.create_share_network(
            name=self.name,
            description=self.description,
            neutron_net_id=self.neutron_net_id,
            neutron_subnet_id=self.neutron_subnet_id,
        )

    def test_get_share_network_subnet(self):
        default_subnet = utils.get_default_subnet(self.user_client,
                                                  self.sn['id'])

        subnet = self.user_client.get_share_network_subnet(
            self.sn['id'], default_subnet['id'])

        self.assertEqual(self.neutron_net_id, subnet['neutron_net_id'])
        self.assertEqual(self.neutron_subnet_id, subnet['neutron_subnet_id'])

    def test_get_invalid_share_network_subnet(self):
        self.assertRaises(
            exceptions.CommandFailed,
            self.user_client.get_share_network_subnet,
            self.sn['id'], 'invalid_subnet_id')

    def _get_availability_zone(self):
        availability_zones = self.user_client.list_availability_zones()
        return availability_zones[0]['Name']

    def test_add_share_network_subnet_to_share_network(self):
        neutron_net_id = 'new_neutron_net_id'
        neutron_subnet_id = 'new_neutron_subnet_id'
        availability_zone = self._get_availability_zone()

        subnet = self.add_share_network_subnet(
            self.sn['id'],
            neutron_net_id, neutron_subnet_id,
            availability_zone,
            cleanup_in_class=False)

        self.assertEqual(neutron_net_id, subnet['neutron_net_id'])
        self.assertEqual(neutron_subnet_id, subnet['neutron_subnet_id'])
        self.assertEqual(availability_zone, subnet['availability_zone'])

    @ddt.data(
        {'neutron_net_id': None, 'neutron_subnet_id': 'fake_subnet_id'},
        {'neutron_net_id': 'fake_net_id', 'neutron_subnet_id': None},
        {'availability_zone': 'invalid_availability_zone'},
    )
    def test_add_invalid_share_network_subnet_to_share_network(self, params):
        self.assertRaises(
            exceptions.CommandFailed,
            self.add_share_network_subnet,
            self.sn['id'],
            **params)

    def test_add_share_network_subnet_to_invalid_share_network(self):
        self.assertRaises(
            exceptions.CommandFailed,
            self.add_share_network_subnet,
            'invalid_share_network',
            self.neutron_net_id,
            self.neutron_subnet_id)

    def test_add_delete_share_network_subnet_from_share_network(self):
        neutron_net_id = 'new_neutron_net_id'
        neutron_subnet_id = 'new_neutron_subnet_id'
        availability_zone = self._get_availability_zone()

        subnet = self.add_share_network_subnet(
            self.sn['id'],
            neutron_net_id, neutron_subnet_id,
            availability_zone,
            cleanup_in_class=False)
        self.user_client.delete_share_network_subnet(
            share_network_subnet=subnet['id'],
            share_network=self.sn['id'])

        self.user_client.wait_for_share_network_subnet_deletion(
            share_network_subnet=subnet['id'],
            share_network=self.sn['id'])

    def test_delete_invalid_share_network_subnet(self):
        self.assertRaises(
            exceptions.NotFound,
            self.user_client.delete_share_network_subnet,
            share_network_subnet='invalid_subnet_id',
            share_network=self.sn['id'])
