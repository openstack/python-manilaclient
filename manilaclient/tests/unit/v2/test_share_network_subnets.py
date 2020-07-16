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

from unittest import mock

import ddt

from manilaclient.tests.unit import utils
from manilaclient.tests.unit.v2 import fakes
from manilaclient.v2 import share_network_subnets


@ddt.ddt
class ShareNetworkSubnetTest(utils.TestCase):

    def setUp(self):
        super(ShareNetworkSubnetTest, self).setUp()
        self.manager = share_network_subnets.ShareNetworkSubnetManager(
            fakes.FakeClient())

    def test_create(self):
        share_network_id = 'fake_share_net_id'
        expected_url = share_network_subnets.RESOURCES_PATH % {
            'share_network_id': share_network_id
        }
        expected_values = {
            'neutron_net_id': 'fake_net_id',
            'neutron_subnet_id': 'fake_subnet_id',
            'availability_zone': 'fake_availability_zone',
        }
        expected_body = {'share-network-subnet': expected_values}
        payload = expected_values.copy()
        payload.update({'share_network_id': share_network_id})

        with mock.patch.object(self.manager, '_create', fakes.fake_create):
            result = self.manager.create(**payload)

            self.assertEqual(expected_url, result['url'])
            self.assertEqual(
                share_network_subnets.RESOURCE_NAME,
                result['resp_key'])
            self.assertEqual(
                expected_body,
                result['body'])

    def test_get(self):
        share_network = 'fake_share_network'
        share_subnet = 'fake_share_subnet'

        with mock.patch.object(self.manager, '_get', mock.Mock()):
            self.manager.get(share_network, share_subnet)

            self.manager._get.assert_called_once_with(
                share_network_subnets.RESOURCE_PATH % {
                    'share_network_id': share_network,
                    'share_network_subnet_id': share_subnet
                },
                share_network_subnets.RESOURCE_NAME)

    def test_delete(self):
        share_network = 'fake_share_network'
        share_subnet = 'fake_share_subnet'

        with mock.patch.object(self.manager, '_delete', mock.Mock()):
            self.manager.delete(share_network, share_subnet)

            self.manager._delete.assert_called_once_with(
                share_network_subnets.RESOURCE_PATH % {
                    'share_network_id': share_network,
                    'share_network_subnet_id': share_subnet
                })
