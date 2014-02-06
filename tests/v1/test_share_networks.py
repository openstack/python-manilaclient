# Copyright 2013 OpenStack LLC.
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
try:
    from collections import OrderedDict
except ImportError:
    from ordereddict import OrderedDict

import mock
import unittest

from manilaclient import exceptions
from manilaclient.v1 import share_networks
from tests.v1 import fakes


class ShareNetworkTest(unittest.TestCase):

    def setUp(self):
        super(ShareNetworkTest, self).setUp()
        self.manager = share_networks.ShareNetworkManager(api=None)

    def test_create(self):
        values = {'neutron_net_id': 'fake net id',
                  'neutron_subnet_id': 'fake subnet id',
                  'name': 'fake name',
                  'description': 'whatever'}
        body_expected = {share_networks.RESOURCE_NAME: values}

        with mock.patch.object(self.manager, '_create', fakes.fake_create):
            result = self.manager.create(**values)

            self.assertEqual(result['url'], share_networks.RESOURCES_PATH)
            self.assertEqual(result['resp_key'], share_networks.RESOURCE_NAME)
            self.assertEqual(
                result['body'],
                body_expected)

    def test_delete(self):
        share_nw = 'fake share nw'
        with mock.patch.object(self.manager, '_delete', mock.Mock()):
            self.manager.delete(share_nw)
            self.manager._delete.assert_called_once_with(
                share_networks.RESOURCE_PATH % share_nw)

    def test_get(self):
        share_nw = 'fake share nw'
        with mock.patch.object(self.manager, '_get', mock.Mock()):
            self.manager.get(share_nw)
            self.manager._get.assert_called_once_with(
                share_networks.RESOURCE_PATH % share_nw,
                share_networks.RESOURCE_NAME)

    def test_list_no_filters(self):
        with mock.patch.object(self.manager, '_list',
                               mock.Mock(return_value=None)):
            self.manager.list()
            self.manager._list.assert_called_once_with(
                share_networks.RESOURCES_PATH,
                share_networks.RESOURCES_NAME)

    def test_list_with_filters(self):
        filters = OrderedDict([('all_tenants', 1), ('status', 'ERROR')])
        expected_path = \
            share_networks.RESOURCES_PATH + '?all_tenants=1&status=ERROR'

        with mock.patch.object(self.manager, '_list',
                               mock.Mock(return_value=None)):
            self.manager.list(search_opts=filters)
            self.manager._list.assert_called_once_with(
                expected_path,
                share_networks.RESOURCES_NAME)

    def test_update(self):
        share_nw = 'fake share nw'
        values = {'neutron_net_id': 'new net id',
                  'neutron_subnet_id': 'new subnet id',
                  'name': 'new name',
                  'description': 'new whatever'}
        body_expected = {share_networks.RESOURCE_NAME: values}

        with mock.patch.object(self.manager, '_update', fakes.fake_update):
            result = self.manager.update(share_nw, **values)
            self.assertEqual(result['url'],
                             share_networks.RESOURCE_PATH % share_nw)
            self.assertEqual(result['resp_key'], share_networks.RESOURCE_NAME)
            self.assertEqual(result['body'], body_expected)

    def test_update_with_exception(self):
        share_nw = 'fake share nw'
        self.assertRaises(exceptions.CommandError,
                          self.manager.update,
                          share_nw)

    def test_add_security_service(self):
        security_service = 'fake security service'
        share_nw = 'fake share nw'
        expected_path = (share_networks.RESOURCE_PATH + '/action') % share_nw
        expected_body = {'add_security_service': {'security_service_id':
                                                  security_service}}

        with mock.patch.object(self.manager, '_create', mock.Mock()):
            self.manager.add_security_service(share_nw, security_service)

            self.manager._create.assert_called_once_with(
                expected_path,
                expected_body,
                share_networks.RESOURCE_NAME)

    def test_remove_security_service(self):
        security_service = 'fake security service'
        share_nw = 'fake share nw'
        expected_path = (share_networks.RESOURCE_PATH + '/action') % share_nw
        expected_body = {'remove_security_service': {'security_service_id':
                                                     security_service}}

        with mock.patch.object(self.manager, '_create', mock.Mock()):
            self.manager.remove_security_service(share_nw, security_service)

            self.manager._create.assert_called_once_with(
                expected_path,
                expected_body,
                share_networks.RESOURCE_NAME)

    def test_activate(self):
        share_nw = 'fake share nw'
        expected_path = (share_networks.RESOURCE_PATH + '/action') % share_nw
        expected_body = {'activate': {}}

        with mock.patch.object(self.manager, '_create', mock.Mock()):
            self.manager.activate(share_nw)

            self.manager._create.assert_called_once_with(
                expected_path,
                expected_body,
                share_networks.RESOURCE_NAME)

    def test_deactivate(self):
        share_nw = 'fake share nw'
        expected_path = (share_networks.RESOURCE_PATH + '/action') % share_nw
        expected_body = {'deactivate': {}}

        with mock.patch.object(self.manager, '_create', mock.Mock()):
            self.manager.deactivate(share_nw)

            self.manager._create.assert_called_once_with(
                expected_path,
                expected_body,
                share_networks.RESOURCE_NAME)
