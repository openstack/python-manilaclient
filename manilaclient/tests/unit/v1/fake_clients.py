# Copyright 2013 OpenStack, LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from six.moves.urllib import parse

from manilaclient import httpclient
from manilaclient.tests.unit import fakes
from manilaclient.tests.unit import utils
from manilaclient.v1 import client


class FakeClient(fakes.FakeClient, client.Client):

    def __init__(self, *args, **kwargs):
        client.Client.__init__(self, 'username', 'password',
                               'project_id', 'auth_url',
                               extensions=kwargs.get('extensions'))
        self.client = FakeHTTPClient(**kwargs)


class FakeHTTPClient(httpclient.HTTPClient):

    def __init__(self, **kwargs):
        self.username = 'username'
        self.password = 'password'
        self.auth_url = 'auth_url'
        self.callstack = []

    def _cs_request(self, url, method, **kwargs):
        # Check that certain things are called correctly
        if method in ['GET', 'DELETE']:
            assert 'body' not in kwargs
        elif method == 'PUT':
            assert 'body' in kwargs

        # Call the method
        args = parse.parse_qsl(parse.urlparse(url)[4])
        kwargs.update(args)
        munged_url = url.rsplit('?', 1)[0]
        munged_url = munged_url.strip('/').replace('/', '_').replace('.', '_')
        munged_url = munged_url.replace('-', '_')

        callback = "%s_%s" % (method.lower(), munged_url)

        if not hasattr(self, callback):
            raise AssertionError('Called unknown API method: %s %s, '
                                 'expected fakes method name: %s' %
                                 (method, url, callback))

        # Note the call
        self.callstack.append((method, url, kwargs.get('body', None)))
        status, headers, body = getattr(self, callback)(**kwargs)
        r = utils.TestResponse({
            "status_code": status,
            "text": body,
            "headers": headers,
        })
        return r, body

        if hasattr(status, 'items'):
            return utils.TestResponse(status), body
        else:
            return utils.TestResponse({"status": status}), body

    #
    # Quotas
    #

    def get_os_quota_sets_test(self, **kw):
        quota_set = {
            'quota_set': {
                'tenant_id': 'test',
                'metadata_items': [],
                'shares': 1,
                'snapshots': 1,
                'gigabytes': 1,
                'snapshot_gigabytes': 1,
                'share_networks': 1,
            }
        }
        return (200, {}, quota_set)

    def get_os_quota_sets_test_defaults(self):
        quota_set = {
            'quota_set': {
                'tenant_id': 'test',
                'metadata_items': [],
                'shares': 1,
                'snapshots': 1,
                'gigabytes': 1,
                'snapshot_gigabytes': 1,
                'share_networks': 1,
            }
        }
        return (200, {}, quota_set)

    def put_os_quota_sets_test(self, body, **kw):
        assert list(body) == ['quota_set']
        fakes.assert_has_keys(body['quota_set'],
                              required=['tenant_id'])
        quota_set = {
            'quota_set': {
                'tenant_id': 'test',
                'metadata_items': [],
                'shares': 2,
                'snapshots': 2,
                'gigabytes': 1,
                'snapshot_gigabytes': 1,
                'share_networks': 1,
            }
        }
        return (200, {}, quota_set)

    #
    # Quota Classes
    #

    def get_os_quota_class_sets_test(self, **kw):
        quota_class_set = {
            'quota_class_set': {
                'class_name': 'test',
                'metadata_items': [],
                'shares': 1,
                'snapshots': 1,
                'gigabytes': 1,
                'snapshot_gigabytes': 1,
                'share_networks': 1,
            }
        }
        return (200, {}, quota_class_set)

    def put_os_quota_class_sets_test(self, body, **kw):
        assert list(body) == ['quota_class_set']
        fakes.assert_has_keys(body['quota_class_set'],
                              required=['class_name'])
        quota_class_set = {
            'quota_class_set': {
                'class_name': 'test',
                'metadata_items': [],
                'shares': 2,
                'snapshots': 2,
                'gigabytes': 1,
                'snapshot_gigabytes': 1,
                'share_networks': 1,
            }
        }
        return (200, {}, quota_class_set)

    def delete_os_quota_sets_test(self, **kw):
        return (202, {}, {})
    #
    # List all extensions
    #

    def get_extensions(self, **kw):
        exts = [
            {
                "alias": "FAKE-1",
                "description": "Fake extension number 1",
                "links": [],
                "name": "Fake1",
                "namespace": ("http://docs.openstack.org/"
                              "/ext/fake1/api/v1.1"),
                "updated": "2011-06-09T00:00:00+00:00"
            },
            {
                "alias": "FAKE-2",
                "description": "Fake extension number 2",
                "links": [],
                "name": "Fake2",
                "namespace": ("http://docs.openstack.org/"
                              "/ext/fake1/api/v1.1"),
                "updated": "2011-06-09T00:00:00+00:00"
            },
        ]
        return (200, {}, {"extensions": exts, })
