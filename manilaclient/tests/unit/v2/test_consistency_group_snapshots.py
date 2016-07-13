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
from manilaclient.v2 import consistency_group_snapshots as cg_snapshots

FAKE_CG = 'fake cg snapshot'
FAKE_CG_ID = 'fake-cg-id'


class ConsistencyGroupSnapshotsTest(utils.TestCase):

    class _FakeConsistencyGroupSnapshot(object):
        id = 'fake_cg_snapshot_id'

    def setUp(self):
        super(ConsistencyGroupSnapshotsTest, self).setUp()
        self.manager = cg_snapshots.ConsistencyGroupSnapshotManager(
            api=fakes.FakeClient())
        self.values = {
            'consistency_group_id': 'fake_cg_id',
            'name': 'fake snapshot name',
            'description': 'new cg snapshot',
        }

    def test_snapshot_create(self):
        body_expected = {cg_snapshots.RESOURCE_NAME: self.values}

        mock_create = mock.Mock()
        mock_create.side_effect = fakes.fake_create
        with mock.patch.object(self.manager, '_create', mock_create):
            result = self.manager.create(**self.values)
            self.manager._create.assert_called_once_with(
                cg_snapshots.RESOURCES_PATH,
                body_expected,
                cg_snapshots.RESOURCE_NAME)

            self.assertEqual(result['url'], cg_snapshots.RESOURCES_PATH)
            self.assertEqual(result['resp_key'], cg_snapshots.RESOURCE_NAME)
            self.assertEqual(result['body'], body_expected)

    def test_snapshot_create_invalid_version(self):
        self.manager.api.api_version = manilaclient.API_MIN_VERSION

        self.assertRaises(
            exceptions.UnsupportedVersion, self.manager.create, **self.values)

    def test_snapshot_get(self):
        with mock.patch.object(self.manager, '_get', mock.Mock()):
            self.manager.get(FAKE_CG_ID)
            self.manager._get.assert_called_once_with(
                cg_snapshots.RESOURCE_PATH % FAKE_CG_ID,
                cg_snapshots.RESOURCE_NAME)

    def test_snapshot_update_str(self):
        body_expected = {cg_snapshots.RESOURCE_NAME: self.values}

        mock_update = mock.Mock()
        mock_update.side_effect = fakes.fake_update
        with mock.patch.object(self.manager, '_update', mock_update):

            result = self.manager.update(FAKE_CG, **self.values)
            self.manager._update.assert_called_once_with(
                cg_snapshots.RESOURCES_PATH + '/' + FAKE_CG,
                body_expected,
                cg_snapshots.RESOURCE_NAME
            )

            self.assertEqual(
                result['url'],
                cg_snapshots.RESOURCE_PATH % FAKE_CG)
            self.assertEqual(
                result['resp_key'],
                cg_snapshots.RESOURCE_NAME)
            self.assertEqual(result['body'], body_expected)

    def test_snapshot_update_obj(self):
        cg_snapshot = self._FakeConsistencyGroupSnapshot()
        body_expected = {cg_snapshots.RESOURCE_NAME: self.values}
        mock_update = mock.Mock()
        mock_update.side_effect = fakes.fake_update

        with mock.patch.object(self.manager, '_update', mock_update):
            result = self.manager.update(cg_snapshot, **self.values)
            self.manager._update.assert_called_once_with(
                cg_snapshots.RESOURCES_PATH + '/' + cg_snapshot.id,
                body_expected,
                cg_snapshots.RESOURCE_NAME
            )
            self.assertEqual(
                result['url'],
                cg_snapshots.RESOURCE_PATH % cg_snapshot.id)
            self.assertEqual(
                result['resp_key'],
                cg_snapshots.RESOURCE_NAME)
            self.assertEqual(result['body'], body_expected)

    def test_snapshot_list_not_detailed(self):
        with mock.patch.object(self.manager, '_list',
                               mock.Mock(return_value=None)):
            self.manager.list(detailed=False)
            self.manager._list.assert_called_once_with(
                cg_snapshots.RESOURCES_PATH,
                cg_snapshots.RESOURCES_NAME)

    def test_snapshot_list(self):
        with mock.patch.object(self.manager, '_list',
                               mock.Mock(return_value=None)):
            self.manager.list()
            self.manager._list.assert_called_once_with(
                cg_snapshots.RESOURCES_PATH + '/detail',
                cg_snapshots.RESOURCES_NAME)

    def test_snapshot_list_with_filters(self):
        filters = {'all_tenants': 1, 'status': 'ERROR'}
        expected_path = ("%s/detail?all_tenants=1&status="
                         "ERROR" % cg_snapshots.RESOURCES_PATH)

        with mock.patch.object(self.manager, '_list',
                               mock.Mock(return_value=None)):
            self.manager.list(search_opts=filters)
            self.manager._list.assert_called_once_with(
                expected_path,
                cg_snapshots.RESOURCES_NAME)

    def test_snapshot_members(self):
        with mock.patch.object(self.manager, '_list',
                               mock.Mock(return_value=None)):
            self.manager.members(FAKE_CG_ID)
            self.manager._list.assert_called_once_with(
                cg_snapshots.RESOURCES_PATH + '/' + FAKE_CG_ID + '/members',
                'cgsnapshot_members')

    def test_snapshot_members_with_filters(self):
        search_opts = {'fake_str': 'fake_str_value', 'fake_int': 1}
        query_str = FAKE_CG_ID + '/members?fake_int=1&fake_str=fake_str_value'
        with mock.patch.object(self.manager, '_list',
                               mock.Mock(return_value=None)):
            self.manager.members(FAKE_CG_ID, search_opts=search_opts)
            self.manager._list.assert_called_once_with(
                cg_snapshots.RESOURCES_PATH + '/' + query_str,
                cg_snapshots.MEMBERS_RESOURCE_NAME)

    def test_snapshot_members_with_offset(self):
        with mock.patch.object(self.manager, '_list',
                               mock.Mock(return_value=None)):
            keys = {'offset': 22}

            url = FAKE_CG_ID + '/members?offset=22'
            self.manager.members(FAKE_CG_ID, keys)
            self.manager._list.assert_called_once_with(
                cg_snapshots.RESOURCES_PATH + '/' + url,
                cg_snapshots.MEMBERS_RESOURCE_NAME)

    def test_snapshot_delete_str(self):
        fake_cg_snapshot = 'fake cgsnapshot'
        with mock.patch.object(self.manager, '_delete', mock.Mock()):
            self.manager.delete(fake_cg_snapshot)
            self.manager._delete.assert_called_once_with(
                cg_snapshots.RESOURCE_PATH % fake_cg_snapshot)

    def test_snapshot_delete_obj(self):
        cg_snapshot = self._FakeConsistencyGroupSnapshot()
        with mock.patch.object(self.manager, '_delete', mock.Mock()):
            self.manager.delete(cg_snapshot)
            self.manager._delete.assert_called_once_with(
                cg_snapshots.RESOURCE_PATH % cg_snapshot.id)
