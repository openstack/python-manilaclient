# Copyright (c) 2011 X.commerce, a business unit of eBay Inc.
# Copyright 2011 OpenStack, LLC
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

from cinderclient.v1 import shares as shares_ext_module
from cinderclient.v1 import client
from tests.v1 import fakes


class FakeClient(fakes.FakeClient):

    def __init__(self, *args, **kwargs):
        client.Client.__init__(self, 'username', 'password',
                               'project_id', 'auth_url',
                               extensions=kwargs.get('extensions'))
        self.client = FakeHTTPClient(**kwargs)


class FakeHTTPClient(fakes.FakeHTTPClient):

    def get_shares_1234(self, **kw):
        share = {'share': {'id': 1234, 'name': 'sharename'}}
        return (200, {}, share)

    def get_shares_detail(self):
        shares = {'shares': [{'id': 1234,
                              'name': 'sharename',
                              'attachments': [{'server_id': 111}]}]}
        return (200, {}, shares)

    def get_share_snapshots_1234(self, **kw):
        snapshot = {'share-snapshot': {'id': 1234, 'name': 'sharename'}}
        return (200, {}, snapshot)

    def get_share_snapshots_detail(self):
        snapshots = {'share-snapshots': [{
            'id': 1234,
            'created_at': '2012-08-27T00:00:00.000000',
            'share_size': 1,
            'share_id': 4321,
            'status': 'available',
            'name': 'sharename',
            'display_description': 'description',
            'share_proto': 'type',
            'export_location': 'location',
        }]}
        return (200, {}, snapshots)

    def post_shares_1234_action(self, body, **kw):
        _body = None
        resp = 202
        assert len(body.keys()) == 1
        action = body.keys()[0]
        if action == 'os-allow_access':
            assert body[action].keys() == ['access_type', 'access_to']
        elif action == 'os-deny_access':
            assert body[action].keys() == ['access_id']
        elif action == 'os-access_list':
            assert body[action] is None
        else:
            raise AssertionError("Unexpected share action: %s" % action)
        return (resp, {}, _body)

    def post_shares(self, **kwargs):
        return (202, {}, {'share': {}})

    def post_share_snapshots(self, **kwargs):
        return (202, {}, {'share-snapshot': {}})

    def delete_shares_1234(self, **kw):
        return (202, {}, None)

    def delete_share_snapshots_1234(self, **kwargs):
        return (202, {}, None)
