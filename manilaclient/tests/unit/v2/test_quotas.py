# Copyright 2013 OpenStack LLC.
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
import mock

from manilaclient import api_versions
from manilaclient.tests.unit import utils
from manilaclient.v2 import quotas


@ddt.ddt
class QuotaSetsTest(utils.TestCase):

    def _get_manager(self, microversion):
        version = api_versions.APIVersion(microversion)
        mock_microversion = mock.Mock(api_version=version)
        return quotas.QuotaSetManager(api=mock_microversion)

    def _get_resource_path(self, microversion):
        if (api_versions.APIVersion(microversion) >
                api_versions.APIVersion("2.6")):
            return quotas.RESOURCE_PATH
        return quotas.RESOURCE_PATH_LEGACY

    @ddt.data("2.6", "2.7")
    def test_tenant_quotas_get(self, microversion):
        tenant_id = 'test'
        manager = self._get_manager(microversion)
        resource_path = self._get_resource_path(microversion)
        expected_url = "%s/test" % resource_path
        with mock.patch.object(manager, '_get',
                               mock.Mock(return_value='fake_get')):
            manager.get(tenant_id)

            manager._get.assert_called_once_with(expected_url, "quota_set")

    @ddt.data("2.6", "2.7")
    def test_user_quotas_get(self, microversion):
        tenant_id = 'test'
        user_id = 'fake_user'
        manager = self._get_manager(microversion)
        resource_path = self._get_resource_path(microversion)
        expected_url = "%s/test?user_id=fake_user" % resource_path
        with mock.patch.object(manager, '_get',
                               mock.Mock(return_value='fake_get')):
            manager.get(tenant_id, user_id=user_id)

            manager._get.assert_called_once_with(expected_url, "quota_set")

    @ddt.data("2.6", "2.7")
    def test_tenant_quotas_defaults(self, microversion):
        tenant_id = 'test'
        manager = self._get_manager(microversion)
        resource_path = self._get_resource_path(microversion)
        expected_url = "%s/test/defaults" % resource_path
        with mock.patch.object(manager, '_get',
                               mock.Mock(return_value='fake_get')):
            manager.defaults(tenant_id)

            manager._get.assert_called_once_with(expected_url, "quota_set")

    @ddt.data(
        ("2.6", {}),
        ("2.6", {"force": True}),
        ("2.7", {}),
        ("2.7", {"force": True}),
    )
    @ddt.unpack
    def test_update_quota(self, microversion, extra_data):
        tenant_id = 'test'
        manager = self._get_manager(microversion)
        resource_path = self._get_resource_path(microversion)
        expected_url = "%s/test" % resource_path
        expected_body = {
            'quota_set': {
                'tenant_id': tenant_id,
                'shares': 1,
                'snapshots': 2,
                'gigabytes': 3,
                'snapshot_gigabytes': 4,
                'share_networks': 5,
            },
        }
        expected_body['quota_set'].update(extra_data)
        with mock.patch.object(manager, '_update',
                               mock.Mock(return_value='fake_update')):
            manager.update(
                tenant_id, shares=1, snapshots=2, gigabytes=3,
                snapshot_gigabytes=4, share_networks=5, **extra_data)

            manager._update.assert_called_once_with(
                expected_url, expected_body, "quota_set")

    @ddt.data("2.6", "2.7")
    def test_update_user_quota(self, microversion):
        tenant_id = 'test'
        user_id = 'fake_user'
        manager = self._get_manager(microversion)
        resource_path = self._get_resource_path(microversion)
        expected_url = "%s/test?user_id=fake_user" % resource_path
        expected_body = {
            'quota_set': {
                'tenant_id': tenant_id,
                'shares': 1,
                'snapshots': 2,
                'gigabytes': 3,
                'snapshot_gigabytes': 4,
                'share_networks': 5,
            },
        }
        with mock.patch.object(manager, '_update',
                               mock.Mock(return_value='fake_update')):
            manager.update(
                tenant_id, shares=1, snapshots=2, gigabytes=3,
                snapshot_gigabytes=4, share_networks=5, user_id=user_id)

            manager._update.assert_called_once_with(
                expected_url, expected_body, "quota_set")

    @ddt.data("2.6", "2.7")
    def test_quotas_delete(self, microversion):
        tenant_id = 'test'
        manager = self._get_manager(microversion)
        resource_path = self._get_resource_path(microversion)
        expected_url = "%s/test" % resource_path
        with mock.patch.object(manager, '_delete',
                               mock.Mock(return_value='fake_delete')):
            manager.delete(tenant_id)

            manager._delete.assert_called_once_with(expected_url)

    @ddt.data("2.6", "2.7")
    def test_user_quotas_delete(self, microversion):
        tenant_id = 'test'
        user_id = 'fake_user'
        manager = self._get_manager(microversion)
        resource_path = self._get_resource_path(microversion)
        expected_url = "%s/test?user_id=fake_user" % resource_path
        with mock.patch.object(manager, '_delete',
                               mock.Mock(return_value='fake_delete')):
            manager.delete(tenant_id, user_id=user_id)

            manager._delete.assert_called_once_with(expected_url)
