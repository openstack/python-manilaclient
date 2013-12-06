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

from manilaclient.v1 import shares as shares_ext_module
from manilaclient.v1 import client
from tests.v1 import fake_clients as fakes


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

    def get_shares_detail(self, **kw):
        shares = {'shares': [{'id': 1234,
                              'name': 'sharename',
                              'attachments': [{'server_id': 111}]}]}
        return (200, {}, shares)

    def get_snapshots_1234(self, **kw):
        snapshot = {'snapshot': {'id': 1234, 'name': 'sharename'}}
        return (200, {}, snapshot)

    def get_snapshots_detail(self, **kw):
        print kw
        # print kw['share_id']
        snapshots = {'snapshots': [{
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
            _body = {'access': {}}
        elif action == 'os-deny_access':
            assert body[action].keys() == ['access_id']
        elif action == 'os-access_list':
            assert body[action] is None
        else:
            raise AssertionError("Unexpected share action: %s" % action)
        return (resp, {}, _body)

    def post_shares(self, **kwargs):
        return (202, {}, {'share': {}})

    def post_snapshots(self, **kwargs):
        return (202, {}, {'snapshot': {}})

    def delete_shares_1234(self, **kw):
        return (202, {}, None)

    def delete_snapshots_1234(self, **kwargs):
        return (202, {}, None)

    def put_shares_1234(self, **kwargs):
        share = {'share': {'id': 1234, 'name': 'sharename'}}
        return (200, {}, share)

    def put_snapshots_1234(self, **kwargs):
        snapshot = {'snapshot': {'id': 1234, 'name': 'snapshot_name'}}
        return (200, {}, snapshot)

    #
    # Set/Unset metadata
    #
    def delete_shares_1234_metadata_test_key(self, **kw):
        return (204, {}, None)

    def delete_shares_1234_metadata_key1(self, **kw):
        return (204, {}, None)

    def delete_shares_1234_metadata_key2(self, **kw):
        return (204, {}, None)

    def post_shares_1234_metadata(self, **kw):
        return (204, {}, {'metadata': {'test_key': 'test_value'}})

    def put_shares_1234_metadata(self, **kw):
        return (200, {}, {"metadata": {"key1": "val1", "key2": "val2"}})

    def get_shares_1234_metadata(self, **kw):
        return (200, {}, {"metadata": {"key1": "val1", "key2": "val2"}})
