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

from manilaclient.tests.unit import utils
from manilaclient.tests.unit.v2 import fakes
from manilaclient.v2 import share_servers


class FakeShareServer(object):
    _info = {
        "backend_details": {
            "fake_key1": "fake_value1",
            "fake_key2": "fake_value2",
        }
    }


class ShareServerTest(utils.TestCase):

    def setUp(self):
        super(ShareServerTest, self).setUp()
        self.share_server_id = 'foo'
        self.share_network = 'bar'
        info = {
            'id': self.share_server_id,
            'share_network_name': self.share_network,
        }
        self.resource_class = share_servers.ShareServer(
            manager=self, info=info)

    def test_get_repr_of_share_server(self):
        self.assertIn(
            'ShareServer: %s' % self.share_server_id,
            repr(self.resource_class),
        )

    def test_get_share_network_attr(self):
        # We did not set 'share_network' attr within instance, it is expected
        # that attr 'share_network_name' will be reused.
        self.assertEqual(self.resource_class.share_network, self.share_network)

    def test_get_nonexistent_share_network_name(self):
        resource_class = share_servers.ShareServer(manager=self, info={})
        try:
            # We expect AttributeError instead of endless loop of getattr
            resource_class.share_network_name
        except AttributeError:
            pass
        else:
            raise Exception("Expected exception 'AttributeError' "
                            "has not been raised.")


class ShareServerManagerTest(utils.TestCase):

    def setUp(self):
        super(ShareServerManagerTest, self).setUp()
        self.manager = share_servers.ShareServerManager(api=fakes.FakeClient())

    def test_list(self):
        with mock.patch.object(self.manager, '_list',
                               mock.Mock(return_value=None)):
            self.manager.list()
            self.manager._list.assert_called_once_with(
                share_servers.RESOURCES_PATH,
                share_servers.RESOURCES_NAME)

    def test_list_with_one_search_opt(self):
        host = 'fake_host'
        query_string = "?host=%s" % host
        with mock.patch.object(self.manager, '_list',
                               mock.Mock(return_value=None)):
            self.manager.list({'host': host})
            self.manager._list.assert_called_once_with(
                share_servers.RESOURCES_PATH + query_string,
                share_servers.RESOURCES_NAME,
            )

    def test_list_with_two_search_opts(self):
        host = 'fake_host'
        status = 'fake_status'
        query_string = "?host=%s&status=%s" % (host, status)
        with mock.patch.object(self.manager, '_list',
                               mock.Mock(return_value=None)):
            self.manager.list({'host': host, 'status': status})
            self.manager._list.assert_called_once_with(
                share_servers.RESOURCES_PATH + query_string,
                share_servers.RESOURCES_NAME,
            )

    def test_delete(self):
        share_server_id = 'fake_share_server_id'
        with mock.patch.object(self.manager, '_delete', mock.Mock()):
            self.manager.delete(share_server_id)
            self.manager._delete.assert_called_once_with(
                share_servers.RESOURCE_PATH % share_server_id)

    def test_get(self):
        server = FakeShareServer()
        with mock.patch.object(self.manager, '_get',
                               mock.Mock(return_value=server)):
            share_server_id = 'fake_share_server_id'
            self.manager.get(share_server_id)
            self.manager._get.assert_called_once_with(
                "%s/%s" % (share_servers.RESOURCES_PATH, share_server_id),
                share_servers.RESOURCE_NAME)
            for key in ["details:fake_key1", "details:fake_key2"]:
                self.assertIn(key, list(server._info))

    def test_details(self):
        with mock.patch.object(self.manager, '_get',
                               mock.Mock(return_value=None)):
            share_server_id = 'fake_share_server_id'
            self.manager.details(share_server_id)
            self.manager._get.assert_called_once_with(
                "%s/%s/details" % (share_servers.RESOURCES_PATH,
                                   share_server_id), 'details')
