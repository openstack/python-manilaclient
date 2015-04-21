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
from oslo_utils import strutils
import six
from tempest_lib.common.utils import data_utils

from manilaclient.tests.functional import base


@ddt.ddt
class ShareTypesReadOnlyTest(base.BaseTestCase):

    @ddt.data('admin', 'user')
    def test_share_type_list(self, role):
        self.clients[role].manila('type-list')

    def test_extra_specs_list(self):
        self.admin_client.manila('extra-specs-list')


@ddt.ddt
class ShareTypesReadWriteTest(base.BaseTestCase):

    @ddt.data('false', 'False', '0', 'True', 'true', '1')
    def test_create_delete_public_share_type(self, dhss):
        share_type_name = data_utils.rand_name('manilaclient_functional_test')
        dhss_expected = 'driver_handles_share_servers : %s' % six.text_type(
            strutils.bool_from_string(dhss))

        # Create share type
        share_type = self.create_share_type(
            name=share_type_name,
            driver_handles_share_servers=dhss,
            is_public=True)

        # Verify response body
        keys = (
            'ID', 'Name', 'Visibility', 'is_default', 'required_extra_specs')
        for key in keys:
            self.assertIn(key, share_type)
        self.assertEqual(share_type_name, share_type['Name'])
        self.assertEqual(dhss_expected, share_type['required_extra_specs'])
        self.assertEqual('public', share_type['Visibility'].lower())
        self.assertEqual('-', share_type['is_default'])

        # Verify that it is listed with common 'type-list' operation.
        share_types = self.admin_client.list_share_types(list_all=False)
        self.assertTrue(
            any(share_type['ID'] == st['ID'] for st in share_types))

        # Delete share type
        self.admin_client.delete_share_type(share_type['ID'])

        # Wait for share type deletion
        self.admin_client.wait_for_share_type_deletion(share_type['ID'])

        # Verify that it is not listed with common 'type-list' operation.
        share_types = self.admin_client.list_share_types(list_all=False)
        self.assertFalse(
            any(share_type['ID'] == st['ID'] for st in share_types))
