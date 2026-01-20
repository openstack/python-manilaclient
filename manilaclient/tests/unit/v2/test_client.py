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

from unittest import mock

import ddt
from oslo_utils import uuidutils

import manilaclient
from manilaclient import exceptions
from manilaclient.tests.unit import utils
from manilaclient.v2 import client


@ddt.ddt
class ClientTest(utils.TestCase):
    def setUp(self):
        super(self.__class__, self).setUp()
        self.catalog = {
            'share': [
                {'region': 'TestRegion', 'publicURL': 'http://1.2.3.4'},
            ],
        }

    def test_adapter_properties(self):
        # sample of properties, there are many more
        retries = 3
        base_url = uuidutils.generate_uuid(dashed=False)

        s = client.session.Session()
        c = client.Client(
            session=s,
            api_version=manilaclient.API_MAX_VERSION,
            service_catalog_url=base_url,
            retries=retries,
            input_auth_token='token',
        )

        self.assertEqual(base_url, c.client.endpoint_url)
        self.assertEqual(retries, c.client.retries)

    def test_auth_via_token_invalid(self):
        self.assertRaises(
            exceptions.ClientException,
            client.Client,
            api_version=manilaclient.API_MAX_VERSION,
            input_auth_token="token",
        )

    def test_auth_via_token_and_session(self):
        s = client.session.Session()
        base_url = uuidutils.generate_uuid(dashed=False)

        c = client.Client(
            input_auth_token='token',
            service_catalog_url=base_url,
            session=s,
            api_version=manilaclient.API_MAX_VERSION,
        )

        self.assertIsNotNone(c.client)
        self.assertIsNone(c.keystone_client)

    def test_auth_via_token(self):
        base_url = uuidutils.generate_uuid(dashed=False)

        c = client.Client(
            input_auth_token='token',
            service_catalog_url=base_url,
            api_version=manilaclient.API_MAX_VERSION,
        )

        self.assertIsNotNone(c.client)
        self.assertIsNone(c.keystone_client)

    @mock.patch.object(client.Client, '_get_keystone_auth_and_session')
    def test_valid_region_name_v1(self, mock_get_auth):
        self.mock_object(client.httpclient, 'HTTPClient')
        self.mock_object(client.adapter, 'LegacyJsonAdapter')

        # Mock the auth and session returned by _get_keystone_auth_and_session
        mock_auth = mock.Mock()
        mock_session = mock.Mock()
        mock_get_auth.return_value = (mock_auth, mock_session)

        # Mock the adapter to return token and endpoint
        mocked_adapter = client.adapter.LegacyJsonAdapter.return_value
        mocked_adapter.session.get_token.return_value = 'fake_token'
        mocked_adapter.session.get_endpoint.return_value = 'http://1.2.3.4'
        mocked_adapter.auth = mock_auth

        c = client.Client(
            api_version=manilaclient.API_DEPRECATED_VERSION,
            service_type="share",
            region_name='TestRegion',
        )

        self.assertTrue(mock_get_auth.called)
        client.httpclient.HTTPClient.assert_called_with(
            'http://1.2.3.4',
            'fake_token',
            'python-manilaclient',
            insecure=False,
            cacert=None,
            cert=None,
            timeout=None,
            retries=None,
            http_log_debug=False,
            api_version=manilaclient.API_DEPRECATED_VERSION,
        )
        self.assertIsNotNone(c.client)

    @mock.patch.object(client.Client, '_get_keystone_auth_and_session')
    def test_nonexistent_region_name(self, mock_get_auth):
        self.mock_object(client.adapter, 'LegacyJsonAdapter')

        # Mock the auth and session returned by _get_keystone_auth_and_session
        mock_auth = mock.Mock()
        mock_session = mock.Mock()
        mock_get_auth.return_value = (mock_auth, mock_session)

        # Mock the adapter to return token but no endpoint (None)
        mocked_adapter = client.adapter.LegacyJsonAdapter.return_value
        mocked_adapter.session.get_token.return_value = 'fake_token'
        mocked_adapter.session.get_endpoint.return_value = None
        mocked_adapter.auth = mock_auth

        self.assertRaises(
            RuntimeError,
            client.Client,
            api_version=manilaclient.API_MAX_VERSION,
            region_name='FakeRegion',
        )
        self.assertTrue(mock_get_auth.called)
        mocked_adapter.session.get_endpoint.assert_called_with(
            mock_auth,
            interface='publicURL',
            service_type='sharev2',
            region_name='FakeRegion',
        )

    @mock.patch.object(client.Client, '_get_keystone_auth_and_session')
    def test_regions_with_same_name(self, mock_get_auth):
        self.mock_object(client.httpclient, 'HTTPClient')
        self.mock_object(client.adapter, 'LegacyJsonAdapter')

        # Mock the auth and session returned by _get_keystone_auth_and_session
        mock_auth = mock.Mock()
        mock_session = mock.Mock()
        mock_get_auth.return_value = (mock_auth, mock_session)

        # Mock the adapter to return token and endpoint
        mocked_adapter = client.adapter.LegacyJsonAdapter.return_value
        mocked_adapter.session.get_token.return_value = 'fake_token'
        mocked_adapter.session.get_endpoint.return_value = 'http://2.2.2.2'
        mocked_adapter.auth = mock_auth

        c = client.Client(
            api_version=manilaclient.API_MIN_VERSION,
            service_type='sharev2',
            region_name='SecondRegion',
        )

        self.assertTrue(mock_get_auth.called)
        mocked_adapter.session.get_endpoint.assert_called_with(
            mock_auth,
            interface='publicURL',
            service_type='sharev2',
            region_name='SecondRegion',
        )
        client.httpclient.HTTPClient.assert_called_with(
            'http://2.2.2.2',
            'fake_token',
            'python-manilaclient',
            insecure=False,
            cacert=None,
            cert=None,
            timeout=None,
            retries=None,
            http_log_debug=False,
            api_version=manilaclient.API_MIN_VERSION,
        )
        self.assertIsNotNone(c.client)

    def test_client_respects_region_name(self):
        mock_session = mock.Mock()
        mock_auth = mock.Mock()
        region = 'region1'
        mock_session.get_endpoint.return_value = 'http://fake-endpoint/'
        client.Client(
            session=mock_session,
            auth=mock_auth,
            service_type='sharev2',
            endpoint_type='public',
            region_name=region,
        )
        mock_session.get_endpoint.assert_called_once_with(
            mock_auth,
            service_type='sharev2',
            interface='public',
            region_name=region,
        )

    def _get_client_args(self, **kwargs):
        client_args = {
            'auth_url': 'http://identity.example.com',
            'api_version': manilaclient.API_DEPRECATED_VERSION,
            'username': 'fake_username',
            'service_type': 'sharev2',
            'region_name': 'SecondRegion',
            'input_auth_token': None,
            'session': None,
            'service_catalog_url': None,
            'user_id': 'foo_user_id',
            'user_domain_name': 'foo_user_domain_name',
            'user_domain_id': 'foo_user_domain_id',
            'project_name': 'foo_project_name',
            'project_domain_name': 'foo_project_domain_name',
            'project_domain_id': 'foo_project_domain_id',
            'endpoint_type': 'publicUrl',
            'cert': 'foo_cert',
        }
        client_args.update(kwargs)
        return client_args

    @ddt.data(
        {
            'auth_url': 'http://identity.example.com',
            'password': 'password_backward_compat',
            'endpoint_type': 'publicURL',
            'project_id': 'foo_tenant_project_id',
        },
        {
            'password': 'renamed_api_key',
            'endpoint_type': 'public',
            'tenant_id': 'foo_tenant_project_id',
        },
    )
    def test_client_init_no_session_no_auth_token(self, kwargs):
        def fake_url_for(version):
            if version == 'v3.0':
                return 'url_v3.0'
            else:
                return None

        self.mock_object(client.httpclient, 'HTTPClient')
        self.mock_object(client.identity.v3, 'Password')
        self.mock_object(client.adapter, 'LegacyJsonAdapter')
        self.mock_object(client.session.discover, 'Discover')
        self.mock_object(client.session, 'Session')
        client_args = self._get_client_args(**kwargs)
        client_args['api_version'] = manilaclient.API_MIN_VERSION
        self.auth_url = client_args['auth_url']

        client.session.discover.Discover.return_value.url_for.side_effect = (
            fake_url_for
        )

        # Mock the adapter to return token and endpoint
        mocked_adapter = client.adapter.LegacyJsonAdapter.return_value
        mocked_adapter.session.get_token.return_value = 'fake_token'
        mocked_adapter.session.get_endpoint.return_value = 'http://3.3.3.3'
        mocked_adapter.auth = client.identity.v3.Password.return_value

        client.Client(**client_args)

        client.httpclient.HTTPClient.assert_called_with(
            'http://3.3.3.3',
            'fake_token',
            'python-manilaclient',
            insecure=False,
            cacert=None,
            cert=client_args['cert'],
            timeout=None,
            retries=None,
            http_log_debug=False,
            api_version=manilaclient.API_MIN_VERSION,
        )

        # Verify identity.v3.Password was called with correct credentials
        client.identity.v3.Password.assert_called_with(
            auth_url='url_v3.0',
            username=client_args['username'],
            password=client_args.get('password'),
            user_id=client_args['user_id'],
            user_domain_name=client_args['user_domain_name'],
            user_domain_id=client_args['user_domain_id'],
            project_id=client_args.get(
                'tenant_id', client_args.get('project_id')
            ),
            project_name=client_args['project_name'],
            project_domain_name=client_args['project_domain_name'],
            project_domain_id=client_args['project_domain_id'],
        )

        # Verify LegacyJsonAdapter was created
        client.adapter.LegacyJsonAdapter.assert_called_with(
            session=mock.ANY,
            auth=mock.ANY,
            interface=client_args['endpoint_type'],
            service_type=client_args['service_type'],
            service_name=None,
            region_name=client_args['region_name'],
        )

        # Verify session.get_token() was called
        mocked_adapter.session.get_token.assert_called_with(mock.ANY)

        # Verify session.get_endpoint() was called
        mocked_adapter.session.get_endpoint.assert_called_with(
            mock.ANY,
            interface=client_args['endpoint_type'],
            service_type=client_args['service_type'],
            region_name=client_args['region_name'],
        )

    @mock.patch.object(client.session.discover, 'Discover', mock.Mock())
    @mock.patch.object(client.session, 'Session', mock.Mock())
    def test_client_init_no_session_no_auth_token_endpoint_not_found(self):
        self.mock_object(client.httpclient, 'HTTPClient')
        self.mock_object(client.identity.v3, 'Password')
        self.mock_object(client.adapter, 'LegacyJsonAdapter')
        client_args = self._get_client_args(
            auth_urli='fake_url',
            password='foo_password',
            tenant_id='foo_tenant_id',
        )
        discover = client.session.discover.Discover
        discover.return_value.url_for.return_value = None

        self.assertRaises(
            exceptions.CommandError, client.Client, **client_args
        )

        self.assertTrue(client.session.Session.called)
        self.assertTrue(client.session.discover.Discover.called)
        self.assertFalse(client.httpclient.HTTPClient.called)
        self.assertFalse(client.identity.v3.Password.called)
        self.assertFalse(client.adapter.LegacyJsonAdapter.called)
