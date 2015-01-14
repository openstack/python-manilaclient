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
from tempest_lib import exceptions

from manilaclient.tests.functional import base


@ddt.ddt
class ManilaClientTestSharesReadOnly(base.BaseTestCase):

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
