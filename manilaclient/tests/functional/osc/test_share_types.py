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


class ShareTypesCLITest(base.OSCClientTestBase):

    def test_share_type_create(self):
        name = 'test_share_type'
        description = 'Description'
        share_type = self.create_share_type(
            name=name, description=description)

        self.assertEqual(name, share_type["name"])
        self.assertEqual(description, share_type["description"])
        self.assertEqual('public', share_type["visibility"])

        share_types_list = self.listing_result('share type', 'list')
        self.assertIn(
            share_type["id"], [item['ID'] for item in share_types_list])

    def test_share_type_create_specs(self):
        share_type = self.create_share_type(
            snapshot_support=True,
            create_share_from_snapshot_support=True,
            revert_to_snapshot_support=True,
            mount_snapshot_support=True,
            extra_specs={
                "foo": "bar",
                "manila": "zorilla"
            },
            formatter='json')

        required_specs = share_type["required_extra_specs"]
        optional_specs = share_type["optional_extra_specs"]

        self.assertEqual(
            False, required_specs["driver_handles_share_servers"])
        self.assertEqual('True', optional_specs["snapshot_support"])
        self.assertEqual(
            'True', optional_specs["create_share_from_snapshot_support"])
        self.assertEqual(
            'True', optional_specs["revert_to_snapshot_support"])
        self.assertEqual('True', optional_specs["mount_snapshot_support"])
        self.assertEqual("bar", optional_specs["foo"])
        self.assertEqual("zorilla", optional_specs["manila"])

    def test_share_type_delete(self):
        share_type_1 = self.create_share_type(add_cleanup=False)
        share_type_2 = self.create_share_type(add_cleanup=False)

        self.openstack(
            f'share type delete {share_type_1["id"]} {share_type_2["id"]}'
        )

        self.check_object_deleted('share type', share_type_1["id"])
        self.check_object_deleted('share type', share_type_2["id"])

    def test_share_type_set(self):
        share_type = self.create_share_type()

        self.openstack(
            f'share type set {share_type["id"]} --description Description'
            ' --name Name --public false --extra-specs foo=bar'
        )

        share_type = json.loads(self.openstack(
            f'share type show {share_type["id"]} -f json'
        ))

        self.assertEqual('Description', share_type["description"])
        self.assertEqual('Name', share_type["name"])
        self.assertEqual('private', share_type["visibility"])
        self.assertEqual(
            'bar', share_type["optional_extra_specs"]["foo"])

    def test_share_type_unset(self):
        share_type = self.create_share_type(
            snapshot_support=True,
            extra_specs={'foo': 'bar'})

        self.openstack(
            f'share type unset {share_type["id"]} '
            'snapshot_support foo')

        share_type = json.loads(self.openstack(
            f'share type show {share_type["id"]} -f json'
        ))

        self.assertNotIn('foo', share_type["optional_extra_specs"])
        self.assertNotIn(
            'snapshot_support', share_type["optional_extra_specs"])

    def test_share_type_list(self):
        share_type_1 = self.create_share_type(public=False)
        share_type_2 = self.create_share_type(
            extra_specs={'foo': 'bar'})

        types_list = self.listing_result(
            'share type', 'list --all', client=self.admin_client)

        self.assertTableStruct(types_list, [
            'ID',
            'Name',
            'Visibility',
            'Is Default',
            'Required Extra Specs',
            'Optional Extra Specs',
            'Description'
        ])
        id_list = [item['ID'] for item in types_list]
        self.assertIn(share_type_1['id'], id_list)
        self.assertIn(share_type_2['id'], id_list)

        types_list = self.listing_result(
            'share type', 'list --extra-specs foo=bar')

        id_list = [item['ID'] for item in types_list]
        self.assertNotIn(share_type_1['id'], id_list)
        self.assertIn(share_type_2['id'], id_list)

    def test_share_type_show(self):
        share_type = self.create_share_type(
            extra_specs={'foo': 'bar'})

        result = json.loads(self.openstack(
            f'share type show {share_type["id"]} -f json'))

        self.assertEqual(share_type["name"], result["name"])
        self.assertEqual(
            share_type["visibility"], result["visibility"])
        self.assertEqual(
            share_type["is_default"], str(result["is_default"]))
        self.assertEqual(
            'bar', result["optional_extra_specs"]["foo"])
