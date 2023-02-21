# Copyright (c) 2022 China Telecom Digital Intelligence.
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

from tempest.lib.common.utils import data_utils

from manilaclient.tests.functional import base


class ShareTransferTests(base.BaseTestCase):
    """Check of base share transfers command"""

    def setUp(self):
        super(ShareTransferTests, self).setUp()
        self.share_type = self.create_share_type(
            name=data_utils.rand_name('test_share_type'),
            driver_handles_share_servers=False)

    def test_transfer_create_list_show_delete(self):
        """Create, list, show and delete a share transfer"""
        self.skip_if_microversion_not_supported('2.77')
        share = self.create_share(
            share_protocol='nfs',
            size=1,
            name=data_utils.rand_name('autotest_share_name'),
            client=self.user_client,
            share_type=self.share_type['ID'],
            use_wait_option=True)
        self.assertEqual("available", share['status'])
        # create share transfer
        transfer = self.create_share_transfer(share['id'],
                                              name='test_share_transfer')
        self.assertIn('auth_key', transfer)

        # list share transfers
        transfers = self.list_share_transfer()
        # We must have at least one transfer
        self.assertTrue(len(transfers) > 0)

        # show the share transfer
        transfer_show = self.get_share_transfer(transfer['id'])
        self.assertEqual(transfer_show['name'], transfer['name'])
        self.assertNotIn('auth_key', transfer_show)

        # delete share transfer
        self.delete_share_transfer(transfer['id'])
        self.user_client.wait_for_transfer_deletion(transfer['id'])
        share = self.user_client.get_share(share['id'])
        self.assertEqual("available", share['status'])
        # finally delete the share
        self.user_client.delete_share(share['id'])
        self.user_client.wait_for_share_deletion(share['id'])

    def test_transfer_accept(self):
        """Show share transfer accept"""
        self.skip_if_microversion_not_supported('2.77')
        share = self.create_share(
            share_protocol='nfs',
            size=1,
            name=data_utils.rand_name('autotest_share_name'),
            client=self.user_client,
            share_type=self.share_type['ID'],
            use_wait_option=True)
        self.assertEqual("available", share['status'])
        # create share transfer
        transfer = self.create_share_transfer(share['id'],
                                              name='test_share_transfer')
        share = self.user_client.get_share(share['id'])
        transfer_id = transfer['id']
        auth_key = transfer['auth_key']
        self.assertEqual("share", transfer['resource_type'])
        self.assertEqual('test_share_transfer', transfer['name'])
        self.assertEqual("awaiting_transfer", share['status'])

        # accept the share transfer
        self.accept_share_transfer(transfer_id, auth_key)
        # after accept complete, the transfer will be deleted.
        self.user_client.wait_for_transfer_deletion(transfer_id)
        share = self.user_client.get_share(share['id'])
        # check share status roll back to available
        self.assertEqual("available", share['status'])
        # finally delete the share
        self.user_client.delete_share(share['id'])
        self.user_client.wait_for_share_deletion(share['id'])
