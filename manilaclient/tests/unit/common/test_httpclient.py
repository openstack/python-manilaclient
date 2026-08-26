# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import hashlib
import re
from unittest import mock

import ddt
from keystoneauth1 import exceptions as ks_exceptions
from keystoneauth1 import session as ks_session
from oslo_serialization import jsonutils
import requests

import manilaclient
from manilaclient.common import constants
from manilaclient.common import httpclient
from manilaclient import exceptions
from manilaclient.tests.unit import utils

fake_user_agent = "fake"

fake_response = utils.TestResponse(
    {
        "status_code": 200,
        "text": '{"hi": "there"}',
    }
)
mock_request = mock.Mock(return_value=(fake_response))

bad_400_response = utils.TestResponse(
    {
        "status_code": 400,
        "text": '{"error": {"message": "n/a", "details": "Terrible!"}}',
    }
)
bad_400_request = mock.Mock(return_value=(bad_400_response))

bad_401_response = utils.TestResponse(
    {
        "status_code": 401,
        "text": '{"error": {"message": "FAILED!", "details": "DETAILS!"}}',
    }
)
bad_401_request = mock.Mock(return_value=(bad_401_response))

bad_500_response = utils.TestResponse(
    {
        "status_code": 500,
        "text": '{"error": {"message": "FAILED!", "details": "DETAILS!"}}',
    }
)
bad_500_request = mock.Mock(return_value=(bad_500_response))

retry_after_response = utils.TestResponse(
    {
        "status_code": 413,
        "text": '',
        "headers": {"retry-after": "5"},
    }
)
retry_after_mock_request = mock.Mock(return_value=retry_after_response)

retry_after_no_headers_response = utils.TestResponse(
    {
        "status_code": 413,
        "text": '',
    }
)
retry_after_no_headers_mock_request = mock.Mock(
    return_value=retry_after_no_headers_response
)

retry_after_non_supporting_response = utils.TestResponse(
    {
        "status_code": 403,
        "text": '',
        "headers": {"retry-after": "5"},
    }
)
retry_after_non_supporting_mock_request = mock.Mock(
    return_value=retry_after_non_supporting_response
)


def get_authed_client(endpoint_url="http://example.com", retries=0):
    cl = httpclient.HTTPClient(
        endpoint_url,
        "token",
        fake_user_agent,
        retries=retries,
        http_log_debug=True,
        api_version=manilaclient.API_MAX_VERSION,
    )
    return cl


@ddt.ddt
class ClientTest(utils.TestCase):
    def setUp(self):
        super().setUp()
        self.max_version = manilaclient.API_MAX_VERSION
        self.max_version_str = self.max_version.get_string()
        self.mock_object(httpclient, 'sleep')

    @ddt.data(
        "http://manila.example.com/v2/b2d18606-2673-4965-885a-4f5a8b955b9b",
        "http://manila.example.com/v1",
        "http://manila.example.com/share/v2.22/",
        "http://manila.example.com/share/v1/"
        "b2d18606-2673-4965-885a-4f5a8b955b9b",
        "http://10.10.10.10:3366/v1",
        "http://10.10.10.10:3366/v2/b2d18606-2673-4965-885a-4f5a8b955b9b",
        "http://manila.example.com:3366/v1.1/",
        "http://manila.example.com:3366/v2/"
        "b2d18606-2673-4965-885a-4f5a8b955b9b",
    )
    def test_get(self, endpoint_url):
        cl = get_authed_client(endpoint_url)

        @mock.patch.object(requests, "request", mock_request)
        @mock.patch('time.time', mock.Mock(return_value=1234))
        def test_get_call():
            resp, body = cl.get("/hi")
            headers = {
                "X-Auth-Token": "token",
                "User-Agent": fake_user_agent,
                cl.API_VERSION_HEADER: self.max_version_str,
                'Accept': 'application/json',
            }
            mock_request.assert_called_with(
                "GET",
                endpoint_url + "/hi",
                headers=headers,
                **self.TEST_REQUEST_BASE,
            )
            # Automatic JSON parsing
            self.assertEqual(body, {"hi": "there"})
            self.assertEqual(
                re.split(r'/v[0-9]+[\.0-9]*', endpoint_url)[0] + "/",
                cl.base_url,
            )

        test_get_call()

    def test_get_retry_500(self):
        cl = get_authed_client(retries=1)

        self.requests = [bad_500_request, mock_request]

        def request(*args, **kwargs):
            next_request = self.requests.pop(0)
            return next_request(*args, **kwargs)

        @mock.patch.object(requests, "request", request)
        @mock.patch('time.time', mock.Mock(return_value=1234))
        def test_get_call():
            resp, body = cl.get("/hi")

        test_get_call()
        self.assertEqual(self.requests, [])

    def test_retry_limit(self):
        cl = get_authed_client(retries=1)

        self.requests = [bad_500_request, bad_500_request, mock_request]

        def request(*args, **kwargs):
            next_request = self.requests.pop(0)
            return next_request(*args, **kwargs)

        @mock.patch.object(requests, "request", request)
        @mock.patch('time.time', mock.Mock(return_value=1234))
        def test_get_call():
            resp, body = cl.get("/hi")

        self.assertRaises(exceptions.ClientException, test_get_call)
        self.assertEqual(self.requests, [mock_request])

    def test_get_no_retry_400(self):
        cl = get_authed_client(retries=0)

        self.requests = [bad_400_request, mock_request]

        def request(*args, **kwargs):
            next_request = self.requests.pop(0)
            return next_request(*args, **kwargs)

        @mock.patch.object(requests, "request", request)
        @mock.patch('time.time', mock.Mock(return_value=1234))
        def test_get_call():
            resp, body = cl.get("/hi")

        self.assertRaises(exceptions.BadRequest, test_get_call)
        self.assertEqual(self.requests, [mock_request])

    def test_get_retry_400_socket(self):
        cl = get_authed_client(retries=1)

        self.requests = [bad_400_request, mock_request]

        def request(*args, **kwargs):
            next_request = self.requests.pop(0)
            return next_request(*args, **kwargs)

        @mock.patch.object(requests, "request", request)
        @mock.patch('time.time', mock.Mock(return_value=1234))
        def test_get_call():
            resp, body = cl.get("/hi")

        test_get_call()
        self.assertEqual(self.requests, [])

    def test_get_with_retries_none(self):
        cl = get_authed_client(retries=None)

        @mock.patch.object(requests, "request", bad_401_request)
        def test_get_call():
            resp, body = cl.get("/hi")

        self.assertRaises(exceptions.Unauthorized, test_get_call)

    @ddt.data(
        "http://manila.example.com/v1/b2d18606-2673-4965-885a-4f5a8b955b9b",
        "http://manila.example.com/v1",
        "http://manila.example.com/share/v2.1/",
        "http://manila.example.com/share/v1/"
        "b2d18606-2673-4965-885a-4f5a8b955b9b",
        "http://10.10.10.10:3366/v1.1",
        "http://10.10.10.10:3366/v2/b2d18606-2673-4965-885a-4f5a8b955b9b",
        "http://manila.example.com:3366/v2.22/",
        "http://manila.example.com:3366/v1/"
        "b2d18606-2673-4965-885a-4f5a8b955b9b",
    )
    def test_post(self, endpoint_url):
        cl = get_authed_client(endpoint_url)

        @mock.patch.object(requests, "request", mock_request)
        def test_post_call():
            cl.post("/hi", body=[1, 2, 3])
            headers = {
                "X-Auth-Token": "token",
                "Content-Type": "application/json",
                'Accept': 'application/json',
                "X-Openstack-Manila-Api-Version": self.max_version_str,
                "User-Agent": fake_user_agent,
            }
            mock_request.assert_called_with(
                "POST",
                endpoint_url + "/hi",
                headers=headers,
                data='[1, 2, 3]',
                **self.TEST_REQUEST_BASE,
            )
            self.assertEqual(
                re.split(r'/v[0-9]+[\.0-9]*', endpoint_url)[0] + "/",
                cl.base_url,
            )

        test_post_call()

    def test_log_request_redacts_token(self):
        cl = get_authed_client()
        token = "token"
        token_hash = hashlib.sha256(token.encode('utf-8')).hexdigest()

        with mock.patch.object(cl._logger, 'debug') as mock_debug:
            cl.log_request(
                'GET', 'http://example.com/hi', {'X-Auth-Token': token}, None
            )
            logged = mock_debug.call_args[0][1]
            self.assertNotIn(token_hash[:8], token[:8])
            self.assertNotIn(f'"X-Auth-Token: {token}"', logged)
            self.assertIn(f'"X-Auth-Token: {{SHA256}}{token_hash}"', logged)

    def test_safe_header_non_sensitive(self):
        value = httpclient.HTTPClient._safe_header(
            'Content-Type', 'application/json'
        )
        self.assertEqual('application/json', value)


@ddt.ddt
class SessionClientTest(utils.TestCase):
    def setUp(self):
        super().setUp()
        self.max_version = manilaclient.API_MAX_VERSION
        self.endpoint = 'http://192.0.2.10/share/v2/fake_project'

    def _fake_response(self, status_code=200, text='{"hi": "there"}'):
        resp = mock.Mock()
        resp.status_code = status_code
        resp.text = text
        resp.headers = {}
        resp.json.return_value = jsonutils.loads(text) if text else None
        return resp

    def _get_client(
        self, retries=0, http_log_debug=False, timeout=None, response=None
    ):
        # Build a SessionClient backed by a real keystoneauth Session whose
        # transport-level request() is mocked, so the real adapter code path
        # (URL handling, body->json mapping, microversion) is exercised.
        session = ks_session.Session()
        self.session_request = mock.Mock(
            return_value=response or self._fake_response()
        )
        session.request = self.session_request
        return httpclient.SessionClient(
            session=session,
            auth=mock.Mock(),
            interface='public',
            service_type='sharev2',
            api_version=self.max_version,
            user_agent=fake_user_agent,
            endpoint_override=self.endpoint,
            retries=retries,
            http_log_debug=http_log_debug,
            timeout=timeout,
        )

    def test_init_sets_default_microversion_and_headers(self):
        cl = self._get_client()
        self.assertEqual({}, cl.default_headers)
        self.assertEqual(
            self.max_version.get_string(), cl.default_microversion
        )

    def test_get_returns_parsed_body(self):
        cl = self._get_client()

        resp, body = cl.get('/shares')

        self.assertEqual({'hi': 'there'}, body)
        args, kwargs = self.session_request.call_args
        self.assertEqual('GET', args[1])
        self.assertTrue(kwargs['authenticated'])

    def test_post_maps_body_to_json(self):
        cl = self._get_client(
            response=self._fake_response(
                status_code=202, text='{"share": {"id": "x"}}'
            )
        )

        resp, body = cl.post('/shares', body={'share': {'name': 'test'}})

        self.assertEqual({'share': {'id': 'x'}}, body)
        args, kwargs = self.session_request.call_args
        self.assertEqual('POST', args[1])
        # LegacyJsonAdapter maps the legacy ``body`` kwarg onto ``json``.
        self.assertEqual({'share': {'name': 'test'}}, kwargs['json'])

    @ddt.data('put', 'delete')
    def test_put_and_delete_dispatch(self, method):
        cl = self._get_client(
            response=self._fake_response(status_code=202, text='')
        )

        getattr(cl, method)('/shares/1')

        args, kwargs = self.session_request.call_args
        self.assertEqual(method.upper(), args[1])

    def test_request_raises_manila_exception_on_error_status(self):
        cl = self._get_client(
            response=self._fake_response(
                status_code=400,
                text='{"badRequest": {"message": "nope"}}',
            )
        )

        self.assertRaises(exceptions.BadRequest, cl.get, '/shares')

    def test_default_headers_are_merged_into_requests(self):
        # Regression test: the experimental_api decorator toggles a sticky
        # header via client.default_headers; it must reach the wire.
        cl = self._get_client()
        cl.default_headers[constants.EXPERIMENTAL_HTTP_HEADER] = 'true'

        cl.get('/shares')

        args, kwargs = self.session_request.call_args
        self.assertEqual(
            'true', kwargs['headers'][constants.EXPERIMENTAL_HTTP_HEADER]
        )

    def test_per_request_headers_override_default_headers(self):
        cl = self._get_client()
        cl.default_headers['X-Test'] = 'default'

        cl.get('/shares', headers={'X-Test': 'override'})

        args, kwargs = self.session_request.call_args
        self.assertEqual('override', kwargs['headers']['X-Test'])

    @ddt.data(
        (
            'http://192.0.2.10/share/v2/fake_project',
            'http://192.0.2.10/share/',
        ),
        ('http://192.0.2.10/share/v2.22/', 'http://192.0.2.10/share/'),
        ('http://192.0.2.10:8786/v2/fake', 'http://192.0.2.10:8786/'),
        ('http://192.0.2.10/share/v1', 'http://192.0.2.10/share/'),
    )
    @ddt.unpack
    def test_get_base_url(self, endpoint, expected):
        self.assertEqual(
            expected, httpclient.SessionClient._get_base_url(endpoint)
        )

    def test_get_with_base_url_strips_version_path(self):
        cl = self._get_client()

        cl.get_with_base_url('')

        args, kwargs = self.session_request.call_args
        self.assertEqual('http://192.0.2.10/share/', args[0])
        self.assertEqual('GET', args[1])

    @mock.patch.object(httpclient, 'sleep', mock.Mock())
    def test_cs_request_retries_client_exception(self):
        cl = self._get_client(retries=1)
        ok = (mock.Mock(status_code=200), {'hi': 'there'})
        with mock.patch.object(
            cl,
            'request',
            side_effect=[exceptions.ClientException('boom'), ok],
        ) as mock_request:
            resp, body = cl.get('/shares')

        self.assertEqual({'hi': 'there'}, body)
        self.assertEqual(2, mock_request.call_count)

    @mock.patch.object(httpclient, 'sleep', mock.Mock())
    def test_cs_request_retries_connection_failure(self):
        # Regression test: transient keystoneauth connection failures are
        # not manila ClientExceptions and must still be retried.
        cl = self._get_client(retries=1)
        ok = (mock.Mock(status_code=200), {'hi': 'there'})
        with mock.patch.object(
            cl,
            'request',
            side_effect=[ks_exceptions.ConnectTimeout(), ok],
        ) as mock_request:
            resp, body = cl.get('/shares')

        self.assertEqual({'hi': 'there'}, body)
        self.assertEqual(2, mock_request.call_count)

    @mock.patch.object(httpclient, 'sleep', mock.Mock())
    def test_cs_request_raises_after_retry_limit(self):
        cl = self._get_client(retries=1)
        with mock.patch.object(
            cl,
            'request',
            side_effect=exceptions.ClientException('boom'),
        ) as mock_request:
            self.assertRaises(exceptions.ClientException, cl.get, '/shares')

        self.assertEqual(2, mock_request.call_count)

    def test_cs_request_no_retry_by_default(self):
        cl = self._get_client(retries=0)
        with mock.patch.object(
            cl,
            'request',
            side_effect=exceptions.BadRequest('boom'),
        ) as mock_request:
            self.assertRaises(exceptions.BadRequest, cl.get, '/shares')

        self.assertEqual(1, mock_request.call_count)
