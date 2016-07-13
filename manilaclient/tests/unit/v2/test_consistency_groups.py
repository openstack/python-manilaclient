# Copyright 2015 Chuck Fouts.
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
import mock

import manilaclient
from manilaclient import exceptions
from manilaclient.tests.unit import utils
from manilaclient.tests.unit.v2 import fakes
from manilaclient.v2 import consistency_groups

FAKE_CG = 'fake consistency group'


class ConsistencyGroupsTest(utils.TestCase):

    class _FakeConsistencyGroupSnapshot(object):
        id = 'fake_cg_snapshot_id'

    def setUp(self):
        super(ConsistencyGroupsTest, self).setUp()
        self.manager = consistency_groups.ConsistencyGroupManager(
            api=fakes.FakeClient())
        self.values = {'name': 'fake name', 'description': 'new cg'}

    def test_create(self):
        body_expected = {consistency_groups.RESOURCE_NAME: self.values}

        mock_create = mock.Mock()
        mock_create.side_effect = fakes.fake_create
        with mock.patch.object(self.manager, '_create', mock_create):
            result = self.manager.create(**self.values)
            self.manager._create.assert_called_once_with(
                consistency_groups.RESOURCES_PATH,
                body_expected,
                consistency_groups.RESOURCE_NAME
            )

            self.assertEqual(result['url'], consistency_groups.RESOURCES_PATH)
            self.assertEqual(result['resp_key'],
                             consistency_groups.RESOURCE_NAME)
            self.assertEqual(result['body'], body_expected)

    def test_invalid_create(self):
        self.manager.api.api_version = manilaclient.API_MIN_VERSION

        self.assertRaises(
            exceptions.UnsupportedVersion, self.manager.create, **self.values)

    def test_create_with_share_network_id(self):
        resource_name = consistency_groups.RESOURCE_NAME
        body_expected = {resource_name: dict(list(self.values.items()))}
        body_expected[resource_name]['share_network_id'] = '050505050505'
        self.values['share_network'] = '050505050505'

        mock_create = mock.Mock()
        mock_create.side_effect = fakes.fake_create
        with mock.patch.object(self.manager, '_create', mock_create):
            result = self.manager.create(**self.values)
            self.manager._create.assert_called_once_with(
                consistency_groups.RESOURCES_PATH,
                body_expected,
                consistency_groups.RESOURCE_NAME
            )
            self.assertEqual(result['url'], consistency_groups.RESOURCES_PATH)
            self.assertEqual(result['resp_key'], resource_name)
            self.assertEqual(result['body'], body_expected)

    def test_list_not_detailed(self):
        with mock.patch.object(self.manager, '_list',
                               mock.Mock(return_value=None)):
            self.manager.list(detailed=False)
            self.manager._list.assert_called_once_with(
                consistency_groups.RESOURCES_PATH,
                consistency_groups.RESOURCES_NAME)

    def test_list(self):
        with mock.patch.object(self.manager, '_list',
                               mock.Mock(return_value=None)):
            self.manager.list()
            self.manager._list.assert_called_once_with(
                consistency_groups.RESOURCES_PATH + '/detail',
                consistency_groups.RESOURCES_NAME)

    def test_list_with_filters(self):
        filters = {'all_tenants': 1, 'status': 'ERROR'}
        expected_path = ("%s/detail?all_tenants=1&status="
                         "ERROR" % consistency_groups.RESOURCES_PATH)

        with mock.patch.object(self.manager, '_list',
                               mock.Mock(return_value=None)):
            self.manager.list(search_opts=filters)
            self.manager._list.assert_called_once_with(
                expected_path,
                consistency_groups.RESOURCES_NAME)

    def test_delete_str(self):
        with mock.patch.object(self.manager, '_delete', mock.Mock()):
            self.manager.delete(FAKE_CG)
            self.manager._delete.assert_called_once_with(
                consistency_groups.RESOURCE_PATH % FAKE_CG)

    def test_get(self):
        with mock.patch.object(self.manager, '_get', mock.Mock()):
            self.manager.get(FAKE_CG)
            self.manager._get.assert_called_once_with(
                consistency_groups.RESOURCE_PATH % FAKE_CG,
                consistency_groups.RESOURCE_NAME)

    def test_update_str(self):
        body_expected = {
            consistency_groups.RESOURCE_NAME: self.values}

        mock_update = mock.Mock()
        mock_update.side_effect = fakes.fake_update
        with mock.patch.object(self.manager, '_update', mock_update):
            result = self.manager.update(FAKE_CG, **self.values)
            self.manager._update.assert_called_once_with(
                consistency_groups.RESOURCES_PATH + '/' + FAKE_CG,
                body_expected,
                consistency_groups.RESOURCE_NAME
            )
            self.assertEqual(
                result['url'],
                consistency_groups.RESOURCE_PATH % FAKE_CG)
            self.assertEqual(
                result['resp_key'],
                consistency_groups.RESOURCE_NAME)
            self.assertEqual(result['body'], body_expected)

    def test_snapshot_update_obj(self):
        cg_snapshot = self._FakeConsistencyGroupSnapshot()
        body_expected = {consistency_groups.RESOURCE_NAME: self.values}

        mock_update = mock.Mock()
        mock_update.side_effect = fakes.fake_update
        with mock.patch.object(self.manager, '_update', mock_update):
            result = self.manager.update(cg_snapshot, **self.values)
            self.manager._update.assert_called_once_with(
                consistency_groups.RESOURCES_PATH + '/' + cg_snapshot.id,
                body_expected,
                consistency_groups.RESOURCE_NAME
            )
            self.assertEqual(
                result['url'],
                consistency_groups.RESOURCE_PATH % cg_snapshot.id)
            self.assertEqual(
                result['resp_key'],
                consistency_groups.RESOURCE_NAME)
            self.assertEqual(result['body'], body_expected)
