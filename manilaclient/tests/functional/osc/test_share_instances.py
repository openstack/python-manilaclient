#   Licensed under the Apache License, Version 2.0 (the "License"); you may
#   not use this file except in compliance with the License. You may obtain
#   a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#   WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#   License for the specific language governing permissions and limitations
#   under the License.

from tempest.lib import exceptions

from manilaclient.tests.functional.osc import base


class ShareInstancesCLITest(base.OSCClientTestBase):
    def setUp(self):
        super().setUp()
        # Create a share to test with
        self.share = self.create_share()
        # Get share instances for testing
        self.share_instances = self.listing_result('share instance', 'list')
        self.share_instance = (
            self.share_instances[0] if self.share_instances else None
        )
        self.non_existent_id = '76a7dd8e-7564-41d4-a184-06dc20e13d7a'
        self.invalid_id = 'invalid-format'

    def test_share_instance_list(self):
        # Test basic listing
        instances = self.listing_result('share instance', 'list')
        self.assertTableStruct(
            instances,
            [
                'ID',
                'Share ID',
                'Host',
                'Status',
                'Availability Zone',
                'Share Network ID',
                'Share Server ID',
                'Share Type ID',
            ],
        )

    def test_share_instance_show(self):
        result = self.dict_result(
            'share instance', f'show {self.share_instance["ID"]}'
        )
        self.assertEqual(self.share_instance['ID'], result['id'])

    def test_share_instance_delete_non_existent(self):
        self.assertRaises(
            exceptions.CommandFailed,
            self.openstack,
            f'share instance delete {self.non_existent_id}',
        )

    def test_share_instance_set_non_existent(self):
        self.assertRaises(
            exceptions.CommandFailed,
            self.openstack,
            f'share instance set {self.non_existent_id}  --status available',
        )

    def test_share_instance_set_invalid_status(self):
        self.assertRaises(
            exceptions.CommandFailed,
            self.openstack,
            f'share instance set {self.invalid_id} --status available',
        )

    def test_share_instance_show_non_existent(self):
        self.assertRaises(
            exceptions.CommandFailed,
            self.openstack,
            f'share instance show {self.non_existent_id}',
        )

    def test_share_instance_show_invalid_id_format(self):
        self.assertRaises(
            exceptions.CommandFailed,
            self.openstack,
            f'share instance show {self.invalid_id}',
        )

    def test_share_instance_list_invalid_filter_share_id_format(self):
        self.assertRaises(
            exceptions.CommandFailed,
            self.openstack,
            f'share instance list --share {self.invalid_id}',
        )

    def test_share_instance_list_invalid_filter_non_existent(self):
        self.assertRaises(
            exceptions.CommandFailed,
            self.openstack,
            f'share instance list --share {self.non_existent_id}',
        )
