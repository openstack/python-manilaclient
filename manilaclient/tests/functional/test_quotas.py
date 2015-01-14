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
class ManilaClientTestQuotasReadOnly(base.BaseTestCase):

    def test_quota_class_show_by_admin(self):
        roles = self.parser.listing(
            self.clients['admin'].manila('quota-class-show', params='abc'))
        self.assertTableStruct(roles, ['Property', 'Value'])

    def test_quota_class_show_by_user(self):
        self.assertRaises(
            exceptions.CommandFailed,
            self.clients['user'].manila,
            'quota-class-show',
            params='abc')

    @ddt.data('admin', 'user')
    def test_quota_defaults(self, role):
        roles = self.parser.listing(
            self.clients[role].manila('quota-defaults'))
        self.assertTableStruct(roles, ['Property', 'Value'])

    @ddt.data('admin', 'user')
    def test_quota_show(self, role):
        roles = self.parser.listing(self.clients[role].manila('quota-show'))
        self.assertTableStruct(roles, ['Property', 'Value'])
