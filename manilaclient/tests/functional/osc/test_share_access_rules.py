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
from tempest.lib import exceptions as tempest_exc

from manilaclient.tests.functional.osc import base


@ddt.ddt
class ShareAccessAllowTestCase(base.OSCClientTestBase):

    def test_share_access_allow(self):
        share = self.create_share()
        access_rule = self.create_share_access_rule(
            share=share['name'],
            access_type='ip',
            access_to='0.0.0.0/0',
            wait=True)

        self.assertEqual(access_rule['share_id'], share['id'])
        self.assertEqual(access_rule['state'], 'active')
        self.assertEqual(access_rule['access_type'], 'ip')
        self.assertEqual(access_rule['access_to'], '0.0.0.0/0')

        # default values
        self.assertEqual(access_rule['properties'], '')
        self.assertEqual(access_rule['access_level'], 'rw')

        access_rules = self.listing_result('share',
                                           f'access list {share["id"]}')
        self.assertIn(access_rule['id'],
                      [item['ID'] for item in access_rules])

        # create another access rule with different params
        access_rule = self.create_share_access_rule(
            share=share['name'],
            access_type='ip',
            access_to='12.34.56.78',
            access_level='ro',
            properties='foo=bar')

        self.assertEqual(access_rule['access_type'], 'ip')
        self.assertEqual(access_rule['access_to'], '12.34.56.78')
        self.assertEqual(access_rule['properties'], 'foo : bar')
        self.assertEqual(access_rule['access_level'], 'ro')

    @ddt.data(
        {'lock_visibility': True, 'lock_deletion': True,
         'lock_reason': None},
        {'lock_visibility': False, 'lock_deletion': True,
         'lock_reason': None},
        {'lock_visibility': True, 'lock_deletion': False,
         'lock_reason': 'testing'},
        {'lock_visibility': True, 'lock_deletion': False,
         'lock_reason': 'testing'},
    )
    @ddt.unpack
    def test_share_access_allow_restrict(self, lock_visibility,
                                         lock_deletion, lock_reason):
        share = self.create_share()
        access_rule = self.create_share_access_rule(
            share=share['id'],
            access_type='ip',
            access_to='0.0.0.0/0',
            wait=True,
            lock_visibility=lock_visibility,
            lock_deletion=lock_deletion,
            lock_reason=lock_reason)

        if lock_deletion:
            self.assertRaises(
                tempest_exc.CommandFailed,
                self.openstack,
                'share',
                params=f'access delete {share["id"]} {access_rule["id"]}'
            )
        self.openstack(
            'share',
            params=f'access delete {share["id"]} {access_rule["id"]} '
                   f'--unrestrict --wait')


@ddt.ddt
class ShareAccessDenyTestCase(base.OSCClientTestBase):
    @ddt.data(True, False)
    def test_share_access_deny(self, lock_deletion):
        share = self.create_share()
        access_rule = self.create_share_access_rule(
            share=share['name'],
            access_type='ip',
            access_to='0.0.0.0/0',
            wait=True,
            lock_deletion=lock_deletion)

        access_rules = self.listing_result('share',
                                           f'access list {share["id"]}')
        num_access_rules = len(access_rules)

        delete_params = (
            f'access delete {share["name"]} {access_rule["id"]} --wait')
        if lock_deletion:
            delete_params += ' --unrestrict'
        self.openstack('share', params=delete_params)

        access_rules = self.listing_result('share',
                                           f'access list {share["id"]}')
        self.assertEqual(num_access_rules - 1, len(access_rules))


@ddt.data
class ListShareAccessRulesTestCase(base.OSCClientTestBase):

    @ddt.data("2.45", "2.33", "2.21")
    def test_share_access_list(self, microversion):
        share = self.create_share()
        self.create_share_access_rule(
            share=share['name'],
            access_type='ip',
            access_to='0.0.0.0/0',
            wait=True)

        output = self.openstack(
            'share',
            params=f'access list {share["id"]}',
            flags=f'--os-share-api-version {microversion}')
        access_rule_list = self.parser.listing(output)
        base_list = [
            'ID',
            'Access Type',
            'Access To',
            'Access Level',
            'State']
        if microversion >= '2.33':
            base_list.append('Access Key')

        if microversion >= '2.45':
            base_list.extend(['Created At',
                             'Updated At'])

        self.assertTableStruct(access_rule_list, base_list)
        self.assertTrue(len(access_rule_list) > 0)

        self.create_share_access_rule(
            share=share['name'],
            access_type='ip',
            access_to='192.168.0.151',
            wait=True,
            properties='foo=bar')

        output = self.openstack(
            'share',
            params=f'access list {share["id"]} '
            f'--properties foo=bar',
            flags=f'--os-share-api-version {microversion}')
        access_rule_properties = self.parser.listing(output)

        self.assertEqual(1, len(access_rule_properties))

        self.assertEqual(access_rule_properties['id'],
                         access_rule_properties[0]['ID'])

    def test_share_access_list_with_filters(self):
        share = self.create_share()
        access_to_filter = '20.0.0.0/0'
        self.create_share_access_rule(
            share=share['name'],
            access_type='ip',
            access_to='0.0.0.0/0',
            wait=True)
        self.create_share_access_rule(
            share=share['name'],
            access_type='ip',
            access_to=access_to_filter,
            wait=True)

        output = self.openstack(
            'share',
            params=f'access list {share["id"]} --access-to {access_to_filter}',
            flags='--os-share-api-version 2.82')
        access_rule_list = self.parser.listing(output)

        self.assertTrue(len(access_rule_list) == 1)


class ShowShareAccessRulesTestCase(base.OSCClientTestBase):
    def test_share_access_show(self):
        share = self.create_share()
        access_rule = self.create_share_access_rule(
            share=share['name'],
            access_type='ip',
            access_to='0.0.0.0/0',
            wait=True)

        access_rule_show = self.dict_result(
            'share',
            f'access show {access_rule["id"]}')
        self.assertEqual(access_rule_show['id'], access_rule['id'])
        self.assertEqual(access_rule_show['share_id'], share['id'])
        self.assertEqual(access_rule_show['access_level'], 'rw')
        self.assertEqual(access_rule_show['access_to'], '0.0.0.0/0')
        self.assertEqual(access_rule_show['access_type'], 'ip')
        self.assertEqual(access_rule_show['state'], 'active')
        self.assertEqual(access_rule_show['access_key'], 'None')
        self.assertEqual(access_rule_show['created_at'],
                         access_rule['created_at'])
        self.assertEqual(access_rule_show['properties'], '')
        self.assertIn('updated_at', access_rule_show)


class SetShareAccessTestCase(base.OSCClientTestBase):
    def test_set_share_access_metadata(self):
        share = self.create_share()
        access_rule = self.create_share_access_rule(
            share=share['name'],
            access_type='ip',
            access_to='0.0.0.0/0',
            wait=True)

        self.assertEqual(access_rule['properties'], '')

        self.openstack('share',
                       params=f'access set {access_rule["id"]} '
                       f'--property foo=bar')

        access_rule = self.dict_result(
            'share',
            f'access show {access_rule["id"]}')
        self.assertEqual(access_rule['properties'], 'foo : bar')

    def test_set_share_access_level(self):
        share = self.create_share()
        access_rule = self.create_share_access_rule(
            share=share['name'],
            access_type='ip',
            access_to='0.0.0.0/0',
            wait=True)

        self.assertEqual(access_rule['access_level'], 'rw')

        self.openstack('share',
                       params=f'access set {access_rule["id"]} '
                       f'--access-level ro')
        access_rule = self.dict_result(
            'share',
            f'access show {access_rule["id"]}')
        self.assertEqual(access_rule['access_level'], 'ro')


class UnsetShareAccessRulesTestCase(base.OSCClientTestBase):
    def test_unset_share_access(self):
        share = self.create_share()
        access_rule = self.create_share_access_rule(
            share=share['name'],
            access_type='ip',
            access_to='192.168.0.101',
            wait=True,
            properties='foo=bar')

        self.openstack('share',
                       params=f'access unset '
                              f'--property foo {access_rule["id"]}')

        access_rule_unset = self.dict_result(
            'share',
            f'access show {access_rule["id"]}')
        self.assertEqual(access_rule_unset['properties'], '')
