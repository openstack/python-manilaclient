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
from oslo_utils import uuidutils

from manilaclient.tests.functional import base


@ddt.ddt
class ExportLocationReadWriteTest(base.BaseTestCase):

    @classmethod
    def setUpClass(cls):
        super(ExportLocationReadWriteTest, cls).setUpClass()
        cls.share = cls.create_share(
            client=cls.get_user_client(),
            cleanup_in_class=True)

    @ddt.data('admin', 'user')
    def test_list_share_export_locations(self, role):
        client = self.admin_client if role == 'admin' else self.user_client
        export_locations = client.list_share_export_locations(
            self.share['id'])

        self.assertTrue(len(export_locations) > 0)
        expected_keys = (
            'Path', 'Updated At', 'Created At', 'UUID',
        )
        for el in export_locations:
            for key in expected_keys:
                self.assertIn(key, el)
            self.assertTrue(uuidutils.is_uuid_like(el['UUID']))

    @ddt.data('admin', 'user')
    def test_list_share_export_locations_with_columns(self, role):
        client = self.admin_client if role == 'admin' else self.user_client
        export_locations = client.list_share_export_locations(
            self.share['id'], columns='uuid,path')

        self.assertTrue(len(export_locations) > 0)
        expected_keys = ('Uuid', 'Path')
        unexpected_keys = ('Updated At', 'Created At')
        for el in export_locations:
            for key in expected_keys:
                self.assertIn(key, el)
            for key in unexpected_keys:
                self.assertNotIn(key, el)
            self.assertTrue(uuidutils.is_uuid_like(el['Uuid']))

    @ddt.data('admin', 'user')
    def test_get_share_export_location(self, role):
        client = self.admin_client if role == 'admin' else self.user_client
        export_locations = client.list_share_export_locations(
            self.share['id'])

        el = client.get_share_export_location(
            self.share['id'], export_locations[0]['UUID'])

        expected_keys = [
            'path', 'updated_at', 'created_at', 'uuid',
        ]
        if role == 'admin':
            expected_keys.extend(['is_admin_only', 'share_instance_id'])
        for key in expected_keys:
            self.assertIn(key, el)
        if role == 'admin':
            self.assertTrue(uuidutils.is_uuid_like(el['share_instance_id']))
            self.assertIn(el['is_admin_only'], ('True', 'False'))
        self.assertTrue(uuidutils.is_uuid_like(el['uuid']))
        for list_k, get_k in (
                ('UUID', 'uuid'), ('Created At', 'created_at'),
                ('Path', 'path'), ('Updated At', 'updated_at')):
            self.assertEqual(
                export_locations[0][list_k], el[get_k])

    def test_list_share_instance_export_locations(self):
        client = self.admin_client
        share_instances = client.list_share_instances(self.share['id'])
        self.assertTrue(len(share_instances) > 0)
        self.assertIn('ID', share_instances[0])
        self.assertTrue(uuidutils.is_uuid_like(share_instances[0]['ID']))
        share_instance_id = share_instances[0]['ID']

        export_locations = client.list_share_instance_export_locations(
            share_instance_id)

        self.assertTrue(len(export_locations) > 0)
        expected_keys = (
            'Path', 'Updated At', 'Created At', 'UUID', 'Is Admin only',
        )
        for el in export_locations:
            for key in expected_keys:
                self.assertIn(key, el)
            self.assertTrue(uuidutils.is_uuid_like(el['UUID']))

    def test_list_share_instance_export_locations_with_columns(self):
        client = self.admin_client
        share_instances = client.list_share_instances(self.share['id'])
        self.assertTrue(len(share_instances) > 0)
        self.assertIn('ID', share_instances[0])
        self.assertTrue(uuidutils.is_uuid_like(share_instances[0]['ID']))
        share_instance_id = share_instances[0]['ID']

        export_locations = client.list_share_instance_export_locations(
            share_instance_id, columns='uuid,path')

        self.assertTrue(len(export_locations) > 0)
        expected_keys = ('Uuid', 'Path')
        unexpected_keys = (
            'Updated At', 'Created At', 'Is Admin only',
        )
        for el in export_locations:
            for key in expected_keys:
                self.assertIn(key, el)
            for key in unexpected_keys:
                self.assertNotIn(key, el)
            self.assertTrue(uuidutils.is_uuid_like(el['Uuid']))

    def test_get_share_instance_export_location(self):
        client = self.admin_client
        share_instances = client.list_share_instances(self.share['id'])
        self.assertTrue(len(share_instances) > 0)
        self.assertIn('ID', share_instances[0])
        self.assertTrue(uuidutils.is_uuid_like(share_instances[0]['ID']))
        share_instance_id = share_instances[0]['ID']

        export_locations = client.list_share_instance_export_locations(
            share_instance_id)

        el = client.get_share_instance_export_location(
            share_instance_id, export_locations[0]['UUID'])

        expected_keys = (
            'path', 'updated_at', 'created_at', 'uuid',
            'is_admin_only', 'share_instance_id',
        )
        for key in expected_keys:
            self.assertIn(key, el)
        self.assertIn(el['is_admin_only'], ('True', 'False'))
        self.assertTrue(uuidutils.is_uuid_like(el['uuid']))
        for list_k, get_k in (
                ('UUID', 'uuid'), ('Created At', 'created_at'),
                ('Path', 'path'), ('Updated At', 'updated_at')):
            self.assertEqual(
                export_locations[0][list_k], el[get_k])
