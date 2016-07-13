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

import manilaclient
from manilaclient.tests.unit.v2 import fake_clients as fakes
from manilaclient.v2 import client


class FakeClient(fakes.FakeClient):

    def __init__(self, *args, **kwargs):
        client.Client.__init__(
            self,
            manilaclient.API_MAX_VERSION,
            'username',
            'password',
            'project_id',
            'auth_url',
            input_auth_token='token',
            extensions=kwargs.get('extensions'),
            service_catalog_url='http://localhost:8786',
            api_version=kwargs.get("api_version", manilaclient.API_MAX_VERSION)
        )
        self.client = FakeHTTPClient(**kwargs)

fake_share_instance = {
    'id': 1234,
    'share_id': 'fake',
    'status': 'available',
    'availability_zone': 'fake',
    'share_network_id': 'fake',
    'share_server_id': 'fake',
}


def get_fake_export_location():
    return {
        'uuid': 'foo_el_uuid',
        'path': '/foo/el/path',
        'share_instance_id': 'foo_share_instance_id',
        'is_admin_only': False,
        'created_at': '2015-12-17T13:14:15Z',
        'updated_at': '2015-12-17T14:15:16Z',
    }


class FakeHTTPClient(fakes.FakeHTTPClient):

    def get_(self, **kw):
        body = {
            "versions": [
                {
                    "status": "CURRENT",
                    "updated": "2015-07-30T11:33:21Z",
                    "links": [
                        {
                            "href": "http://docs.openstack.org/",
                            "type": "text/html",
                            "rel": "describedby",
                        },
                        {
                            "href": "http://localhost:8786/v2/",
                            "rel": "self",
                        }
                    ],
                    "min_version": "2.0",
                    "version": self.default_headers[
                        "X-Openstack-Manila-Api-Version"],
                    "id": "v2.0",
                }
            ]
        }
        return (200, {}, body)

    def get_os_services(self, **kw):
        services = {
            "services": [
                {"status": "enabled",
                 "binary": "manila-scheduler",
                 "zone": "foozone",
                 "state": "up",
                 "updated_at": "2015-10-09T13:54:09.000000",
                 "host": "lucky-star",
                 "id": 1},
                {"status": "enabled",
                 "binary": "manila-share",
                 "zone": "foozone",
                 "state": "up",
                 "updated_at": "2015-10-09T13:54:05.000000",
                 "host": "lucky-star",
                 "id": 2},
            ]
        }
        return (200, {}, services)

    get_services = get_os_services

    def put_os_services_enable(self, **kw):
        return (200, {}, {'host': 'foo', 'binary': 'manila-share',
                          'disabled': False})

    put_services_enable = put_os_services_enable

    def put_os_services_disable(self, **kw):
        return (200, {}, {'host': 'foo', 'binary': 'manila-share',
                          'disabled': True})

    put_services_disable = put_os_services_disable

    def get_v2(self, **kw):
        body = {
            "versions": [
                {
                    "status": "CURRENT",
                    "updated": "2015-07-30T11:33:21Z",
                    "links": [
                        {
                            "href": "http://docs.openstack.org/",
                            "type": "text/html",
                            "rel": "describedby",
                        },
                        {
                            "href": "http://localhost:8786/v2/",
                            "rel": "self",
                        }
                    ],
                    "min_version": "2.0",
                    "version": "2.5",
                    "id": "v1.0",
                }
            ]
        }
        return (200, {}, body)

    def get_shares_1234(self, **kw):
        share = {'share': {'id': 1234, 'name': 'sharename'}}
        return (200, {}, share)

    def get_shares_1111(self, **kw):
        share = {'share': {'id': 1111, 'name': 'share1111'}}
        return (200, {}, share)

    def get_shares(self, **kw):
        endpoint = "http://127.0.0.1:8786/v2"
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
        endpoint = "http://127.0.0.1:8786/v2"
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

    def get_share_servers(self, **kw):
        share_servers = {
            'share_servers': [
                {
                    'id': 1234,
                    'host': 'fake_host',
                    'status': 'fake_status',
                    'share_network': 'fake_share_nw',
                    'project_id': 'fake_project_id',
                    'updated_at': 'fake_updated_at',
                    'name': 'fake_name',
                    'share_name': 'fake_share_name',
                }
            ]
        }
        return (200, {}, share_servers)

    def post_snapshots_1234_action(self, body, **kw):
        _body = None
        resp = 202
        assert len(list(body)) == 1
        action = list(body)[0]
        if action in ('reset_status', 'os-reset_status'):
            assert 'status' in body.get(
                'reset_status', body.get('os-reset_status'))
        elif action in ('force_delete', 'os-force_delete'):
            assert body[action] is None
        elif action in ('unmanage', ):
            assert body[action] is None
        else:
            raise AssertionError("Unexpected action: %s" % action)
        return (resp, {}, _body)

    def post_snapshots_manage(self, body, **kw):
        _body = {'snapshot': {'id': 'fake'}}
        resp = 202

        if not ('share_id' in body['snapshot']
                and 'provider_location' in body['snapshot']
                and 'driver_options' in body['snapshot']):
            resp = 422

        result = (resp, {}, _body)
        return result

    def _share_instances(self):
        instances = {
            'share_instances': [
                fake_share_instance
            ]
        }
        return (200, {}, instances)

    def get_share_instances(self, **kw):
        return self._share_instances()

    def get_share_instances_1234_export_locations(self, **kw):
        export_locations = {
            'export_locations': [
                get_fake_export_location(),
            ]
        }
        return (200, {}, export_locations)

    get_shares_1234_export_locations = (
        get_share_instances_1234_export_locations)

    def get_share_instances_1234_export_locations_fake_el_uuid(self, **kw):
        export_location = {'export_location': get_fake_export_location()}
        return (200, {}, export_location)

    get_shares_1234_export_locations_fake_el_uuid = (
        get_share_instances_1234_export_locations_fake_el_uuid)

    def get_shares_fake_instances(self, **kw):
        return self._share_instances()

    def get_shares_1234_instances(self, **kw):
        return self._share_instances()

    def get_share_instances_1234(self):
        return (200, {}, {'share_instance': fake_share_instance})

    def post_share_instances_1234_action(self, body, **kw):
        _body = None
        resp = 202
        assert len(list(body)) == 1
        action = list(body)[0]
        if action in ('reset_status', 'os-reset_status'):
            assert 'status' in body.get(
                'reset_status', body.get('os-reset_status'))
        elif action == 'os-force_delete':
            assert body[action] is None
        else:
            raise AssertionError("Unexpected share action: %s" % action)
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

    post_shares_manage = post_os_share_manage

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
        if action in ('os-allow_access', 'allow_access'):
            expected = ['access_to', 'access_type']
            actual = sorted(list(body[action]))
            err_msg = "expected '%s', actual is '%s'" % (expected, actual)
            assert expected == actual, err_msg
            _body = {'access': {}}
        elif action in ('os-deny_access', 'deny_access'):
            assert list(body[action]) == ['access_id']
        elif action in ('os-access_list', 'access_list'):
            assert body[action] is None
        elif action in ('os-reset_status', 'reset_status'):
            assert 'status' in body.get(
                'reset_status', body.get('os-reset_status'))
        elif action in ('os-force_delete', 'force_delete'):
            assert body[action] is None
        elif action in ('os-extend', 'os-shrink', 'extend', 'shrink'):
            assert body[action] is not None
            assert body[action]['new_size'] is not None
        elif action in ('unmanage', ):
            assert body[action] is None
        else:
            raise AssertionError("Unexpected share action: %s" % action)
        return (resp, {}, _body)

    def post_shares_1111_action(self, body, **kw):
        _body = None
        resp = 202
        assert len(list(body)) == 1
        action = list(body)[0]
        if action in ('allow_access', 'os-allow_access'):
            expected = ['access_level', 'access_to', 'access_type']
            actual = sorted(list(body[action]))
            err_msg = "expected '%s', actual is '%s'" % (expected, actual)
            assert expected == actual, err_msg
            _body = {'access': {}}
        elif action in ('access_list', 'os-access_list'):
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

    def get_security_services_1111(self, **kw):
        ss = {'security_service': {'id': 1111, 'name': 'fake_ss'}}
        return (200, {}, ss)

    def put_security_services_1111(self, **kwargs):
        ss = {'security_service': {'id': 1111, 'name': 'fake_ss'}}
        return (200, {}, ss)

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

    def get_consistency_groups_detail(self, **kw):
        consistency_groups = {
            'consistency_groups': [
                {
                    'id': 1234,
                    'status': 'available',
                    'name': 'cgname',
                    'description': 'my cg'
                }
            ]
        }
        return (200, {}, consistency_groups)

    def delete_consistency_groups_1234(self, **kw):
        return (202, {}, None)

    def post_consistency_groups_1234_action(self, **kw):
        return (202, {}, None)

    def post_consistency_groups(self, body, **kw):
        return (202, {}, {
            'consistency_group': {
                'id': 'fake-cg-id',
                'name': 'fake_name'
            }
        })

    def get_cgsnapshots_fake_cg_id_members(self, **kw):
        members = {
            'cgsnapshot_members': [
                {
                    'id': 1234,
                    'name': 'fake name',
                    'created_at': '05050505',
                    'size': '50PB',
                    'share_protocol': 'NFS',
                    'project_id': '2221234',
                    'share_type_id': '3331234',
                },
                {
                    'id': 4321,
                    'name': 'fake name 2',
                    'created_at': '03030303',
                    'size': '50PB',
                    'share_protocol': 'NFS',
                    'project_id': '2224321',
                    'share_type_id': '3334321',
                }
            ]
        }
        return(200, {}, members)

    def get_cgsnapshots(self, **kw):
        cg_snapshots = {
            'cgsnapshots': [
                {
                    'id': 1234,
                    'status': 'available',
                    'name': 'cgsnapshotname',
                }
            ]
        }
        return (200, {}, cg_snapshots)

    def get_cgsnapshots_detail(self, **kw):
        cg_snapshots = {
            'cgsnapshots': [
                {
                    'id': 1234,
                    'status': 'available',
                    'name': 'cgsnapshotname',
                    'description': 'my cgsnapshot'
                }
            ]
        }
        return (200, {}, cg_snapshots)

    def delete_cgsnapshots_1234(self, **kw):
        return (202, {}, None)

    def post_cgsnapshots_1234_action(self, **kw):
        return (202, {}, None)

    def post_cgsnapshots(self, body, **kw):
        return (202, {}, {
            'cgsnapshot': {
                'id': 3,
                'name': 'cust_snapshot',
            }
        })

    fake_share_replica = {
        "id": "5678",
        "share_id": "1234",
        "availability_zone": "nova",
        "share_network_id": None,
        "export_locations": [],
        "share_server_id": None,
        "host": "",
        "status": "error",
        "replica_state": "error",
        "created_at": "2015-10-05T18:21:33.000000",
        "export_location": None,
    }

    def delete_share_replicas_1234(self, **kw):
        return (202, {}, None)

    def get_share_replicas_detail(self, **kw):
        replicas = {
            'share_replicas': [
                self.fake_share_replica,
            ]
        }
        return (200, {}, replicas)

    def get_share_replicas_5678(self, **kw):
        replicas = {'share_replica': self.fake_share_replica}
        return (200, {}, replicas)

    def post_share_replicas(self, **kw):
        return (202, {}, {'share_replica': self.fake_share_replica})

    def post_share_replicas_1234_action(self, body, **kw):
        _body = None
        resp = 202
        assert len(list(body)) == 1
        action = list(body)[0]
        if action in ('reset_status', 'reset_replica_state'):
            attr = action.split('reset_')[1]
            assert attr in body.get(action)
        elif action in ('force_delete', 'resync', 'promote'):
            assert body[action] is None
        else:
            raise AssertionError("Unexpected share action: %s" % action)
        return (resp, {}, _body)

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

    get_types_3_share_type_access = get_types_3_os_share_type_access


def fake_create(url, body, response_key):
    return {'url': url, 'body': body, 'resp_key': response_key}


def fake_update(url, body, response_key):
    return {'url': url, 'body': body, 'resp_key': response_key}
