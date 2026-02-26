# Copyright (c) 2025 Cloudification GmbH.
#
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


class QosTypesCLITest(base.OSCClientTestBase):
    def test_qos_type_create(self):
        name = 'test_qos_type'
        description = 'Description'
        qos_type = self.create_qos_type(name=name, description=description)

        self.assertEqual(name, qos_type["name"])
        self.assertEqual(description, qos_type["description"])

        qos_types_list = self.listing_result('share qos type', 'list')
        self.assertIn(qos_type["id"], [item['ID'] for item in qos_types_list])

    def test_qos_type_create_specs(self):
        name = 'test_qos_type2'
        qos_type = self.create_qos_type(
            name=name,
            specs={"foo": "bar", "manila": "gazpacho"},
            formatter='json',
        )

        specs = qos_type["specs"]
        self.assertEqual("bar", specs["foo"])
        self.assertEqual("gazpacho", specs["manila"])

    def test_qos_type_create_specs_using_command(self):
        self.openstack(
            'share qos type create test_qos_type2_cli '
            '--description test_cli --spec foo1=bar1 --spec foo2=bar2'
        )
        self.addCleanup(
            self.openstack, 'share qos type delete test_qos_type2_cli'
        )

        qos_type = json.loads(
            self.openstack('share qos type show test_qos_type2_cli -f json')
        )

        self.assertEqual('test_cli', qos_type["description"])
        self.assertEqual('bar1', qos_type["specs"]["foo1"])
        self.assertEqual('bar2', qos_type["specs"]["foo2"])

    def test_qos_type_delete(self):
        qos_type_1 = self.create_qos_type(
            name='test_qos_type3', add_cleanup=False
        )
        qos_type_2 = self.create_qos_type(
            name='test_qos_type4', add_cleanup=False
        )

        self.openstack(
            f'share qos type delete {qos_type_1["id"]} {qos_type_2["id"]}'
        )

        self.check_object_deleted('share qos type', qos_type_1["id"])
        self.check_object_deleted('share qos type', qos_type_2["id"])

    def test_qos_type_set(self):
        qos_type = self.create_qos_type(name='test_qos_type5')

        self.openstack(
            f'share qos type set {qos_type["id"]} --description Description'
            ' --spec foo=bar2'
        )

        qos_type = json.loads(
            self.openstack(f'share qos type show {qos_type["id"]} -f json')
        )

        self.assertEqual('Description', qos_type["description"])
        self.assertEqual('bar2', qos_type["specs"]["foo"])

    def test_qos_type_unset(self):
        qos_type = self.create_qos_type(
            name='test_qos_type6', specs={'foo': 'bar', 'foo1': 'bar1'}
        )

        self.openstack(
            f'share qos type unset {qos_type["id"]} --spec foo --spec foo1'
        )

        qos_type = json.loads(
            self.openstack(f'share qos type show {qos_type["id"]} -f json')
        )

        self.assertNotIn('foo', qos_type["specs"])
        self.assertNotIn('foo1', qos_type["specs"])

    def test_qos_type_list(self):
        qos_type_1 = self.create_qos_type(name='test_qos_type7')
        qos_type_2 = self.create_qos_type(
            name='test_qos_type8', specs={'foo': 'bar'}
        )

        types_list = self.listing_result(
            'share qos type', 'list', client=self.admin_client
        )

        self.assertTableStruct(
            types_list,
            [
                'ID',
                'Name',
                'Description',
                'Specs',
            ],
        )
        id_list = [item['ID'] for item in types_list]
        self.assertIn(qos_type_1['id'], id_list)
        self.assertIn(qos_type_2['id'], id_list)

        types_list = self.listing_result('share qos type', 'list')

        id_list = [item['ID'] for item in types_list]
        self.assertIn(qos_type_1['id'], id_list)
        self.assertIn(qos_type_2['id'], id_list)

    def test_qos_type_show(self):
        qos_type = self.create_qos_type(
            name='test_qos_type10', specs={'foo': 'bar'}
        )

        result = json.loads(
            self.openstack(f'share qos type show {qos_type["id"]} -f json')
        )

        self.assertEqual(qos_type["name"], result["name"])
        self.assertEqual('bar', result["specs"]["foo"])
