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

from manilaclient.tests.functional import base


@ddt.ddt
class ShareTypesReadOnlyTest(base.BaseTestCase):

    @ddt.data(
        ("admin", "1.0"),
        ("admin", "2.0"),
        ("admin", "2.6"),
        ("admin", "2.7"),
        ("user", "1.0"),
        ("user", "2.0"),
        ("user", "2.6"),
        ("user", "2.7"),
    )
    @ddt.unpack
    def test_share_type_list(self, role, microversion):
        self.skip_if_microversion_not_supported(microversion)
        self.clients[role].manila("type-list", microversion=microversion)

    @ddt.data("1.0", "2.0", "2.6", "2.7")
    def test_extra_specs_list(self, microversion):
        self.skip_if_microversion_not_supported(microversion)
        self.admin_client.manila("extra-specs-list", microversion=microversion)


@ddt.ddt
class ShareTypesReadWriteTest(base.BaseTestCase):

    create_keys = (
        'ID', 'Name', 'Visibility', 'is_default', 'required_extra_specs',
        'optional_extra_specs')

    def _share_type_listed_by(self, share_type_id, by_admin=False,
                              list_all=False, microversion=None):
        client = self.admin_client if by_admin else self.user_client
        share_types = client.list_share_types(
            list_all=list_all, microversion=microversion)
        return any(share_type_id == st['ID'] for st in share_types)

    def _verify_access(self, share_type_id, is_public, microversion=None):
        if is_public:
            # Verify that it is listed with common 'type-list' operation.
            share_types = self.admin_client.list_share_types(
                list_all=False, microversion=microversion)
            self.assertTrue(
                any(share_type_id == st['ID'] for st in share_types))
        else:
            # Verify that it is not listed for user
            self.assertFalse(self._share_type_listed_by(
                share_type_id=share_type_id, by_admin=False, list_all=True,
                microversion=microversion))

            # Verify it is listed for admin
            self.assertTrue(self._share_type_listed_by(
                share_type_id=share_type_id, by_admin=True, list_all=True,
                microversion=microversion))

            # Verify it is not listed by default
            self.assertFalse(self._share_type_listed_by(
                share_type_id=share_type_id, by_admin=True, list_all=False,
                microversion=microversion))

    @ddt.data(
        (True, False),
        (True, True),
        (False, True),
        (False, False),
        (False, True, False, "2.6"),
        (False, False, True, "2.7"),
    )
    @ddt.unpack
    def test_create_delete_share_type(self, is_public, dhss,
                                      snapshot_support=True,
                                      microversion=None):
        if microversion:
            self.skip_if_microversion_not_supported(microversion)

        share_type_name = data_utils.rand_name('manilaclient_functional_test')
        dhss_expected = 'driver_handles_share_servers : %s' % dhss
        snapshot_support_expected = 'snapshot_support : %s' % snapshot_support

        # Create share type
        share_type = self.create_share_type(
            name=share_type_name,
            driver_handles_share_servers=dhss,
            snapshot_support=snapshot_support,
            is_public=is_public,
            microversion=microversion,
        )

        st_id = share_type['ID']

        # Verify response body
        for key in self.create_keys:
            self.assertIn(key, share_type)
        self.assertEqual(share_type_name, share_type['Name'])
        self.assertEqual(dhss_expected, share_type['required_extra_specs'])
        self.assertEqual(
            snapshot_support_expected, share_type['optional_extra_specs'])
        self.assertEqual('public' if is_public else 'private',
                         share_type['Visibility'].lower())
        self.assertEqual('-', share_type['is_default'])

        # Verify its access
        self._verify_access(
            share_type_id=st_id, is_public=is_public,
            microversion=microversion)

        # Delete share type
        self.admin_client.delete_share_type(st_id, microversion=microversion)

        # Wait for share type deletion
        self.admin_client.wait_for_share_type_deletion(
            st_id, microversion=microversion)

        # Verify that it is not listed with common 'type-list' operation.
        share_types = self.admin_client.list_share_types(
            list_all=False, microversion=microversion)
        self.assertFalse(
            any(st_id == st['ID'] for st in share_types))

    @ddt.data("2.6", "2.7")
    def test_add_remove_access_to_private_share_type(self, microversion):
        self.skip_if_microversion_not_supported(microversion)

        share_type_name = data_utils.rand_name('manilaclient_functional_test')
        is_public = False

        # Create share type
        share_type = self.create_share_type(
            name=share_type_name,
            driver_handles_share_servers='False',
            is_public=is_public,
            microversion=microversion,
        )

        st_id = share_type['ID']
        user_project_id = self.admin_client.get_project_id(
            self.user_client.tenant_name)

        self._verify_access(
            share_type_id=st_id,
            is_public=is_public,
            microversion=microversion,
        )

        # Project ID is in access list - false
        st_access_list = self.admin_client.list_share_type_access(
            st_id, microversion=microversion)
        self.assertNotIn(user_project_id, st_access_list)

        # Add access for project of user
        self.admin_client.add_share_type_access(
            st_id, user_project_id, microversion=microversion)

        # Verify it is listed for user as well as for admin
        self.assertTrue(self._share_type_listed_by(
            share_type_id=st_id, by_admin=False, list_all=True))
        self.assertTrue(self._share_type_listed_by(
            share_type_id=st_id, by_admin=True, list_all=True))

        # Project ID is in access list - true
        st_access_list = self.admin_client.list_share_type_access(
            st_id, microversion=microversion)
        self.assertIn(user_project_id, st_access_list)

        # Remove access
        self.admin_client.remove_share_type_access(
            st_id, user_project_id, microversion=microversion)

        self._verify_access(
            share_type_id=st_id,
            is_public=is_public,
            microversion=microversion,
        )

        # Project ID is in access list - false
        st_access_list = self.admin_client.list_share_type_access(
            st_id, microversion=microversion)
        self.assertNotIn(user_project_id, st_access_list)

    @ddt.data("2.6", "2.7")
    def test_list_share_type(self, microversion):
        share_type_name = data_utils.rand_name('manilaclient_functional_test')

        # Create share type
        self.create_share_type(
            name=share_type_name,
            driver_handles_share_servers='False')
        share_types = self.admin_client.list_share_types(
            list_all=True,
            microversion=microversion
        )
        self.assertTrue(any(s['ID'] is not None for s in share_types))
        self.assertTrue(any(s['Name'] is not None for s in share_types))
        self.assertTrue(any(s['visibility'] is not None for s in share_types))

    @ddt.data("2.6", "2.7")
    def test_list_share_type_select_column(self, microversion):
        share_type_name = data_utils.rand_name('manilaclient_functional_test')

        # Create share type
        self.create_share_type(
            name=share_type_name,
            driver_handles_share_servers='False')
        share_types = self.admin_client.list_share_types(
            list_all=True,
            columns="id,name",
            microversion=microversion
        )
        self.assertTrue(any(s['id'] is not None for s in share_types))
        self.assertTrue(any(s['name'] is not None for s in share_types))
        self.assertTrue(all('visibility' not in s for s in share_types))
        self.assertTrue(all('Visibility' not in s for s in share_types))


@ddt.ddt
class ShareTypeExtraSpecsReadWriteTest(base.BaseTestCase):

    @ddt.data(
        (True, False),
        (True, True),
        (False, True),
        (False, False),
        (False, False, "2.6"),
        (False, False, "2.7"),
    )
    @ddt.unpack
    def test_share_type_extra_specs_life_cycle(self, is_public, dhss,
                                               microversion=None):
        if microversion:
            self.skip_if_microversion_not_supported(microversion)

        # Create share type
        st = self.create_share_type(
            driver_handles_share_servers=dhss, is_public=is_public,
            microversion=microversion)

        # Add extra specs to share type
        st_extra_specs = dict(foo_key='foo_value', bar_key='bar_value')
        self.admin_client.set_share_type_extra_specs(
            st['ID'], st_extra_specs, microversion=microversion)

        # View list of extra specs
        extra_specs = self.admin_client.list_share_type_extra_specs(
            st['ID'], microversion=microversion)
        for k, v in st_extra_specs.items():
            self.assertIn('%s : %s' % (k, v), extra_specs)

        # Remove one extra spec
        self.admin_client.unset_share_type_extra_specs(
            st['ID'], ('foo_key', ), microversion=microversion)

        # Verify that removed extra spec is absent
        extra_specs = self.admin_client.list_share_type_extra_specs(
            st['ID'], microversion=microversion)
        self.assertNotIn('foo_key : foo_value', extra_specs)
        self.assertIn('bar_key : bar_value', extra_specs)
        self.assertIn('driver_handles_share_servers : %s' % dhss, extra_specs)
