# Copyright 2015 Mirantis Inc.
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

import ddt
from tempest.lib.common.utils import data_utils
from tempest.lib import exceptions
import testtools

from manilaclient import config
from manilaclient.tests.functional import base

CONF = config.CONF


@ddt.ddt
class SharesListReadOnlyTest(base.BaseTestCase):

    @ddt.data('admin', 'user')
    def test_shares_list(self, role):
        self.clients[role].manila('list')

    @ddt.data('admin', 'user')
    def test_list_with_debug_flag(self, role):
        self.clients[role].manila('list', flags='--debug')

    @ddt.data('admin', 'user')
    def test_shares_list_all_tenants(self, role):
        self.clients[role].manila('list', params='--all-tenants')

    @ddt.data('admin', 'user')
    def test_shares_list_filter_by_name(self, role):
        self.clients[role].manila('list', params='--name name')

    @ddt.data('admin', 'user')
    def test_shares_list_filter_by_status(self, role):
        self.clients[role].manila('list', params='--status status')

    def test_shares_list_filter_by_share_server_as_admin(self):
        self.clients['admin'].manila('list', params='--share-server fake')

    def test_shares_list_filter_by_share_server_as_user(self):
        self.assertRaises(
            exceptions.CommandFailed,
            self.clients['user'].manila,
            'list',
            params='--share-server fake')

    @ddt.data('admin', 'user')
    def test_shares_list_filter_by_project_id(self, role):
        self.clients[role].manila('list', params='--project-id fake')

    @ddt.data('admin', 'user')
    def test_shares_list_filter_by_host(self, role):
        self.clients[role].manila('list', params='--host fake')

    @ddt.data('admin', 'user')
    def test_shares_list_with_limit_and_offset(self, role):
        self.clients[role].manila('list', params='--limit 1 --offset 1')

    @ddt.data(
        {'role': 'admin', 'direction': 'asc'},
        {'role': 'admin', 'direction': 'desc'},
        {'role': 'user', 'direction': 'asc'},
        {'role': 'user', 'direction': 'desc'})
    @ddt.unpack
    def test_shares_list_with_sorting(self, role, direction):
        self.clients[role].manila(
            'list', params='--sort-key host --sort-dir ' + direction)

    @ddt.data('admin', 'user')
    def test_snapshot_list(self, role):
        self.clients[role].manila('snapshot-list')

    @ddt.data('admin', 'user')
    def test_snapshot_list_all_tenants(self, role):
        self.clients[role].manila('snapshot-list', params='--all-tenants')

    @ddt.data('admin', 'user')
    def test_snapshot_list_filter_by_name(self, role):
        self.clients[role].manila('snapshot-list', params='--name name')

    @ddt.data('admin', 'user')
    def test_snapshot_list_filter_by_status(self, role):
        self.clients[role].manila('snapshot-list', params='--status status')


@ddt.ddt
class SharesListReadWriteTest(base.BaseTestCase):

    @classmethod
    def setUpClass(cls):
        super(SharesListReadWriteTest, cls).setUpClass()
        cls.private_name = data_utils.rand_name('autotest_share_name')
        cls.private_description = data_utils.rand_name(
            'autotest_share_description')
        cls.public_name = data_utils.rand_name('autotest_public_share_name')
        cls.public_description = data_utils.rand_name(
            'autotest_public_share_description')

        cls.admin_private_name = data_utils.rand_name(
            'autotest_admin_private_share_name')
        cls.admin_private_description = data_utils.rand_name(
            'autotest_admin_private_share_description')

        cls.admin_private_share = cls.create_share(
            name=cls.admin_private_name,
            description=cls.admin_private_description,
            public=False,
            cleanup_in_class=True,
            client=None,
            wait_for_creation=False)

        cls.private_share = cls.create_share(
            name=cls.private_name,
            description=cls.private_description,
            public=False,
            cleanup_in_class=True,
            client=cls.get_user_client(),
            wait_for_creation=False)

        cls.public_share = cls.create_share(
            name=cls.public_name,
            description=cls.public_description,
            public=True,
            client=cls.get_user_client(),
            cleanup_in_class=True)

        for share_id in (cls.private_share['id'], cls.public_share['id'],
                         cls.admin_private_share['id']):
            cls.get_admin_client().wait_for_share_status(share_id, 'available')

    def _list_shares(self, filters=None):
        filters = filters or dict()
        shares = self.user_client.list_shares(filters=filters)

        self.assertTrue(len(shares) > 1)
        for s_id in (self.private_share['id'], self.public_share['id']):
            self.assertTrue(any(s_id == s['ID'] for s in shares))
        if filters:
            for share in shares:
                try:
                    get = self.user_client.get_share(share['ID'])
                except exceptions.NotFound:
                    # NOTE(vponomaryov): Case when some share was deleted
                    # between our 'list' and 'get' requests. Skip such case.
                    # It occurs with concurrently running tests.
                    continue
                for k, v in filters.items():
                    if k in ('share_network', 'share-network'):
                        k = 'share_network_id'
                    if v != 'deleting' and get[k] == 'deleting':
                        continue
                    self.assertEqual(v, get[k])

    def test_list_shares(self):
        self._list_shares()

    @ddt.data(1, 0)
    def test_list_shares_for_all_tenants(self, all_tenants):
        shares = self.admin_client.list_shares(all_tenants=all_tenants)
        self.assertTrue(len(shares) >= 1)

        if all_tenants:
            self.assertTrue(all('Project ID' in s for s in shares))
            for s_id in (self.private_share['id'], self.public_share['id'],
                         self.admin_private_share['id']):
                self.assertTrue(any(s_id == s['ID'] for s in shares))
        else:
            self.assertTrue(all('Project ID' not in s for s in shares))
            self.assertTrue(any(self.admin_private_share['id'] == s['ID']
                                for s in shares))
            if self.private_share['project_id'] != (
                    self.admin_private_share['project_id']):
                for s_id in (
                        self.private_share['id'], self.public_share['id']):
                    self.assertFalse(any(s_id == s['ID'] for s in shares))

    @ddt.data(True, False)
    def test_list_shares_with_public(self, public):
        shares = self.user_client.list_shares(is_public=public)
        self.assertTrue(len(shares) > 1)
        if public:
            self.assertTrue(all('Project ID' in s for s in shares))
        else:
            self.assertTrue(all('Project ID' not in s for s in shares))

    def test_list_shares_by_name(self):
        shares = self.user_client.list_shares(
            filters={'name': self.private_name})

        self.assertEqual(1, len(shares))
        self.assertTrue(
            any(self.private_share['id'] == s['ID'] for s in shares))
        for share in shares:
            get = self.user_client.get_share(share['ID'])
            self.assertEqual(self.private_name, get['name'])

    def test_list_shares_by_share_type(self):
        share_type_id = self.user_client.get_share_type(
            self.private_share['share_type'])['ID']
        # NOTE(vponomaryov): this is API 2.6+ specific
        self._list_shares({'share_type': share_type_id})

    def test_list_shares_by_status(self):
        self._list_shares({'status': 'available'})

    def test_list_shares_by_project_id(self):
        project_id = self.user_client.get_project_id(
            self.user_client.tenant_name)
        self._list_shares({'project_id': project_id})

    @testtools.skipUnless(
        CONF.share_network, "Usage of Share networks is disabled")
    def test_list_shares_by_share_network(self):
        share_network_id = self.user_client.get_share_network(
            CONF.share_network)['id']
        self._list_shares({'share_network': share_network_id})

    def test_list_shares_by_host(self):
        get = self.user_client.get_share(self.private_share['id'])
        self._list_shares({'host': get['host']})

    @ddt.data(
        {'limit': 1},
        {'limit': 2},
        {'limit': 1, 'offset': 1},
        {'limit': 2, 'offset': 0},
    )
    def test_list_shares_with_limit(self, filters):
        shares = self.user_client.list_shares(filters=filters)
        self.assertEqual(filters['limit'], len(shares))

    def test_list_share_select_column(self):
        shares = self.user_client.list_shares(columns="Name,Size")
        self.assertTrue(any(s['Name'] is not None for s in shares))
        self.assertTrue(any(s['Size'] is not None for s in shares))
        self.assertTrue(all('Description' not in s for s in shares))
