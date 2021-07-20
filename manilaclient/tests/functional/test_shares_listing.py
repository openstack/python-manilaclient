# -*- coding: utf-8 -*-
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

from manilaclient.common import constants
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
    def test_shares_list_filter_by_export_location(self, role):
        self.clients[role].manila('list', params='--export_location fake')

    @ddt.data('admin', 'user')
    def test_shares_list_filter_by_inexact_name(self, role):
        self.clients[role].manila('list', params='--name~ na')

    @ddt.data('admin', 'user')
    def test_shares_list_filter_by_inexact_description(self, role):
        self.clients[role].manila('list', params='--description~ des')

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

    def test_shares_list_filter_by_host(self):
        self.clients['admin'].manila('list', params='--host fake')

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

    def setUp(self):
        super(SharesListReadWriteTest, self).setUp()
        self.private_name = data_utils.rand_name('autotest_share_name')
        self.private_description = data_utils.rand_name(
            'autotest_share_description')
        self.public_name = data_utils.rand_name('autotest_public_share_name')
        self.public_description = data_utils.rand_name(
            'autotest_public_share_description')

        self.admin_private_name = data_utils.rand_name(
            'autotest_admin_private_share_name')
        self.admin_private_description = data_utils.rand_name(
            'autotest_admin_private_share_description')

        self.soft_name = data_utils.rand_name('soft_delete_share_name')

        self.admin_private_share = self.create_share(
            name=self.admin_private_name,
            description=self.admin_private_description,
            public=False,
            client=None,
            wait_for_creation=False)

        self.private_share = self.create_share(
            name=self.private_name,
            description=self.private_description,
            public=False,
            client=self.get_user_client(),
            wait_for_creation=False)

        self.public_share = self.create_share(
            name=self.public_name,
            description=self.public_description,
            public=True,
            client=self.admin_client)

        self.wait_soft_delete_share = self.create_share(
            name=self.soft_name,
            public=False,
            client=self.get_user_client(),
            wait_for_creation=False)

        self.shares_created = (self.private_share['id'],
                               self.public_share['id'],
                               self.admin_private_share['id'],
                               self.wait_soft_delete_share['id'])

        for share_id in self.shares_created:
            self.admin_client.wait_for_resource_status(
                share_id, constants.STATUS_AVAILABLE)

        self.soft_delete_share([self.wait_soft_delete_share['id']],
                               client=self.get_user_client(),
                               microversion='2.69')

    def _list_shares(self, filters=None):
        filters = filters or dict()
        shares = self.user_client.list_shares(filters=filters)

        self.assertGreater(len(shares), 0)
        if filters:
            for share in shares:
                try:
                    share_get = self.user_client.get_share(share['ID'])
                except exceptions.NotFound:
                    # NOTE(vponomaryov): Case when some share was deleted
                    # between our 'list' and 'get' requests. Skip such case.
                    # It occurs with concurrently running tests.
                    continue
                if 'migrating' in share_get['status']:
                    # all bets are off, a fair chance share migration
                    # started between the 'list' and 'get' requests. No need
                    # to verify these shares.
                    continue
                for filter_key, expected_value in filters.items():
                    if filter_key in ('share_network', 'share-network'):
                        filter_key = 'share_network_id'
                        if share_get[filter_key] != expected_value:
                            # Possibly a mismatch because the share was
                            # migrated to a new network in the time that
                            # elapsed between the 'list' and 'get' requests.
                            # If this isn't one of the shares created in
                            # this class, don't worry about such mismatches
                            self.assertNotIn(share_get['id'],
                                             self.shares_created)
                            continue

                    if (expected_value != 'deleting' and
                            share_get[filter_key] == 'deleting'):
                        continue
                    self.assertEqual(expected_value, share_get[filter_key])

    def test_list_shares(self):
        self._list_shares()

    @ddt.data(1, 0)
    def test_list_shares_for_all_tenants(self, all_tenants):
        shares = self.admin_client.list_shares(all_tenants=all_tenants)
        self.assertLessEqual(1, len(shares))

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
        self.assertGreater(len(shares), 1)
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

    @ddt.data('ID', 'Path')
    def test_list_shares_by_export_location(self, option):
        export_locations = self.admin_client.list_share_export_locations(
            self.public_share['id'])
        shares = self.admin_client.list_shares(
            filters={'export_location': export_locations[0][option]})

        self.assertEqual(1, len(shares))
        self.assertTrue(
            any(self.public_share['id'] == s['ID'] for s in shares))
        for share in shares:
            get = self.admin_client.get_share(share['ID'])
            self.assertEqual(self.public_name, get['name'])

    @ddt.data('ID', 'Path')
    def test_list_share_instances_by_export_location(self, option):
        export_locations = self.admin_client.list_share_export_locations(
            self.public_share['id'])
        share_instances = self.admin_client.list_share_instances(
            filters={'export_location': export_locations[0][option]})

        self.assertEqual(1, len(share_instances))

        share_instance_id = share_instances[0]['ID']
        except_export_locations = (
            self.admin_client.list_share_instance_export_locations(
                share_instance_id))
        self.assertGreater(len(except_export_locations), 0)
        self.assertTrue(
            any(export_locations[0][option] == e[option] for e in
                except_export_locations))

    def test_list_share_by_export_location_with_invalid_version(self):
        self.assertRaises(
            exceptions.CommandFailed,
            self.admin_client.list_shares,
            filters={'export_location': 'fake'},
            microversion='2.34')

    def test_list_share_instance_by_export_location_invalid_version(self):
        self.assertRaises(
            exceptions.CommandFailed,
            self.admin_client.list_share_instances,
            filters={'export_location': 'fake'},
            microversion='2.34')

    @ddt.data('name', 'description')
    def test_list_shares_by_inexact_option(self, option):
        shares = self.user_client.list_shares(
            filters={option + '~': option})

        # We know we have to have atleast three shares.
        # Due to test concurrency, there can be
        # more than three shares (some created by other tests).
        self.assertGreaterEqual(len(shares), 3)
        self.assertTrue(
            any(self.private_share['id'] == s['ID'] for s in shares))

    def test_list_shares_by_inexact_unicode_option(self):
        self.create_share(
            name=u'共享名称',
            description=u'共享描述',
            client=self.user_client)
        filters = {'name~': u'名称'}
        shares = self.user_client.list_shares(filters=filters)
        self.assertGreater(len(shares), 0)

        filters = {'description~': u'描述'}
        shares = self.user_client.list_shares(filters=filters)
        self.assertGreater(len(shares), 0)

    def test_list_shares_by_description(self):
        shares = self.user_client.list_shares(
            filters={'description': self.private_description})

        self.assertEqual(1, len(shares))
        self.assertTrue(
            any(self.private_share['id'] == s['ID'] for s in shares))

    def test_list_shares_in_recycle_bin(self):
        shares = self.user_client.list_shares(is_soft_deleted=True)

        self.assertTrue(
            any(self.wait_soft_delete_share['id'] == s['ID'] for s in shares))
