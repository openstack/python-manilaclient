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
#
from osc_lib import exceptions
from osc_lib import utils as oscutils

from manilaclient import api_versions
from manilaclient.api_versions import MAX_VERSION
from manilaclient.osc.v2 import share_backups as osc_share_backups
from manilaclient.tests.unit.osc import osc_utils
from manilaclient.tests.unit.osc.v2 import fakes as manila_fakes


class TestShareBackup(manila_fakes.TestShare):

    def setUp(self):
        super(TestShareBackup, self).setUp()

        self.shares_mock = self.app.client_manager.share.shares
        self.shares_mock.reset_mock()

        self.backups_mock = self.app.client_manager.share.share_backups
        self.backups_mock.reset_mock()
        self.app.client_manager.share.api_version = api_versions.APIVersion(
            MAX_VERSION)


class TestShareBackupCreate(TestShareBackup):

    def setUp(self):
        super(TestShareBackupCreate, self).setUp()

        self.share = manila_fakes.FakeShare.create_one_share()
        self.shares_mock.get.return_value = self.share

        self.share_backup = (
            manila_fakes.FakeShareBackup.create_one_backup(
                attrs={'status': 'available'}
            ))
        self.backups_mock.create.return_value = self.share_backup
        self.backups_mock.get.return_value = self.share_backup
        self.cmd = osc_share_backups.CreateShareBackup(self.app, None)
        self.data = tuple(self.share_backup._info.values())
        self.columns = tuple(self.share_backup._info.keys())

    def test_share_backup_create_missing_args(self):
        arglist = []
        verifylist = []

        self.assertRaises(
            osc_utils.ParserException,
            self.check_parser, self.cmd, arglist, verifylist)

    def test_share_backup_create(self):
        arglist = [
            self.share.id
        ]
        verifylist = [
            ('share', self.share.id)
        ]

        parsed_args = self.check_parser(self.cmd, arglist, verifylist)
        columns, data = self.cmd.take_action(parsed_args)
        self.backups_mock.create.assert_called_with(
            self.share,
        )

        self.assertCountEqual(self.columns, columns)
        self.assertCountEqual(self.data, data)

    def test_share_backup_create_name(self):
        arglist = [
            self.share.id,
            '--name', "FAKE_SHARE_BACKUP_NAME"
        ]
        verifylist = [
            ('share', self.share.id),
            ('name', "FAKE_SHARE_BACKUP_NAME")
        ]

        parsed_args = self.check_parser(self.cmd, arglist, verifylist)
        columns, data = self.cmd.take_action(parsed_args)
        self.backups_mock.create.assert_called_with(
            self.share,
            name="FAKE_SHARE_BACKUP_NAME",
        )

        self.assertCountEqual(self.columns, columns)
        self.assertCountEqual(self.data, data)


class TestShareBackupDelete(TestShareBackup):

    def setUp(self):
        super(TestShareBackupDelete, self).setUp()

        self.share_backup = (
            manila_fakes.FakeShareBackup.create_one_backup())
        self.backups_mock.get.return_value = self.share_backup

        self.cmd = osc_share_backups.DeleteShareBackup(self.app, None)

    def test_share_backup_delete_missing_args(self):
        arglist = []
        verifylist = []

        self.assertRaises(osc_utils.ParserException,
                          self.check_parser, self.cmd, arglist, verifylist)

    def test_share_backup_delete(self):
        arglist = [
            self.share_backup.id
        ]
        verifylist = [
            ('backup', [self.share_backup.id])
        ]

        parsed_args = self.check_parser(self.cmd, arglist, verifylist)
        result = self.cmd.take_action(parsed_args)
        self.backups_mock.delete.assert_called_with(self.share_backup)
        self.assertIsNone(result)

    def test_share_backup_delete_multiple(self):
        share_backups = (
            manila_fakes.FakeShareBackup.create_share_backups(
                count=2))
        arglist = [
            share_backups[0].id,
            share_backups[1].id
        ]
        verifylist = [
            ('backup', [share_backups[0].id, share_backups[1].id])
        ]
        parsed_args = self.check_parser(self.cmd, arglist, verifylist)
        result = self.cmd.take_action(parsed_args)
        self.assertEqual(self.backups_mock.delete.call_count,
                         len(share_backups))
        self.assertIsNone(result)

    def test_share_backup_delete_exception(self):
        arglist = [
            self.share_backup.id
        ]
        verifylist = [
            ('backup', [self.share_backup.id])
        ]

        parsed_args = self.check_parser(self.cmd, arglist, verifylist)
        self.backups_mock.delete.side_effect = exceptions.CommandError()
        self.assertRaises(exceptions.CommandError,
                          self.cmd.take_action,
                          parsed_args)


class TestShareBackupList(TestShareBackup):

    columns = [
        'ID',
        'Name',
        'Share ID',
        'Status',
    ]
    detailed_columns = [
        'ID',
        'Name',
        'Share ID',
        'Status',
        'Description',
        'Size',
        'Created At',
        'Updated At',
        'Availability Zone',
        'Progress',
        'Restore Progress',
        'Host',
        'Topic',
    ]

    def setUp(self):
        super(TestShareBackupList, self).setUp()

        self.share = manila_fakes.FakeShare.create_one_share()
        self.shares_mock.get.return_value = self.share
        self.backups_list = (
            manila_fakes.FakeShareBackup.create_share_backups(
                count=2))
        self.backups_mock.list.return_value = self.backups_list
        self.values = (oscutils.get_dict_properties(
            i._info, self.columns) for i in self.backups_list)
        self.detailed_values = (oscutils.get_dict_properties(
            i._info, self.detailed_columns) for i in self.backups_list)

        self.cmd = osc_share_backups.ListShareBackup(self.app, None)

    def test_share_backup_list(self):
        arglist = []
        verifylist = []

        parsed_args = self.check_parser(self.cmd, arglist, verifylist)
        columns, data = self.cmd.take_action(parsed_args)
        self.backups_mock.list.assert_called_with(
            detailed=0,
            search_opts={
                'offset': None, 'limit': None, 'name': None,
                'description': None, 'name~': None, 'description~': None,
                'status': None, 'share_id': None
            },
            sort_key=None, sort_dir=None
        )
        self.assertEqual(self.columns, columns)
        self.assertEqual(list(self.values), list(data))

    def test_share_backup_list_detail(self):
        arglist = [
            '--detail'
        ]
        verifylist = [
            ('detail', True)
        ]

        parsed_args = self.check_parser(self.cmd, arglist, verifylist)
        columns, data = self.cmd.take_action(parsed_args)
        self.backups_mock.list.assert_called_with(
            detailed=1,
            search_opts={
                'offset': None, 'limit': None, 'name': None,
                'description': None, 'name~': None, 'description~': None,
                'status': None, 'share_id': None
            },
            sort_key=None, sort_dir=None
        )
        self.assertEqual(self.detailed_columns, columns)
        self.assertEqual(list(self.detailed_values), list(data))

    def test_share_backup_list_for_share(self):
        arglist = [
            '--share', self.share.id
        ]
        verifylist = [
            ('share', self.share.id)
        ]

        parsed_args = self.check_parser(self.cmd, arglist, verifylist)
        columns, data = self.cmd.take_action(parsed_args)
        self.backups_mock.list.assert_called_with(
            detailed=0,
            search_opts={
                'offset': None, 'limit': None, 'name': None,
                'description': None, 'name~': None, 'description~': None,
                'status': None, 'share_id': self.share.id
            },
            sort_key=None, sort_dir=None
        )
        self.assertEqual(self.columns, columns)
        self.assertEqual(list(self.values), list(data))


class TestShareBackupShow(TestShareBackup):

    def setUp(self):
        super(TestShareBackupShow, self).setUp()
        self.share_backup = (
            manila_fakes.FakeShareBackup.create_one_backup()
        )
        self.backups_mock.get.return_value = self.share_backup
        self.cmd = osc_share_backups.ShowShareBackup(self.app, None)
        self.data = tuple(self.share_backup._info.values())
        self.columns = tuple(self.share_backup._info.keys())

    def test_share_backup_show_missing_args(self):
        arglist = []
        verifylist = []

        self.assertRaises(
            osc_utils.ParserException,
            self.check_parser, self.cmd, arglist, verifylist)

    def test_share_backup_show(self):
        arglist = [
            self.share_backup.id
        ]
        verifylist = [
            ('backup', self.share_backup.id)
        ]

        parsed_args = self.check_parser(self.cmd, arglist, verifylist)
        columns, data = self.cmd.take_action(parsed_args)
        self.backups_mock.get.assert_called_with(
            self.share_backup.id
        )

        self.assertCountEqual(self.columns, columns)
        self.assertCountEqual(self.data, data)


class TestShareBackupRestore(TestShareBackup):

    def setUp(self):
        super(TestShareBackupRestore, self).setUp()
        self.share_backup = (
            manila_fakes.FakeShareBackup.create_one_backup()
        )
        self.backups_mock.get.return_value = self.share_backup
        self.cmd = osc_share_backups.RestoreShareBackup(
            self.app, None)

    def test_share_backup_restore(self):
        arglist = [
            self.share_backup.id,
        ]
        verifylist = [
            ('backup', self.share_backup.id),
        ]
        parsed_args = self.check_parser(self.cmd, arglist, verifylist)
        result = self.cmd.take_action(parsed_args)
        self.backups_mock.restore.assert_called_with(self.share_backup.id)
        self.assertIsNone(result)


class TestShareBackupSet(TestShareBackup):

    def setUp(self):
        super(TestShareBackupSet, self).setUp()
        self.share_backup = (
            manila_fakes.FakeShareBackup.create_one_backup()
        )
        self.backups_mock.get.return_value = self.share_backup
        self.cmd = osc_share_backups.SetShareBackup(self.app, None)

    def test_set_share_backup_name(self):
        arglist = [
            self.share_backup.id,
            '--name', "FAKE_SHARE_BACKUP_NAME"
        ]
        verifylist = [
            ('backup', self.share_backup.id),
            ('name', "FAKE_SHARE_BACKUP_NAME")
        ]

        parsed_args = self.check_parser(self.cmd, arglist, verifylist)
        result = self.cmd.take_action(parsed_args)
        self.backups_mock.update.assert_called_with(self.share_backup,
                                                    name=parsed_args.name)
        self.assertIsNone(result)

    def test_set_backup_status(self):
        arglist = [
            self.share_backup.id,
            '--status', 'available'
        ]
        verifylist = [
            ('backup', self.share_backup.id),
            ('status', 'available')
        ]
        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        result = self.cmd.take_action(parsed_args)

        self.backups_mock.reset_status.assert_called_with(
            self.share_backup,
            parsed_args.status)
        self.assertIsNone(result)


class TestShareBackupUnset(TestShareBackup):

    def setUp(self):
        super(TestShareBackupUnset, self).setUp()

        self.share_backup = (
            manila_fakes.FakeShareBackup.create_one_backup()
        )

        self.backups_mock.get.return_value = self.share_backup
        self.cmd = osc_share_backups.UnsetShareBackup(self.app, None)

    def test_unset_backup_name(self):
        arglist = [
            self.share_backup.id,
            '--name'
        ]
        verifylist = [
            ('backup', self.share_backup.id),
            ('name', True)
        ]
        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        result = self.cmd.take_action(parsed_args)

        self.backups_mock.update.assert_called_with(
            self.share_backup,
            name=None)
        self.assertIsNone(result)

    def test_unset_backup_description(self):
        arglist = [
            self.share_backup.id,
            '--description'
        ]
        verifylist = [
            ('backup', self.share_backup.id),
            ('description', True)
        ]
        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        result = self.cmd.take_action(parsed_args)

        self.backups_mock.update.assert_called_with(
            self.share_backup,
            description=None)
        self.assertIsNone(result)
