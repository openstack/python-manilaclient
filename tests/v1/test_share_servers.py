# Copyright 2014 OpenStack Foundation.
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
import unittest

from manilaclient.v1 import share_servers


class FakeShareServer(object):
    _info = {
        "backend_details": {
            "fake_key1": "fake_value1",
            "fake_key2": "fake_value2",
        }
    }


class ShareServersTest(unittest.TestCase):

    def setUp(self):
        super(ShareServersTest, self).setUp()
        self.manager = share_servers.ShareServerManager(api=None)

    def test_list(self):
        with mock.patch.object(self.manager, '_list',
                               mock.Mock(return_value=None)):
            self.manager.list()
            self.manager._list.assert_called_once_with(
                share_servers.RESOURCES_PATH,
                share_servers.RESOURCES_NAME)

    def test_get(self):
        server = FakeShareServer()
        with mock.patch.object(self.manager, '_get',
                               mock.Mock(return_value=server)):
            share_server_id = 'fake_share_server_id'
            self.manager.get(share_server_id)
            self.manager._get.assert_called_once_with(
                "%s/%s" % (share_servers.RESOURCES_PATH, share_server_id),
                share_servers.RESOURCE_NAME)
            self.assertTrue("details:fake_key1" in server._info.keys())
            self.assertTrue("details:fake_key2" in server._info.keys())

    def test_details(self):
        with mock.patch.object(self.manager, '_get',
                               mock.Mock(return_value=None)):
            share_server_id = 'fake_share_server_id'
            self.manager.details(share_server_id)
            self.manager._get.assert_called_once_with(
                "%s/%s/details" % (share_servers.RESOURCES_PATH,
                                   share_server_id), 'details')
