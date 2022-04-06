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


class ShareSnapshotCLITest(base.OSCClientTestBase):
    """Functional tests for share snpshot."""

    def test_share_snapshot_create(self):
        share = self.create_share()

        snapshot = self.create_snapshot(
            share=share['id'],
            name='Snap',
            description='Description')

        self.assertEqual(share["id"], snapshot["share_id"])
        self.assertEqual('Snap', snapshot["name"])
        self.assertEqual('Description', snapshot["description"])
        self.assertEqual('available', snapshot["status"])

        snapshots_list = self.listing_result('share snapshot', 'list')
        self.assertIn(snapshot['id'],
                      [item['ID'] for item in snapshots_list])

    def test_share_snapshot_delete(self):
        share = self.create_share()

        snapshot_1 = self.create_snapshot(
            share=share['id'], add_cleanup=False)
        snapshot_2 = self.create_snapshot(
            share=share['id'], add_cleanup=False)

        self.openstack(
            f'share snapshot delete {snapshot_1["id"]} {snapshot_2["id"]} '
            '--wait')

        self.check_object_deleted('share snapshot', snapshot_1["id"])
        self.check_object_deleted('share snapshot', snapshot_2["id"])

        snapshot_3 = self.create_snapshot(
            share=share['id'], add_cleanup=False)

        self.openstack(
            f'share snapshot set {snapshot_3["id"]} '
            '--status creating')

        self.openstack(
            f'share snapshot delete {snapshot_3["id"]} --wait --force')

        self.check_object_deleted('share snapshot', snapshot_3["id"])

    def test_share_snapshot_show(self):
        share = self.create_share()

        snapshot = self.create_snapshot(
            share=share['id'],
            name='Snap',
            description='Description')

        show_result = self.dict_result(
            'share snapshot', f'show {snapshot["id"]}')

        self.assertEqual(snapshot["id"], show_result["id"])
        self.assertEqual('Snap', show_result["name"])
        self.assertEqual('Description', show_result["description"])

    def test_share_snapshot_set(self):
        share = self.create_share()

        snapshot = self.create_snapshot(share=share['id'])

        self.openstack(
            f'share snapshot set {snapshot["id"]} '
            f'--name Snap --description Description')

        show_result = self.dict_result(
            'share snapshot ', f'show {snapshot["id"]}')

        self.assertEqual(snapshot['id'], show_result["id"])
        self.assertEqual('Snap', show_result["name"])
        self.assertEqual('Description', show_result["description"])

    def test_share_snapshot_unset(self):
        share = self.create_share()

        snapshot = self.create_snapshot(
            share=share['id'],
            name='Snap',
            description='Description')

        self.openstack(
            f'share snapshot unset {snapshot["id"]} --name --description')

        show_result = json.loads(self.openstack(
            f'share snapshot show -f json {snapshot["id"]}'))

        self.assertEqual(snapshot['id'], show_result["id"])
        self.assertIsNone(show_result["name"])
        self.assertIsNone(show_result["description"])

    def test_share_snapshot_list(self):
        share = self.create_share()

        snapshot_1 = self.create_snapshot(share=share['id'])
        snapshot_2 = self.create_snapshot(
            share=share['id'],
            description='Description')

        snapshots_list = self.listing_result(
            'share snapshot', f'list --name {snapshot_2["name"]} '
            f'--description {snapshot_2["description"]} --all-projects'
        )

        self.assertTableStruct(snapshots_list, [
            'ID',
            'Name',
            'Project ID'
        ])

        self.assertIn(snapshot_2["name"],
                      [snap["Name"] for snap in snapshots_list])
        self.assertEqual(1, len(snapshots_list))

        snapshots_list = self.listing_result(
            'share snapshot', f'list --share {share["name"]}')

        self.assertTableStruct(snapshots_list, [
            'ID',
            'Name'
        ])

        id_list = [snap["ID"] for snap in snapshots_list]
        self.assertIn(snapshot_1["id"], id_list)
        self.assertIn(snapshot_2["id"], id_list)

        snapshots_list = self.listing_result(
            'share snapshot',
            f'list --name~ {snapshot_2["name"][-3:]} '
            '--description~ Des --detail')

        self.assertTableStruct(snapshots_list, [
            'ID',
            'Name',
            'Status',
            'Description',
            'Created At',
            'Size',
            'Share ID',
            'Share Proto',
            'Share Size',
            'User ID'
        ])

        self.assertIn(snapshot_2["name"],
                      [snap["Name"] for snap in snapshots_list])
        self.assertEqual(
            snapshot_2["description"], snapshots_list[0]['Description'])
        self.assertEqual(1, len(snapshots_list))

    def test_share_snapshot_export_location_list(self):
        share = self.create_share()

        snapshot = self.create_snapshot(share=share['id'])

        export_location_list = self.listing_result(
            'share snapshot export location', f' list {snapshot["id"]}')

        self.assertTableStruct(export_location_list, [
            'ID',
            'Path'
        ])

    def test_share_snapshot_export_location_show(self):
        share = self.create_share()

        snapshot = self.create_snapshot(share=share['id'])

        export_location_list = self.listing_result(
            'share snapshot export location', f'list {snapshot["id"]}')

        export_location = self.dict_result(
            'share snapshot export location',
            f'show {snapshot["id"]} {export_location_list[0]["ID"]}')

        self.assertIn('id', export_location)
        self.assertIn('created_at', export_location)
        self.assertIn('is_admin_only', export_location)
        self.assertIn('path', export_location)
        self.assertIn('share_snapshot_instance_id', export_location)
        self.assertIn('updated_at', export_location)

    def test_share_snapshot_abandon_adopt(self):
        share = self.create_share()

        snapshot = self.create_snapshot(
            share=share['id'], add_cleanup=False)

        self.openstack(
            f'share snapshot abandon {snapshot["id"]} --wait')

        snapshots_list = self.listing_result('share snapshot', 'list')
        self.assertNotIn(snapshot['id'],
                         [item['ID'] for item in snapshots_list])

        snapshot = self.dict_result(
            'share snapshot',
            f'adopt {share["id"]} 10.0.0.1:/foo/path '
            f'--name Snap --description Zorilla --wait')

        snapshots_list = self.listing_result('share snapshot', 'list')
        self.assertIn(snapshot['id'],
                      [item['ID'] for item in snapshots_list])

        self.addCleanup(
            self.openstack,
            f'share snapshot delete {snapshot["id"]} --force --wait')
