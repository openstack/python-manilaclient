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

from __future__ import print_function

from manilaclient.tests.unit.v1 import fake_clients as fakes
from manilaclient.v1 import client


class FakeClient(fakes.FakeClient):

    def __init__(self, *args, **kwargs):
        client.Client.__init__(self, 'username', 'password',
                               'project_id', 'auth_url',
                               input_auth_token='token',
                               extensions=kwargs.get('extensions'),
                               service_catalog_url='http://localhost:8786')
        self.client = FakeHTTPClient(**kwargs)


class FakeHTTPClient(fakes.FakeHTTPClient):

    def get_shares_1234(self, **kw):
        share = {'share': {'id': 1234, 'name': 'sharename'}}
        return (200, {}, share)

    def get_shares_1111(self, **kw):
        share = {'share': {'id': 1111, 'name': 'share1111'}}
        return (200, {}, share)

    def get_shares(self, **kw):
        endpoint = "http://127.0.0.1:8786/v1"
        share_id = '1234'
        shares = {
            'shares': [
                {
                    'id': share_id,
                    'name': 'sharename',
                    'links': [
                        {"href": endpoint + "/fake_project/shares/" + share_id,
                         "rel": "self"},
                    ],
                },
            ]
        }
        return (200, {}, shares)

    def get_shares_detail(self, **kw):
        endpoint = "http://127.0.0.1:8786/v1"
        share_id = '1234'
        shares = {
            'shares': [
                {
                    'id': share_id,
                    'name': 'sharename',
                    'status': 'fake_status',
                    'size': 1,
                    'host': 'fake_host',
                    'export_location': 'fake_export_location',
                    'snapshot_id': 'fake_snapshot_id',
                    'links': [
                        {"href": endpoint + "/fake_project/shares/" + share_id,
                         "rel": "self"},
                    ],
                },
            ]
        }
        return (200, {}, shares)

    def get_snapshots_1234(self, **kw):
        snapshot = {'snapshot': {'id': 1234, 'name': 'sharename'}}
        return (200, {}, snapshot)

    def post_snapshots_1234_action(self, body, **kw):
        _body = None
        resp = 202
        assert len(list(body)) == 1
        action = list(body)[0]
        if action == 'os-reset_status':
            assert 'status' in body['os-reset_status']
        elif action == 'os-force_delete':
            assert body[action] is None
        else:
            raise AssertionError("Unexpected action: %s" % action)
        return (resp, {}, _body)

    def get_snapshots(self, **kw):
        snapshots = {
            'snapshots': [
                {
                    'id': 1234,
                    'status': 'available',
                    'name': 'sharename',
                }
            ]
        }
        return (200, {}, snapshots)

    def get_snapshots_detail(self, **kw):
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

    def post_os_share_manage(self, body, **kw):
        _body = {'share': {'id': 'fake'}}
        resp = 202

        if not ('service_host' in body['share']
                and 'share_type' in body['share']
                and 'export_path' in body['share']
                and 'protocol' in body['share']
                and 'driver_options' in body['share']):
            resp = 422

        result = (resp, {}, _body)
        return result

    def post_os_share_unmanage_1234_unmanage(self, **kw):
        _body = None
        resp = 202
        result = (resp, {}, _body)
        return result

    def post_shares_1234_action(self, body, **kw):
        _body = None
        resp = 202
        assert len(list(body)) == 1
        action = list(body)[0]
        if action == 'os-allow_access':
            expected = ['access_to', 'access_type']
            actual = sorted(list(body[action]))
            err_msg = "expected '%s', actual is '%s'" % (expected, actual)
            assert expected == actual, err_msg
            _body = {'access': {}}
        elif action == 'os-deny_access':
            assert list(body[action]) == ['access_id']
        elif action == 'os-access_list':
            assert body[action] is None
        elif action == 'os-reset_status':
            assert 'status' in body['os-reset_status']
        elif action == 'os-force_delete':
            assert body[action] is None
        else:
            raise AssertionError("Unexpected share action: %s" % action)
        return (resp, {}, _body)

    def post_shares_1111_action(self, body, **kw):
        _body = None
        resp = 202
        assert len(list(body)) == 1
        action = list(body)[0]
        if action == 'os-allow_access':
            expected = ['access_level', 'access_to', 'access_type']
            actual = sorted(list(body[action]))
            err_msg = "expected '%s', actual is '%s'" % (expected, actual)
            assert expected == actual, err_msg
            _body = {'access': {}}
        elif action == 'os-access_list':
            assert body[action] is None
            _body = {
                'access_list': [{
                    'access_level': 'rw',
                    'state': 'active',
                    'id': '1122',
                    'access_type': 'ip',
                    'access_to': '10.0.0.7'
                }]
            }
        else:
            raise AssertionError("Unexpected share action: %s" % action)
        return (resp, {}, _body)

    def post_share_networks(self, **kwargs):
        return (202, {}, {'share_network': {}})

    def post_shares(self, **kwargs):
        return (202, {}, {'share': {}})

    def post_snapshots(self, **kwargs):
        return (202, {}, {'snapshot': {}})

    def delete_shares_1234(self, **kw):
        return (202, {}, None)

    def delete_snapshots_1234(self, **kwargs):
        return (202, {}, None)

    def delete_share_servers_1234(self, **kwargs):
        return (202, {}, None)

    def put_share_networks_1111(self, **kwargs):
        share_network = {'share_network': {'id': 1111}}
        return (200, {}, share_network)

    def put_shares_1234(self, **kwargs):
        share = {'share': {'id': 1234, 'name': 'sharename'}}
        return (200, {}, share)

    def put_snapshots_1234(self, **kwargs):
        snapshot = {'snapshot': {'id': 1234, 'name': 'snapshot_name'}}
        return (200, {}, snapshot)

    def get_share_networks_1111(self, **kw):
        share_nw = {'share_network': {'id': 1111, 'name': 'fake_share_nw'}}
        return (200, {}, share_nw)

    def post_share_networks_1234_action(self, **kw):
        share_nw = {'share_network': {'id': 1111, 'name': 'fake_share_nw'}}
        return (200, {}, share_nw)

    def get_share_networks_detail(self, **kw):
        share_nw = {
            'share_networks': [
                {'id': 1234, 'name': 'fake_share_nw'},
                {'id': 4321, 'name': 'duplicated_name'},
                {'id': 4322, 'name': 'duplicated_name'},
            ]
        }
        return (200, {}, share_nw)

    def get_security_services(self, **kw):
        security_services = {
            'security_services': [
                {
                    'id': 1111,
                    'name': 'fake_security_service',
                    'type': 'fake_type',
                    'status': 'fake_status',
                },
            ],
        }
        return (200, {}, security_services)

    def get_security_services_detail(self, **kw):
        security_services = {
            'security_services': [
                {
                    'id': 1111,
                    'name': 'fake_security_service',
                    'description': 'fake_description',
                    'share_network_id': 'fake_share-network_id',
                    'user': 'fake_user',
                    'password': 'fake_password',
                    'domain': 'fake_domain',
                    'server': 'fake_server',
                    'dns_ip': 'fake_dns_ip',
                    'type': 'fake_type',
                    'status': 'fake_status',
                    'project_id': 'fake_project_id',
                    'updated_at': 'fake_updated_at',
                },
            ],
        }
        return (200, {}, security_services)

    def get_scheduler_stats_pools(self, **kw):
        pools = {
            'pools': [
                {
                    'name': 'host1@backend1#pool1',
                    'host': 'host1',
                    'backend': 'backend1',
                    'pool': 'pool1',
                },
                {
                    'name': 'host1@backend1#pool2',
                    'host': 'host1',
                    'backend': 'backend1',
                    'pool': 'pool2',
                }
            ]
        }
        return (200, {}, pools)

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

    def get_types_default(self, **kw):
        return self.get_types_1(**kw)

    def get_types(self, **kw):
        return (200, {}, {
            'share_types': [{'id': 1,
                             'name': 'test-type-1',
                             'extra_specs': {'test': 'test'},
                             'required_extra_specs': {'test': 'test'}},
                            {'id': 2,
                             'name': 'test-type-2',
                             'extra_specs': {'test': 'test'},
                             'required_extra_specs': {'test': 'test'}}]})

    def get_types_1(self, **kw):
        return (200, {}, {'share_type': {
            'id': 1,
            'name': 'test-type-1',
            'extra_specs': {'test': 'test'},
            'required_extra_specs': {'test': 'test'}}})

    def get_types_2(self, **kw):
        return (200, {}, {'share_type': {
            'id': 2,
            'name': 'test-type-2',
            'extra_specs': {'test': 'test'},
            'required_extra_specs': {'test': 'test'}}})

    def get_types_3(self, **kw):
        return (200, {}, {
            'share_type': {
                'id': 3,
                'name': 'test-type-3',
                'extra_specs': {},
                'os-share-type-access:is_public': False
            }
        })

    def get_types_4(self, **kw):
        return (200, {}, {
            'share_type': {
                'id': 4,
                'name': 'test-type-3',
                'extra_specs': {},
                'os-share-type-access:is_public': True
            }
        })

    def post_types(self, body, **kw):
        share_type = body['share_type']
        return (202, {}, {
            'share_type': {
                'id': 3,
                'name': 'test-type-3',
                'extra_specs': share_type['extra_specs'],
                'required_extra_specs': share_type['extra_specs'],
            }
        })

    def post_types_3_action(self, body, **kw):
        _body = None
        resp = 202
        assert len(list(body)) == 1
        action = list(body)[0]
        if action == 'addProjectAccess':
            assert 'project' in body['addProjectAccess']
        elif action == 'removeProjectAccess':
            assert 'project' in body['removeProjectAccess']
        else:
            raise AssertionError('Unexpected action: %s' % action)
        return (resp, {}, _body)

    def post_types_1_extra_specs(self, body, **kw):
        assert list(body) == ['extra_specs']
        return (200, {}, {'extra_specs': {'k': 'v'}})

    def delete_types_1_extra_specs_k(self, **kw):
        return(204, {}, None)

    def delete_types_1(self, **kw):
        return (202, {}, None)

    def get_types_3_os_share_type_access(self, **kw):
        return (200, {}, {'share_type_access': [
            {'share_type_id': '11111111-1111-1111-1111-111111111111',
             'project_id': '00000000-0000-0000-0000-000000000000'}
        ]})


def fake_create(url, body, response_key):
    return {'url': url, 'body': body, 'resp_key': response_key}


def fake_update(url, body, response_key):
    return {'url': url, 'body': body, 'resp_key': response_key}
