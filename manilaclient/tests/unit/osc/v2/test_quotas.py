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

import mock

from osc_lib import exceptions

from openstackclient.tests.unit.identity.v3 import fakes as identity_fakes

from manilaclient import api_versions
from manilaclient.common.apiclient.exceptions import BadRequest
from manilaclient.osc.v2 import quotas as osc_quotas
from manilaclient.tests.unit.osc.v2 import fakes as manila_fakes


class TestQuotas(manila_fakes.TestShare):

    def setUp(self):
        super(TestQuotas, self).setUp()

        self.quotas_mock = self.app.client_manager.share.quotas
        self.quotas_mock.reset_mock()

        self.quota_classes_mock = self.app.client_manager.share.quota_classes
        self.quota_classes_mock.reset_mock()

        self.app.client_manager.share.api_version = api_versions.APIVersion(
            api_versions.MAX_VERSION
        )


class TestQuotaSet(TestQuotas):
    project = identity_fakes.FakeProject.create_one_project()
    user = identity_fakes.FakeUser.create_one_user()

    def setUp(self):
        super(TestQuotaSet, self).setUp()

        self.quotas = manila_fakes.FakeQuotaSet.create_fake_quotas()
        self.quotas_mock.update = mock.Mock()
        self.quotas_mock.update.return_value = None

        self.quota_classes_mock.update = mock.Mock()
        self.quota_classes_mock.update.return_value = None

        self.cmd = osc_quotas.QuotaSet(self.app, None)

    def test_quota_set_default_class_shares(self):
        arglist = [
            'default',
            '--class',
            '--shares', '40'
        ]
        verifylist = [
            ('project', 'default'),
            ('quota_class', True),
            ('shares', 40)
        ]

        with mock.patch('osc_lib.utils.find_resource') as mock_find_resource:
            mock_find_resource.return_value = self.project

            parsed_args = self.check_parser(self.cmd, arglist, verifylist)

            result = self.cmd.take_action(parsed_args)
            self.quota_classes_mock.update.assert_called_with(
                class_name='default',
                gigabytes=None,
                share_networks=None,
                shares=40,
                snapshot_gigabytes=None,
                snapshots=None,
                per_share_gigabytes=None)
            self.assertIsNone(result)
            mock_find_resource.assert_not_called()
            self.quotas_mock.assert_not_called()

    def test_quota_set_shares(self):
        arglist = [
            self.project.id,
            '--shares', '40'
        ]
        verifylist = [
            ('project', self.project.id),
            ('shares', 40)
        ]

        with mock.patch('osc_lib.utils.find_resource') as mock_find_resource:
            mock_find_resource.return_value = self.project

            parsed_args = self.check_parser(self.cmd, arglist, verifylist)

            result = self.cmd.take_action(parsed_args)
            self.quotas_mock.update.assert_called_with(
                force=None,
                gigabytes=None,
                share_networks=None,
                shares=40,
                snapshot_gigabytes=None,
                snapshots=None,
                per_share_gigabytes=None,
                tenant_id=self.project.id,
                user_id=None)
            self.assertIsNone(result)

    def test_quota_set_gigabytes(self):
        arglist = [
            self.project.id,
            '--gigabytes', '1100'
        ]
        verifylist = [
            ('project', self.project.id),
            ('gigabytes', 1100)
        ]

        with mock.patch('osc_lib.utils.find_resource') as mock_find_resource:
            mock_find_resource.return_value = self.project

            parsed_args = self.check_parser(self.cmd, arglist, verifylist)

            result = self.cmd.take_action(parsed_args)
            self.quotas_mock.update.assert_called_with(
                force=None,
                gigabytes=1100,
                share_networks=None,
                shares=None,
                snapshot_gigabytes=None,
                snapshots=None,
                per_share_gigabytes=None,
                tenant_id=self.project.id,
                user_id=None)
            self.assertIsNone(result)

    def test_quota_set_share_type(self):
        arglist = [
            self.project.id,
            '--share-type', 'default'
        ]
        verifylist = [
            ('project', self.project.id),
            ('share_type', 'default')
        ]

        with mock.patch('osc_lib.utils.find_resource') as mock_find_resource:
            mock_find_resource.return_value = self.project

            parsed_args = self.check_parser(self.cmd, arglist, verifylist)

            result = self.cmd.take_action(parsed_args)
            self.quotas_mock.update.assert_called_with(
                force=None,
                gigabytes=None,
                share_networks=None,
                share_type='default',
                shares=None,
                snapshot_gigabytes=None,
                snapshots=None,
                per_share_gigabytes=None,
                tenant_id=self.project.id,
                user_id=None)
            self.assertIsNone(result)

    def test_quota_set_force(self):
        arglist = [
            self.project.id,
            '--force',
            '--shares', '40'
        ]
        verifylist = [
            ('project', self.project.id),
            ('force', True),
            ('shares', 40)
        ]

        with mock.patch('osc_lib.utils.find_resource') as mock_find_resource:
            mock_find_resource.return_value = self.project

            parsed_args = self.check_parser(self.cmd, arglist, verifylist)

            result = self.cmd.take_action(parsed_args)
            self.quotas_mock.update.assert_called_with(
                force=True,
                gigabytes=None,
                share_networks=None,
                shares=40,
                snapshot_gigabytes=None,
                snapshots=None,
                tenant_id=self.project.id,
                per_share_gigabytes=None,
                user_id=None)
            self.assertIsNone(result)

    def test_quota_set_api_version_exception(self):
        self.app.client_manager.share.api_version = api_versions.APIVersion(
            '2.39'
        )

        arglist = [
            self.project.id,
            '--share-groups', '40'
        ]
        verifylist = [
            ('project', self.project.id),
            ('share_groups', 40)
        ]

        parsed_args = self.check_parser(self.cmd, arglist, verifylist)
        self.assertRaises(
            exceptions.CommandError, self.cmd.take_action, parsed_args)

    def test_quota_set_update_project_exception(self):
        arglist = [
            self.project.id,
            '--share-groups', '40',
            '--share-group-snapshots', '40'
        ]
        verifylist = [
            ('project', self.project.id),
            ('share_groups', 40),
            ('share_group_snapshots', 40)
        ]

        parsed_args = self.check_parser(self.cmd, arglist, verifylist)
        self.quotas_mock.update.side_effect = BadRequest()
        self.assertRaises(
            exceptions.CommandError, self.cmd.take_action, parsed_args)

    def test_quota_set_update_class_exception(self):
        arglist = [
            'default',
            '--class',
            '--gigabytes', '40'
        ]
        verifylist = [
            ('project', 'default'),
            ('gigabytes', 40)
        ]

        parsed_args = self.check_parser(self.cmd, arglist, verifylist)
        self.quota_classes_mock.update.side_effect = BadRequest()
        self.assertRaises(
            exceptions.CommandError, self.cmd.take_action, parsed_args)

    def test_quota_set_nothing_to_set_exception(self):
        arglist = [
            self.project.id,
        ]
        verifylist = [
            ('project', self.project.id)
        ]

        parsed_args = self.check_parser(self.cmd, arglist, verifylist)
        self.assertRaises(
            exceptions.CommandError, self.cmd.take_action, parsed_args)

    def test_quota_set_share_replicas(self):
        self.app.client_manager.share.api_version = api_versions.APIVersion(
            '2.53'
        )

        arglist = [
            self.project.id,
            '--share-replicas', '2',
        ]
        verifylist = [
            ('project', self.project.id),
            ('share_replicas', 2)
        ]

        with mock.patch('osc_lib.utils.find_resource') as mock_find_resource:
            mock_find_resource.return_value = self.project

            parsed_args = self.check_parser(self.cmd, arglist, verifylist)

            result = self.cmd.take_action(parsed_args)
            self.quotas_mock.update.assert_called_with(
                force=None,
                gigabytes=None,
                share_networks=None,
                share_replicas=2,
                shares=None,
                snapshot_gigabytes=None,
                snapshots=None,
                per_share_gigabytes=None,
                tenant_id=self.project.id,
                user_id=None)
            self.assertIsNone(result)

    def test_quota_set_replica_gigabytes_exception(self):
        self.app.client_manager.share.api_version = api_versions.APIVersion(
            '2.51')
        arglist = [
            self.project.id,
            '--replica-gigabytes', '10',
        ]
        verifylist = [
            ('project', self.project.id),
            ('replica_gigabytes', 10)
        ]

        parsed_args = self.check_parser(self.cmd, arglist, verifylist)
        self.assertRaises(
            exceptions.CommandError, self.cmd.take_action, parsed_args)

    def test_quota_set_per_share_gigabytes(self):
        arglist = [
            self.project.id,
            '--per-share-gigabytes', '10',
        ]
        verifylist = [
            ('project', self.project.id),
            ('per_share_gigabytes', 10)
        ]

        with mock.patch('osc_lib.utils.find_resource') as mock_find_resource:
            mock_find_resource.return_value = self.project

            parsed_args = self.check_parser(self.cmd, arglist, verifylist)

            result = self.cmd.take_action(parsed_args)
            self.quotas_mock.update.assert_called_with(
                force=None,
                gigabytes=None,
                share_networks=None,
                shares=None,
                snapshot_gigabytes=None,
                snapshots=None,
                per_share_gigabytes=10,
                tenant_id=self.project.id,
                user_id=None)
            self.assertIsNone(result)


class TestQuotaShow(TestQuotas):
    project = identity_fakes.FakeProject.create_one_project()
    user = identity_fakes.FakeUser.create_one_user()

    def setUp(self):
        super(TestQuotaShow, self).setUp()

        self.quotas = manila_fakes.FakeQuotaSet.create_fake_quotas()
        self.quotas_mock.get.return_value = self.quotas
        self.cmd = osc_quotas.QuotaShow(self.app, None)

    def test_quota_show(self):
        arglist = [
            self.project.id
        ]
        verifylist = [
            ('project', self.project.id)
        ]

        with mock.patch('osc_lib.utils.find_resource') as mock_find_resource:
            mock_find_resource.return_value = self.project

            parsed_args = self.check_parser(self.cmd, arglist, verifylist)
            columns, data = self.cmd.take_action(parsed_args)

            self.quotas_mock.get.assert_called_with(
                detail=False,
                tenant_id=self.project.id,
                user_id=None
            )

            self.assertCountEqual(columns, self.quotas.keys())
            self.assertCountEqual(data, self.quotas._info.values())

    def test_quota_show_api_version_exception(self):
        self.app.client_manager.share.api_version = api_versions.APIVersion(
            '2.38'
        )

        arglist = [
            self.project.id,
            '--share-type', 'default'
        ]
        verifylist = [
            ('project', self.project.id),
            ('share_type', 'default')
        ]

        parsed_args = self.check_parser(self.cmd, arglist, verifylist)
        self.assertRaises(
            exceptions.CommandError, self.cmd.take_action, parsed_args)

    def test_quota_show_defaults(self):
        arglist = [
            self.project.id,
            '--defaults'
        ]
        verifylist = [
            ('project', self.project.id),
            ('defaults', True)
        ]

        self.quotas_mock.defaults = mock.Mock()
        self.quotas_mock.defaults.return_value = self.quotas

        with mock.patch('osc_lib.utils.find_resource') as mock_find_resource:
            mock_find_resource.return_value = self.project

            parsed_args = self.check_parser(self.cmd, arglist, verifylist)
            columns, data = self.cmd.take_action(parsed_args)

            self.quotas_mock.defaults.assert_called_with(self.project.id)

            self.assertCountEqual(columns, self.quotas.keys())
            self.assertCountEqual(data, self.quotas._info.values())


class TestQuotaDelete(TestQuotas):
    project = identity_fakes.FakeProject.create_one_project()
    user = identity_fakes.FakeUser.create_one_user()

    def setUp(self):
        super(TestQuotaDelete, self).setUp()

        self.quotas = manila_fakes.FakeQuotaSet.create_fake_quotas()
        self.quotas_mock.delete.return_value = None
        self.cmd = osc_quotas.QuotaDelete(self.app, None)

    def test_quota_delete(self):
        arglist = [
            self.project.id
        ]
        verifylist = [
            ('project', self.project.id)
        ]

        with mock.patch('osc_lib.utils.find_resource') as mock_find_resource:
            mock_find_resource.return_value = self.project

            parsed_args = self.check_parser(self.cmd, arglist, verifylist)

            result = self.cmd.take_action(parsed_args)
            self.quotas_mock.delete.assert_called_with(
                tenant_id=self.project.id,
                user_id=None)
            self.assertIsNone(result)

    def test_quota_delete_share_type(self):
        arglist = [
            self.project.id,
            '--share-type', 'default'
        ]
        verifylist = [
            ('project', self.project.id),
            ('share_type', 'default')
        ]

        with mock.patch('osc_lib.utils.find_resource') as mock_find_resource:
            mock_find_resource.return_value = self.project

            parsed_args = self.check_parser(self.cmd, arglist, verifylist)

            result = self.cmd.take_action(parsed_args)
            self.quotas_mock.delete.assert_called_with(
                share_type='default',
                tenant_id=self.project.id,
                user_id=None)
            self.assertIsNone(result)

    def test_quota_delete_api_version_exception(self):
        self.app.client_manager.share.api_version = api_versions.APIVersion(
            '2.38'
        )

        arglist = [
            self.project.id,
            '--share-type', 'default'
        ]
        verifylist = [
            ('project', self.project.id),
            ('share_type', 'default')
        ]

        parsed_args = self.check_parser(self.cmd, arglist, verifylist)
        self.assertRaises(
            exceptions.CommandError, self.cmd.take_action, parsed_args)
