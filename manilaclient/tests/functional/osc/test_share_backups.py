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

import json

from manilaclient.tests.functional.osc import base


class ShareBackupCLITest(base.OSCClientTestBase):
    """Functional tests for share backup."""

    def test_share_backup_create(self):
        share = self.create_share()

        backup = self.create_backup(
            share_id=share['id'],
            name='test_backup_create',
            description='Description',
            backup_options={'dummy': True})

        # fetch latest after periodic callback updates status
        backup = json.loads(self.openstack(
            f'share backup show -f json {backup["id"]}'))

        self.assertEqual(share["id"], backup["share_id"])
        self.assertEqual('test_backup_create', backup["name"])
        self.assertEqual('Description', backup["description"])
        self.assertEqual('available', backup["status"])

        backups_list = self.listing_result('share backup', 'list')
        self.assertIn(backup['id'],
                      [item['ID'] for item in backups_list])

    def test_share_backup_delete(self):
        share = self.create_share()

        backup = self.create_backup(
            share_id=share['id'],
            backup_options={'dummy': True},
            add_cleanup=False)

        self.openstack(
            f'share backup delete {backup["id"]} --wait')

        self.check_object_deleted('share backup', backup["id"])

    def test_share_backup_show(self):
        share = self.create_share()

        backup = self.create_backup(
            share_id=share['id'],
            name='test_backup_show',
            description='Description',
            backup_options={'dummy': True})

        show_result = self.dict_result(
            'share backup', f'show {backup["id"]}')

        self.assertEqual(backup["id"], show_result["id"])
        self.assertEqual('test_backup_show', show_result["name"])
        self.assertEqual('Description', show_result["description"])

    def test_share_backup_set(self):
        share = self.create_share()

        backup = self.create_backup(share_id=share['id'],
                                    backup_options={'dummy': True})

        self.openstack(
            f'share backup set {backup["id"]} '
            f'--name test_backup_set --description Description')

        show_result = self.dict_result(
            'share backup ', f'show {backup["id"]}')

        self.assertEqual(backup['id'], show_result["id"])
        self.assertEqual('test_backup_set', show_result["name"])
        self.assertEqual('Description', show_result["description"])

    def test_share_backup_unset(self):
        share = self.create_share()

        backup = self.create_backup(
            share_id=share['id'],
            name='test_backup_unset',
            description='Description',
            backup_options={'dummy': True})

        self.openstack(
            f'share backup unset {backup["id"]} --name --description')

        show_result = json.loads(self.openstack(
            f'share backup show -f json {backup["id"]}'))

        self.assertEqual(backup['id'], show_result["id"])
        self.assertIsNone(show_result["name"])
        self.assertIsNone(show_result["description"])

    def test_share_backup_list(self):
        share_1 = self.create_share()
        share_2 = self.create_share()

        backup_1 = self.create_backup(share_id=share_1['id'],
                                      backup_options={'dummy': True})
        backup_2 = self.create_backup(share_id=share_2['id'],
                                      backup_options={'dummy': True})

        backups_list = self.listing_result(
            'share backup', f'list --name {backup_2["name"]} '
        )

        self.assertTableStruct(backups_list, [
            'ID',
            'Name',
            'Share ID',
            'Status'
        ])
        self.assertEqual(1, len(backups_list))
        self.assertIn(backup_2['id'],
                      [item['ID'] for item in backups_list])

        backups_list = self.listing_result(
            'share backup', f'list --share {share_1["id"]} --detail'
        )

        self.assertTableStruct(backups_list, [
            'ID',
            'Name',
            'Share ID',
            'Status',
            'Description',
            'Availability Zone',
            'Created At',
            'Updated At',
            'Size',
            'Progress',
            'Restore Progress',
            'Host',
            'Topic',
        ])
        self.assertEqual(1, len(backups_list))
        self.assertIn(backup_1['id'],
                      [item['ID'] for item in backups_list])
