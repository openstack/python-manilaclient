# -*- coding: utf-8 -*-
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

import ast
import ddt
from tempest.lib.common.utils import data_utils
from tempest.lib import exceptions as tempest_lib_exc

from manilaclient.tests.functional import base
from manilaclient.tests.functional import utils


@ddt.ddt
class ShareNetworksReadWriteTest(base.BaseTestCase):

    def setUp(self):
        super(ShareNetworksReadWriteTest, self).setUp()
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

    @ddt.data(
        {'name': data_utils.rand_name('autotest_share_network_name')},
        {'description': 'fake_description'},
        {'neutron_net_id': 'fake_neutron_net_id',
         'neutron_subnet_id': 'fake_neutron_subnet_id'},
    )
    def test_create_delete_share_network(self, net_data):
        share_subnet_support = utils.share_network_subnets_are_supported()
        share_subnet_fields = (
            ['neutron_net_id', 'neutron_subnet_id', 'availability_zone']
            if share_subnet_support else [])
        sn = self.create_share_network(cleanup_in_class=False, **net_data)
        default_subnet = (utils.get_default_subnet(self.user_client, sn['id'])
                          if share_subnet_support
                          else None)

        expected_data = {
            'name': 'None',
            'description': 'None',
            'neutron_net_id': 'None',
            'neutron_subnet_id': 'None',
        }
        expected_data.update(net_data)
        share_network_expected_data = [
            (k, v) for k, v in expected_data.items()
            if k not in share_subnet_fields]
        share_subnet_expected_data = [
            (k, v) for k, v in expected_data.items()
            if k in share_subnet_fields]

        for k, v in share_network_expected_data:
            self.assertEqual(v, sn[k])
        for k, v in share_subnet_expected_data:
            self.assertEqual(v, default_subnet[k])

        self.admin_client.delete_share_network(sn['id'])
        self.admin_client.wait_for_share_network_deletion(sn['id'])

    @utils.skip_if_microversion_not_supported('2.51')
    def test_create_delete_share_network_with_az(self):
        share_subnet_fields = (
            ['neutron_net_id', 'neutron_subnet_id', 'availability_zone'])
        az = self.user_client.list_availability_zones()[0]
        net_data = {
            'neutron_net_id': 'fake_neutron_net_id',
            'neutron_subnet_id': 'fake_neutron_subnet_id',
            'availability_zone': az['Name']
        }
        sn = self.create_share_network(cleanup_in_class=False, **net_data)
        default_subnet = utils.get_subnet_by_availability_zone_name(
            self.user_client, sn['id'], az['Name'])

        expected_data = {
            'name': 'None',
            'description': 'None',
            'neutron_net_id': 'None',
            'neutron_subnet_id': 'None',
            'availability_zone': 'None',
        }
        expected_data.update(net_data)
        share_network_expected_data = [
            (k, v) for k, v in expected_data.items()
            if k not in share_subnet_fields]
        share_subnet_expected_data = [
            (k, v) for k, v in expected_data.items()
            if k in share_subnet_fields]

        for k, v in share_network_expected_data:
            self.assertEqual(v, sn[k])
        for k, v in share_subnet_expected_data:
            self.assertEqual(v, default_subnet[k])

        self.admin_client.delete_share_network(sn['id'])
        self.admin_client.wait_for_share_network_deletion(sn['id'])

    def test_get_share_network_with_neutron_data(self):
        get = self.admin_client.get_share_network(self.sn['id'])

        self.assertEqual(self.name, get['name'])
        self.assertEqual(self.description, get['description'])
        if not utils.share_network_subnets_are_supported():
            self.assertEqual(self.neutron_net_id, get['neutron_net_id'])
            self.assertEqual(self.neutron_subnet_id, get['neutron_subnet_id'])

    def _get_expected_update_data(self, net_data, net_creation_data):
        # NOTE(dviroel): When subnets are supported, the outputs are converted
        # from string to literal structures in order to process the content of
        # 'share_network_subnets' field.
        default_return_value = (
            None if utils.share_network_subnets_are_supported() else 'None')

        expected_nn_id = (
            default_return_value
            if net_data.get('neutron_net_id')
            else net_creation_data.get('neutron_net_id', default_return_value))
        expected_nsn_id = (
            default_return_value
            if net_data.get('neutron_subnet_id')
            else net_creation_data.get('neutron_subnet_id',
                                       default_return_value))
        return expected_nn_id, expected_nsn_id

    @ddt.data(
        ({'name': data_utils.rand_name('autotest_share_network_name')}, {}),
        ({'description': 'fake_description'}, {}),
        ({'neutron_net_id': 'fake_neutron_net_id',
          'neutron_subnet_id': 'fake_neutron_subnet_id'}, {}),
        ({'name': '""'}, {}),
        ({'description': '""'}, {}),
        ({'neutron_net_id': '""'},
         {'neutron_net_id': 'fake_nn_id', 'neutron_subnet_id': 'fake_nsn_id'}),
        ({'neutron_subnet_id': '""'},
         {'neutron_net_id': 'fake_nn_id', 'neutron_subnet_id': 'fake_nsn_id'})
    )
    @ddt.unpack
    def test_create_update_share_network(self, net_data, net_creation_data):
        sn = self.create_share_network(
            cleanup_in_class=False, **net_creation_data)

        update = self.admin_client.update_share_network(sn['id'], **net_data)

        expected_nn_id, expected_nsn_id = self._get_expected_update_data(
            net_data, net_creation_data)

        expected_data = {
            'name': 'None',
            'description': 'None',
            'neutron_net_id': expected_nn_id,
            'neutron_subnet_id': expected_nsn_id,
        }
        subnet_keys = []
        if utils.share_network_subnets_are_supported():
            subnet_keys = ['neutron_net_id', 'neutron_subnet_id']
            subnet = ast.literal_eval(update['share_network_subnets'])

        update_values = dict([(k, v) for k, v in net_data.items()
                              if v != '""'])
        expected_data.update(update_values)

        for k, v in expected_data.items():
            if k in subnet_keys:
                self.assertEqual(v, subnet[0][k])
            else:
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
        assert_subnet_fields = utils.share_network_subnets_are_supported()
        share_subnet_fields = (['neutron_subnet_id', 'neutron_net_id']
                               if assert_subnet_fields
                               else [])
        share_network_filters = [(k, v) for k, v in filters.items()
                                 if k not in share_subnet_fields]
        share_network_subnet_filters = [(k, v) for k, v in filters.items()
                                        if k in share_subnet_fields]
        share_networks = self.admin_client.list_share_networks(filters=filters)

        self.assertGreater(len(share_networks), 0)
        self.assertTrue(
            any(self.sn['id'] == sn['id'] for sn in share_networks))
        for sn in share_networks:
            try:
                share_network = self.admin_client.get_share_network(sn['id'])
                default_subnet = (
                    utils.get_default_subnet(self.user_client, sn['id'])
                    if assert_subnet_fields
                    else None)
            except tempest_lib_exc.NotFound:
                # NOTE(vponomaryov): Case when some share network was deleted
                # between our 'list' and 'get' requests. Skip such case.
                continue
            for k, v in share_network_filters:
                self.assertIn(k, share_network)
                self.assertEqual(v, share_network[k])
            for k, v in share_network_subnet_filters:
                self.assertIn(k, default_subnet)
                self.assertEqual(v, default_subnet[k])

    def test_list_share_networks_filter_by_project_id(self):
        project_id = self.admin_client.get_project_id(
            self.admin_client.tenant_name)
        filters = {'project_id': project_id}
        self._list_share_networks_with_filters(filters)

    def test_list_share_networks_filter_by_name(self):
        filters = {'name': self.name}
        self._list_share_networks_with_filters(filters)

    def test_list_share_networks_filter_by_description(self):
        filters = {'description': self.description}
        self._list_share_networks_with_filters(filters)

    def test_list_share_networks_filter_by_neutron_net_id(self):
        filters = {'neutron_net_id': self.neutron_net_id}
        self._list_share_networks_with_filters(filters)

    def test_list_share_networks_filter_by_neutron_subnet_id(self):
        filters = {'neutron_subnet_id': self.neutron_subnet_id}
        self._list_share_networks_with_filters(filters)

    @ddt.data('name', 'description')
    def test_list_share_networks_filter_by_inexact(self, option):
        self.create_share_network(
            name=data_utils.rand_name('autotest_inexact'),
            description='fake_description_inexact',
            neutron_net_id='fake_neutron_net_id',
            neutron_subnet_id='fake_neutron_subnet_id',
        )

        filters = {option + '~': 'inexact'}
        share_networks = self.admin_client.list_share_networks(
            filters=filters)

        self.assertGreater(len(share_networks), 0)

    def test_list_share_networks_by_inexact_unicode_option(self):
        self.create_share_network(
            name=u'网络名称',
            description=u'网络描述',
            neutron_net_id='fake_neutron_net_id',
            neutron_subnet_id='fake_neutron_subnet_id',
        )

        filters = {'name~': u'名称'}
        share_networks = self.admin_client.list_share_networks(
            filters=filters)

        self.assertGreater(len(share_networks), 0)

        filters = {'description~': u'描述'}
        share_networks = self.admin_client.list_share_networks(
            filters=filters)

        self.assertGreater(len(share_networks), 0)
