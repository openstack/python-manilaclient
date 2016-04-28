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
from tempest.lib import exceptions

from manilaclient.tests.functional import base


@ddt.ddt
class ManilaClientTestShareServersReadOnly(base.BaseTestCase):

    def test_share_server_list(self):
        self.clients['admin'].manila('share-server-list')

    def test_share_server_list_with_host_param(self):
        self.clients['admin'].manila('share-server-list', params='--host host')

    def test_share_server_list_with_status_param(self):
        self.clients['admin'].manila(
            'share-server-list', params='--status status')

    def test_share_server_list_with_share_network_param(self):
        self.clients['admin'].manila(
            'share-server-list', params='--share-network share-network')

    def test_share_server_list_with_project_id_param(self):
        self.clients['admin'].manila(
            'share-server-list', params='--project-id project-id')

    def test_share_server_list_by_user(self):
        self.assertRaises(
            exceptions.CommandFailed,
            self.clients['user'].manila,
            'share-server-list')
