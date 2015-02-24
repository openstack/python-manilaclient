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

from manilaclient.tests.unit import utils
from manilaclient.tests.unit.v1 import fakes


cs = fakes.FakeClient()


class QuotaSetsTest(utils.TestCase):

    def test_tenant_quotas_get(self):
        tenant_id = 'test'
        cs.quotas.get(tenant_id)
        cs.assert_called('GET', '/os-quota-sets/%s' % tenant_id)

    def test_user_quotas_get(self):
        tenant_id = 'test'
        user_id = 'fake_user'
        cs.quotas.get(tenant_id, user_id=user_id)
        url = '/os-quota-sets/%s?user_id=%s' % (tenant_id, user_id)
        cs.assert_called('GET', url)

    def test_tenant_quotas_defaults(self):
        tenant_id = 'test'
        cs.quotas.defaults(tenant_id)
        cs.assert_called('GET', '/os-quota-sets/%s/defaults' % tenant_id)

    def test_update_quota(self):
        q = cs.quotas.get('test')
        q.update(shares=1)
        q.update(snapshots=2)
        q.update(gigabytes=3)
        q.update(snapshot_gigabytes=4)
        q.update(share_networks=5)
        cs.assert_called('PUT', '/os-quota-sets/test')

    def test_update_user_quota(self):
        tenant_id = 'test'
        user_id = 'fake_user'
        q = cs.quotas.get(tenant_id)
        q.update(shares=1, user_id=user_id)
        q.update(snapshots=2, user_id=user_id)
        q.update(gigabytes=3, user_id=user_id)
        q.update(snapshot_gigabytes=4, user_id=user_id)
        q.update(share_networks=5, user_id=user_id)
        url = '/os-quota-sets/%s?user_id=%s' % (tenant_id, user_id)
        cs.assert_called('PUT', url)

    def test_force_update_quota(self):
        q = cs.quotas.get('test')
        q.update(shares=2, force=True)
        cs.assert_called(
            'PUT', '/os-quota-sets/test',
            {'quota_set': {'force': True,
                           'shares': 2,
                           'tenant_id': 'test'}})

    def test_quotas_delete(self):
        tenant_id = 'test'
        cs.quotas.delete(tenant_id)
        cs.assert_called('DELETE', '/os-quota-sets/%s' % tenant_id)

    def test_user_quotas_delete(self):
        tenant_id = 'test'
        user_id = 'fake_user'
        cs.quotas.delete(tenant_id, user_id=user_id)
        url = '/os-quota-sets/%s?user_id=%s' % (tenant_id, user_id)
        cs.assert_called('DELETE', url)

    def test_refresh_quota(self):
        q = cs.quotas.get('test')
        q2 = cs.quotas.get('test')
        self.assertEqual(q.shares, q2.shares)
        self.assertEqual(q.snapshots, q2.snapshots)
        q2.shares = 0
        self.assertNotEqual(q.shares, q2.shares)
        q2.snapshots = 0
        self.assertNotEqual(q.snapshots, q2.snapshots)
        q2.get()
        self.assertEqual(q.shares, q2.shares)
        self.assertEqual(q.snapshots, q2.snapshots)
