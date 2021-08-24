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
from manilaclient.osc.v2 import share_pools
from manilaclient.tests.unit.osc.v2 import fakes as manila_fakes


class TestPool(manila_fakes.TestShare):

    def setUp(self):
        super(TestPool, self).setUp()

        self.pools_mock = self.app.client_manager.share.pools
        self.pools_mock.reset_mock()

        self.share_types_mock = self.app.client_manager.share.share_types
        self.share_types_mock.reset_mock()

        self.app.client_manager.share.api_version = api_versions.APIVersion(
            api_versions.MAX_VERSION)


class TestPoolList(TestPool):

    columns = ['Name', 'Host', 'Backend', 'Pool']

    def setUp(self):
        super(TestPoolList, self).setUp()

        self.share_type = manila_fakes.FakeShareType.create_one_sharetype()
        self.share_types_mock.get.return_value = self.share_type

        self.share_pools = manila_fakes.FakeSharePools.create_share_pools()
        self.pools_mock.list.return_value = self.share_pools

        self.values = (oscutils.get_dict_properties(
            pool._info, self.columns) for pool in self.share_pools)

        self.cmd = share_pools.ListSharePools(self.app, None)

    def test_list_share_pools(self):
        arglist = []
        verifylist = []

        parsed_args = self.check_parser(self.cmd, arglist, verifylist)
        columns, data = self.cmd.take_action(parsed_args)

        self.pools_mock.list.assert_called_with(
            detailed=False,
            search_opts={
                'host': None,
                'backend': None,
                'pool': None,
                'share_type': None,
            })

        self.assertEqual(self.columns, columns)
        self.assertEqual(list(self.values), list(data))

    def test_list_share_pools_filters(self):
        arglist = [
            '--host', self.share_pools[0].host,
            '--backend', self.share_pools[0].backend,
            '--pool', self.share_pools[0].pool
        ]
        verifylist = [
            ('host', self.share_pools[0].host),
            ('backend', self.share_pools[0].backend),
            ('pool', self.share_pools[0].pool)
        ]

        parsed_args = self.check_parser(self.cmd, arglist, verifylist)
        columns, data = self.cmd.take_action(parsed_args)

        self.pools_mock.list.assert_called_with(
            detailed=False,
            search_opts={
                'host': self.share_pools[0].host,
                'backend': self.share_pools[0].backend,
                'pool': self.share_pools[0].pool,
                'share_type': None,
            })

        self.assertEqual(self.columns, columns)
        self.assertEqual(list(self.values), list(data))

    def test_list_share_pools_share_type(self):
        arglist = [
            '--share-type', self.share_type.id
        ]
        verifylist = [
            ('share_type', self.share_type.id)
        ]
        parsed_args = self.check_parser(self.cmd, arglist, verifylist)
        columns, data = self.cmd.take_action(parsed_args)

        self.pools_mock.list.assert_called_with(
            detailed=False,
            search_opts={
                'host': None,
                'backend': None,
                'pool': None,
                'share_type': self.share_type.id,
            })
        self.assertEqual(self.columns, columns)
        self.assertEqual(list(self.values), list(data))

    def test_list_share_pools_share_type_api_version_exception(self):
        self.app.client_manager.share.api_version = api_versions.APIVersion(
            "2.22")

        arglist = [
            '--share-type', self.share_type.id
        ]
        verifylist = [
            ('share_type', self.share_type.id)
        ]

        parsed_args = self.check_parser(self.cmd, arglist, verifylist)
        self.assertRaises(
            exceptions.CommandError, self.cmd.take_action, parsed_args)

    def test_list_share_pools_detail(self):
        detail_columns = ['Name', 'Host', 'Backend', 'Pool', 'Capabilities']
        detail_values = (oscutils.get_dict_properties(
            pool._info, detail_columns) for pool in self.share_pools)
        arglist = [
            '--detail'
        ]
        verifylist = [
            ('detail', True)
        ]

        parsed_args = self.check_parser(self.cmd, arglist, verifylist)
        columns, data = self.cmd.take_action(parsed_args)

        self.pools_mock.list.assert_called_with(
            detailed=True,
            search_opts={
                'host': None,
                'backend': None,
                'pool': None,
                'share_type': None,
            })

        self.assertEqual(detail_columns, columns)
        self.assertEqual(list(detail_values), list(data))
