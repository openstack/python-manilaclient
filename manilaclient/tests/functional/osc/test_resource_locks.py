# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

from tempest.lib.common.utils import data_utils
from tempest.lib import exceptions as lib_exc

from manilaclient.tests.functional.osc import base
from manilaclient.tests.functional import utils

LOCK_DETAIL_ATTRIBUTES = [
    'ID',
    'Resource Id',
    'Resource Type',
    'Resource Action',
    'Lock Context',
    'User Id',
    'Project Id',
    'Created At',
    'Updated At',
    'Lock Reason',
]

LOCK_SUMMARY_ATTRIBUTES = [
    'ID',
    'Resource Id',
    'Resource Type',
    'Resource Action',
]


@utils.skip_if_microversion_not_supported('2.82')
class ResourceLockTests(base.OSCClientTestBase):
    """Lock CLI test cases"""

    def setUp(self):
        super(ResourceLockTests, self).setUp()
        self.share_type = self.create_share_type(
            name=data_utils.rand_name('lock_tests_type'))
        self.share = self.create_share(share_type=self.share_type['id'])

    def test_lock_create_show_use_delete(self):
        """Create a deletion lock on share, view it, try it and remove."""
        lock = self.create_resource_lock(self.share['id'],
                                         lock_reason='tigers rule',
                                         client=self.user_client,
                                         add_cleanup=False)

        client_user_id = self.openstack(
            "token issue -c user_id -f value",
            client=self.user_client
        ).strip()
        client_project_id = self.openstack(
            "token issue -c project_id -f value",
            client=self.user_client
        ).strip()

        self.assertEqual(self.share['id'], lock['resource_id'])
        self.assertEqual('delete', lock['resource_action'])
        self.assertEqual(client_user_id, lock['user_id'])
        self.assertEqual(client_project_id, lock['project_id'])
        self.assertEqual('user', lock['lock_context'])
        self.assertEqual('tigers rule', lock['lock_reason'])

        lock_show = self.dict_result("share", f"lock show {lock['id']}")
        self.assertEqual(lock['id'], lock_show['ID'])
        self.assertEqual(lock['lock_context'], lock_show['Lock Context'])

        # When a deletion lock exists, share deletion must fail
        self.assertRaises(lib_exc.CommandFailed,
                          self.openstack,
                          f"share delete {self.share['id']}")

        # delete the lock, share will be deleted in cleanup stage
        self.openstack(f"share lock delete {lock['id']}",
                       client=self.user_client)

        self.assertRaises(lib_exc.CommandFailed,
                          self.openstack,
                          f"share lock show {lock['id']}")

    def test_lock_list_filter_paginate(self):
        lock_1 = self.create_resource_lock(self.share['id'],
                                           lock_reason='tigers rule',
                                           client=self.user_client)
        lock_2 = self.create_resource_lock(self.share['id'],
                                           lock_reason='tigers still rule',
                                           client=self.user_client)
        lock_3 = self.create_resource_lock(self.share['id'],
                                           lock_reason='admins rule',
                                           client=self.admin_client)

        locks = self.listing_result('share',
                                    f'lock list --resource {self.share["id"]}')

        self.assertEqual(3, len(locks))
        self.assertEqual(sorted(LOCK_SUMMARY_ATTRIBUTES),
                         sorted(locks[0].keys()))

        locks = self.listing_result('share',
                                    'lock list --lock-context user '
                                    f' --resource {self.share["id"]}')
        self.assertEqual(2, len(locks))
        self.assertNotIn(lock_3['id'], [lock['ID'] for lock in locks])

        locks = self.listing_result('share',
                                    'lock list --lock-context user'
                                    f' --resource {self.share["id"]}'
                                    ' --sort-key created_at '
                                    ' --sort-dir desc '
                                    ' --limit 1')
        self.assertEqual(1, len(locks))
        self.assertIn(lock_2['id'], [lock['ID'] for lock in locks])
        self.assertNotIn(lock_1['id'], [lock['ID'] for lock in locks])
        self.assertNotIn(lock_3['id'], [lock['ID'] for lock in locks])

    def test_lock_set_unset_lock_reason(self):
        lock = self.create_resource_lock(self.share['id'],
                                         client=self.user_client)
        self.assertEqual('None', lock['lock_reason'])

        self.openstack('share lock set '
                       f"--lock-reason 'updated reason' {lock['id']}")
        lock_show = self.dict_result("share", f"lock show {lock['id']}")
        self.assertEqual('updated reason', lock_show['Lock Reason'])

        self.openstack(f"share lock unset --lock-reason {lock['id']}")
        lock_show = self.dict_result("share", f"lock show {lock['id']}")
        self.assertEqual('None', lock_show['Lock Reason'])

    def test_lock_restrictions(self):
        """A user can't update or delete a lock created by another user."""
        lock = self.create_resource_lock(self.share['id'],
                                         client=self.admin_client,
                                         add_cleanup=False)
        self.assertEqual('admin', lock['lock_context'])

        self.assertRaises(lib_exc.CommandFailed,
                          self.openstack,
                          f"share lock set {lock['id']} "
                          f"--reason 'i cannot do this'",
                          client=self.user_client)
        self.assertRaises(lib_exc.CommandFailed,
                          self.openstack,
                          f"share lock unset {lock['id']} --reason",
                          client=self.user_client)
        self.assertRaises(lib_exc.CommandFailed,
                          self.openstack,
                          f"share lock delete {lock['id']} ",
                          client=self.user_client)

        self.openstack(f'share lock set '
                       f'--lock-reason "I can do this" '
                       f'{lock["id"]}',
                       client=self.admin_client)

        self.openstack(f'share lock delete '
                       f'{lock["id"]}',
                       client=self.admin_client)
