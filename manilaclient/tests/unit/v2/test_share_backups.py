# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

from unittest import mock

import ddt

from manilaclient import api_versions
from manilaclient.tests.unit import utils
from manilaclient.tests.unit.v2 import fakes
from manilaclient.v2 import share_backups

FAKE_BACKUP = 'fake_backup'


@ddt.ddt
class ShareBackupsTest(utils.TestCase):

    class _FakeShareBackup(object):
        id = 'fake_share_backup_id'

    def setUp(self):
        super(ShareBackupsTest, self).setUp()
        microversion = api_versions.APIVersion("2.80")
        self.manager = share_backups.ShareBackupManager(
            fakes.FakeClient(api_version=microversion))

    def test_delete_str(self):
        with mock.patch.object(self.manager, '_delete', mock.Mock()):
            self.manager.delete(FAKE_BACKUP)
            self.manager._delete.assert_called_once_with(
                share_backups.RESOURCE_PATH % FAKE_BACKUP)

    def test_delete_obj(self):
        backup = self._FakeShareBackup
        with mock.patch.object(self.manager, '_delete', mock.Mock()):
            self.manager.delete(backup)
            self.manager._delete.assert_called_once_with(
                share_backups.RESOURCE_PATH % backup.id)

    def test_get(self):
        with mock.patch.object(self.manager, '_get', mock.Mock()):
            self.manager.get(FAKE_BACKUP)
            self.manager._get.assert_called_once_with(
                share_backups.RESOURCE_PATH % FAKE_BACKUP,
                share_backups.RESOURCE_NAME)

    def test_restore(self):
        with mock.patch.object(self.manager, '_action', mock.Mock()):
            self.manager.restore(FAKE_BACKUP)
            self.manager._action.assert_called_once_with(
                'restore', FAKE_BACKUP)

    def test_list(self):
        with mock.patch.object(self.manager, '_list', mock.Mock()):
            self.manager.list()
            self.manager._list.assert_called_once_with(
                share_backups.RESOURCES_PATH + '/detail',
                share_backups.RESOURCES_NAME)

    def test_list_with_share(self):
        with mock.patch.object(self.manager, '_list', mock.Mock()):
            self.manager.list(search_opts={'share_id': 'fake_share_id'})
            share_uri = '?share_id=fake_share_id'
            self.manager._list.assert_called_once_with(
                (share_backups.RESOURCES_PATH + '/detail' + share_uri),
                share_backups.RESOURCES_NAME)

    def test_reset_state(self):
        with mock.patch.object(self.manager, '_action', mock.Mock()):
            self.manager.reset_status(FAKE_BACKUP, 'fake_status')
            self.manager._action.assert_called_once_with(
                'reset_status', FAKE_BACKUP, {'status': 'fake_status'})

    def test_update(self):
        backup = self._FakeShareBackup
        with mock.patch.object(self.manager, '_update', mock.Mock()):
            data = dict(name='backup1')
            self.manager.update(backup, **data)
            self.manager._update.assert_called_once_with(
                share_backups.RESOURCE_PATH % backup.id,
                {'share_backup': data})
