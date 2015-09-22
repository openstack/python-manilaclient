# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import uuid

from keystoneclient import session
import mock

from manilaclient.common import constants
from manilaclient import exceptions
from manilaclient import httpclient
from manilaclient.tests.unit import utils
from manilaclient.v1 import client


class ClientTest(utils.TestCase):
    def setUp(self):
        super(ClientTest, self).setUp()
        self.catalog = {
            'share': [
                {'region': 'TestRegion', 'publicURL': 'http://1.2.3.4'},
            ],
        }

    def test_adapter_properties(self):
        # sample of properties, there are many more
        retries = 3
        base_url = uuid.uuid4().hex

        s = session.Session()
        c = client.Client(session=s, api_version=constants.MAX_API_VERSION,
                          service_catalog_url=base_url, retries=retries,
                          input_auth_token='token')

        self.assertEqual(base_url, c.client.endpoint_url)
        self.assertEqual(retries, c.client.retries)

    def test_auth_via_token_invalid(self):
        self.assertRaises(exceptions.ClientException, client.Client,
                          api_version=constants.MAX_API_VERSION,
                          input_auth_token="token")

    def test_auth_via_token_and_session(self):
        s = session.Session()
        base_url = uuid.uuid4().hex
        c = client.Client(input_auth_token='token',
                          service_catalog_url=base_url, session=s,
                          api_version=constants.MAX_API_VERSION)

        self.assertIsNotNone(c.client)
        self.assertIsNone(c.keystone_client)

    def test_auth_via_token(self):
        base_url = uuid.uuid4().hex

        c = client.Client(input_auth_token='token',
                          service_catalog_url=base_url,
                          api_version=constants.MAX_API_VERSION)

        self.assertIsNotNone(c.client)
        self.assertIsNone(c.keystone_client)

    @mock.patch.object(httpclient, 'HTTPClient', mock.Mock())
    @mock.patch.object(client.Client, '_get_keystone_client', mock.Mock())
    def test_valid_region_name(self):
        kc = client.Client._get_keystone_client.return_value
        kc.service_catalog = mock.Mock()
        kc.service_catalog.get_endpoints = mock.Mock(return_value=self.catalog)
        c = client.Client(api_version=constants.MAX_API_VERSION,
                          region_name='TestRegion')
        self.assertTrue(client.Client._get_keystone_client.called)
        kc.service_catalog.get_endpoints.assert_called_once_with('share')
        httpclient.HTTPClient.assert_called_once_with(
            'http://1.2.3.4',
            mock.ANY,
            'python-manilaclient',
            insecure=False,
            cacert=None,
            timeout=None,
            retries=None,
            http_log_debug=False,
            api_version=constants.MAX_API_VERSION)
        self.assertIsNotNone(c.client)

    @mock.patch.object(client.Client, '_get_keystone_client', mock.Mock())
    def test_nonexistent_region_name(self):
        kc = client.Client._get_keystone_client.return_value
        kc.service_catalog = mock.Mock()
        kc.service_catalog.get_endpoints = mock.Mock(return_value=self.catalog)
        self.assertRaises(RuntimeError, client.Client,
                          api_version=constants.MAX_API_VERSION,
                          region_name='FakeRegion')
        self.assertTrue(client.Client._get_keystone_client.called)
        kc.service_catalog.get_endpoints.assert_called_once_with('share')

    @mock.patch.object(httpclient, 'HTTPClient', mock.Mock())
    @mock.patch.object(client.Client, '_get_keystone_client', mock.Mock())
    def test_regions_with_same_name(self):
        catalog = {
            'share': [
                {'region': 'FirstRegion', 'publicURL': 'http://1.2.3.4'},
                {'region': 'secondregion', 'publicURL': 'http://1.1.1.1'},
                {'region': 'SecondRegion', 'publicURL': 'http://2.2.2.2'},
            ],
        }
        kc = client.Client._get_keystone_client.return_value
        kc.service_catalog = mock.Mock()
        kc.service_catalog.get_endpoints = mock.Mock(return_value=catalog)
        c = client.Client(api_version=constants.MAX_API_VERSION,
                          region_name='SecondRegion')
        self.assertTrue(client.Client._get_keystone_client.called)
        kc.service_catalog.get_endpoints.assert_called_once_with('share')
        httpclient.HTTPClient.assert_called_once_with(
            'http://2.2.2.2',
            mock.ANY,
            'python-manilaclient',
            insecure=False,
            cacert=None,
            timeout=None,
            retries=None,
            http_log_debug=False,
            api_version=constants.MAX_API_VERSION)
        self.assertIsNotNone(c.client)
