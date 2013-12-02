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
from manilaclient.v1 import security_services
from tests.v1 import fakes


class SecurityServiceTest(unittest.TestCase):

    def setUp(self):
        super(SecurityServiceTest, self).setUp()
        self.manager = security_services.SecurityServiceManager(api=None)

    def test_create_all_fields(self):
        values = {'type': 'ldap',
                  'dns_ip': 'fake dns ip',
                  'server': 'fake.ldap.server',
                  'domain': 'fake.ldap.domain',
                  'sid': 'fake sid',
                  'password': 'fake password',
                  'name': 'fake name',
                  'description': 'fake description'}

        with mock.patch.object(self.manager, '_create', fakes.fake_create):
            result = self.manager.create(**values)

            self.assertEqual(result['url'], security_services.RESOURCES_PATH)
            self.assertEqual(result['resp_key'],
                             security_services.RESOURCE_NAME)
            self.assertTrue(security_services.RESOURCE_NAME in result['body'])
            self.assertEqual(result['body'][security_services.RESOURCE_NAME],
                             values)

    def test_create_some_fields(self):
        values = {'type': 'ldap',
                  'dns_ip': 'fake dns ip',
                  'server': 'fake.ldap.server',
                  'domain': 'fake.ldap.domain',
                  'sid': 'fake sid'}

        with mock.patch.object(self.manager, '_create', fakes.fake_create):
            result = self.manager.create(**values)

            self.assertEqual(result['url'], security_services.RESOURCES_PATH)
            self.assertEqual(result['resp_key'],
                             security_services.RESOURCE_NAME)
            self.assertTrue(security_services.RESOURCE_NAME in result['body'])
            self.assertEqual(result['body'][security_services.RESOURCE_NAME],
                             values)

    def test_delete(self):
        security_service = 'fake service'
        with mock.patch.object(self.manager, '_delete', mock.Mock()):
            self.manager.delete(security_service)
            self.manager._delete.assert_called_once_with(
                security_services.RESOURCE_PATH % security_service)

    def test_get(self):
        security_service = 'fake service'
        with mock.patch.object(self.manager, '_get', mock.Mock()):
            self.manager.get(security_service)
            self.manager._get.assert_called_once_with(
                security_services.RESOURCE_PATH % security_service,
                security_services.RESOURCE_NAME)

    def test_list_no_filters(self):
        with mock.patch.object(self.manager, '_list',
                               mock.Mock(return_value=None)):
            self.manager.list()
            self.manager._list.assert_called_once_with(
                security_services.RESOURCES_PATH,
                security_services.RESOURCES_NAME)

    def test_list_with_filters(self):
        filters = OrderedDict([('all_tenants', 1),
                               ('status', 'ERROR'),
                               ('network', 'fake_network')])
        expected_postfix = '?all_tenants=1&status=ERROR&network=fake_network'

        with mock.patch.object(self.manager, '_list',
                               mock.Mock(return_value=None)):
            self.manager.list(search_opts=filters)
            self.manager._list.assert_called_once_with(
                security_services.RESOURCES_PATH + expected_postfix,
                security_services.RESOURCES_NAME)

    def test_update(self):
        security_service = 'fake service'
        values = {'dns_ip': 'new dns ip',
                  'server': 'new.ldap.server',
                  'domain': 'new.ldap.domain',
                  'sid': 'new sid',
                  'password': 'fake password',}

        with mock.patch.object(self.manager, '_update', fakes.fake_update):
            result = self.manager.update(security_service, **values)
            self.assertEqual(
                result['url'],
                security_services.RESOURCE_PATH % security_service)
            self.assertEqual(result['resp_key'],
                             security_services.RESOURCE_NAME)
            self.assertEqual(result['body'][security_services.RESOURCE_NAME],
                             values)

    def test_update_no_fields_specified(self):
        security_service = 'fake service'
        self.assertRaises(exceptions.CommandError,
                          self.manager.update,
                          security_service)
