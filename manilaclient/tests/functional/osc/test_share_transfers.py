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

from manilaclient.tests.functional.osc import base


class TransfersCLITest(base.OSCClientTestBase):

    def setUp(self):
        super(TransfersCLITest, self).setUp()
        self.share_type = self.create_share_type()

    def test_transfer_create_list_show_delete(self):
        share = self.create_share(share_type=self.share_type['name'],
                                  wait_for_status='available',
                                  client=self.user_client)
        # create share transfer
        self.create_share_transfer(share['id'], name='transfer_test')
        self._wait_for_object_status('share', share['id'], 'awaiting_transfer')

        # Get all transfers
        transfers = self.listing_result(
            'share', 'transfer list', client=self.user_client)
        # We must have at least one transfer
        self.assertTrue(len(transfers) > 0)
        self.assertTableStruct(transfers, [
            'ID',
            'Name',
            'Resource Type',
            'Resource Id',
        ])

        # grab the transfer we created
        transfer = [transfer for transfer in transfers
                    if transfer['Resource Id'] == share['id']]
        self.assertEqual(1, len(transfer))

        show_transfer = self.dict_result('share',
                                         f'transfer show {transfer[0]["ID"]}')
        self.assertEqual(transfer[0]['ID'], show_transfer['id'])
        expected_keys = (
            'id', 'created_at', 'name', 'resource_type', 'resource_id',
            'source_project_id', 'destination_project_id', 'accepted',
            'expires_at',
        )
        for key in expected_keys:
            self.assertIn(key, show_transfer)

        # filtering by Resource ID
        filtered_transfers = self.listing_result(
            'share',
            f'transfer list --resource-id {share["id"]}',
            client=self.user_client)
        self.assertEqual(1, len(filtered_transfers))
        self.assertEqual(show_transfer['resource_id'], share["id"])

        # finally delete transfer and share
        self.openstack(f'share transfer delete {show_transfer["id"]}')
        self._wait_for_object_status('share', share['id'], 'available')

    def test_transfer_accept(self):
        share = self.create_share(share_type=self.share_type['name'],
                                  wait_for_status='available',
                                  client=self.user_client)
        # create share transfer
        transfer = self.create_share_transfer(share['id'],
                                              name='transfer_test')
        self._wait_for_object_status('share', share['id'], 'awaiting_transfer')

        # accept share transfer
        self.openstack(
            f'share transfer accept {transfer["id"]} {transfer["auth_key"]}')
        self._wait_for_object_status('share', share['id'], 'available')
