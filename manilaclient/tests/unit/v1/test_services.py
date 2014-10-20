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

import mock

from manilaclient.tests.unit import utils
from manilaclient.v1 import services


class ServicesTest(utils.TestCase):

    def setUp(self):
        super(ServicesTest, self).setUp()
        self.manager = services.ServiceManager(api=None)

    def test_list(self):
        with mock.patch.object(self.manager, '_list',
                               mock.Mock(return_value=None)):
            self.manager.list()
            self.manager._list.assert_called_once_with(
                services.RESOURCES_PATH,
                services.RESOURCES_NAME,
            )

    def test_list_services_with_one_search_opt(self):
        host = 'fake_host'
        query_string = "?host=%s" % host
        with mock.patch.object(self.manager, '_list',
                               mock.Mock(return_value=None)):
            self.manager.list({'host': host})
            self.manager._list.assert_called_once_with(
                services.RESOURCES_PATH + query_string,
                services.RESOURCES_NAME,
            )

    def test_list_services_with_two_search_opts(self):
        host = 'fake_host'
        binary = 'fake_binary'
        query_string = "?binary=%s&host=%s" % (binary, host)
        with mock.patch.object(self.manager, '_list',
                               mock.Mock(return_value=None)):
            self.manager.list({'binary': binary, 'host': host})
            self.manager._list.assert_called_once_with(
                services.RESOURCES_PATH + query_string,
                services.RESOURCES_NAME,
            )
