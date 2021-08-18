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

from manilaclient.osc import utils
from manilaclient.osc.v2 import services as osc_services
from manilaclient.tests.unit.osc.v2 import fakes as manila_fakes


class TestShareService(manila_fakes.TestShare):

    def setUp(self):
        super(TestShareService, self).setUp()

        self.services_mock = self.app.client_manager.share.services
        self.services_mock.reset_mock()


class TestShareServiceSet(TestShareService):

    def setUp(self):
        super(TestShareServiceSet, self).setUp()

        self.share_service = (
            manila_fakes.FakeShareService.create_fake_service()
        )
        self.cmd = osc_services.SetShareService(self.app, None)

    def test_share_service_set_enable(self):
        arglist = [
            self.share_service.host,
            self.share_service.binary,
            '--enable'
        ]
        verifylist = [
            ('host', self.share_service.host),
            ('binary', self.share_service.binary),
            ('enable', True)
        ]
        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        result = self.cmd.take_action(parsed_args)

        self.services_mock.enable.assert_called_with(
            self.share_service.host,
            self.share_service.binary)
        self.assertIsNone(result)

    def test_share_service_set_enable_exception(self):
        arglist = [
            self.share_service.host,
            self.share_service.binary,
            '--enable'
        ]
        verifylist = [
            ('host', self.share_service.host),
            ('binary', self.share_service.binary),
            ('enable', True)
        ]
        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        self.services_mock.enable.side_effect = Exception()
        self.assertRaises(
            exceptions.CommandError,
            self.cmd.take_action,
            parsed_args)

    def test_share_service_set_disable(self):
        arglist = [
            self.share_service.host,
            self.share_service.binary,
            '--disable'
        ]
        verifylist = [
            ('host', self.share_service.host),
            ('binary', self.share_service.binary),
            ('disable', True)
        ]
        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        result = self.cmd.take_action(parsed_args)

        self.services_mock.disable.assert_called_with(
            self.share_service.host,
            self.share_service.binary)
        self.assertIsNone(result)

    def test_share_service_set_disable_exception(self):
        arglist = [
            self.share_service.host,
            self.share_service.binary,
            '--disable'
        ]
        verifylist = [
            ('host', self.share_service.host),
            ('binary', self.share_service.binary),
            ('disable', True)
        ]
        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        self.services_mock.disable.side_effect = Exception()
        self.assertRaises(
            exceptions.CommandError,
            self.cmd.take_action,
            parsed_args)


class TestShareServiceList(TestShareService):

    columns = [
        'id',
        'binary',
        'host',
        'zone',
        'status',
        'state',
        'updated_at'
    ]

    column_headers = utils.format_column_headers(columns)

    def setUp(self):
        super(TestShareServiceList, self).setUp()

        self.services_list = (
            manila_fakes.FakeShareService.create_fake_services()
        )
        self.services_mock.list.return_value = self.services_list
        self.values = (oscutils.get_dict_properties(
            i._info, self.columns) for i in self.services_list)

        self.cmd = osc_services.ListShareService(self.app, None)

    def test_share_service_list(self):
        arglist = []
        verifylist = []
        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        columns, data = self.cmd.take_action(parsed_args)

        self.services_mock.list.assert_called_with(
            search_opts={
                'host': None,
                'binary': None,
                'status': None,
                'state': None,
                'zone': None
            })
        self.assertEqual(self.column_headers, columns)
        self.assertEqual(list(self.values), list(data))

    def test_share_service_list_host_status(self):
        arglist = [
            '--host', self.services_list[0].host,
            '--status', self.services_list[1].status
        ]
        verifylist = [
            ('host', self.services_list[0].host),
            ('status', self.services_list[1].status)
        ]
        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        columns, data = self.cmd.take_action(parsed_args)

        self.services_mock.list.assert_called_with(
            search_opts={
                'host': self.services_list[0].host,
                'binary': None,
                'status': self.services_list[1].status,
                'state': None,
                'zone': None
            })
        self.assertEqual(self.column_headers, columns)
        self.assertEqual(list(self.values), list(data))

    def test_share_service_list_binary_state_zone(self):
        arglist = [
            '--binary', self.services_list[0].binary,
            '--state', self.services_list[1].state,
            '--zone', self.services_list[1].zone
        ]
        verifylist = [
            ('binary', self.services_list[0].binary),
            ('state', self.services_list[1].state),
            ('zone', self.services_list[1].zone)
        ]
        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        columns, data = self.cmd.take_action(parsed_args)

        self.services_mock.list.assert_called_with(
            search_opts={
                'host': None,
                'binary': self.services_list[0].binary,
                'status': None,
                'state': self.services_list[1].state,
                'zone': self.services_list[1].zone
            })
        self.assertEqual(self.column_headers, columns)
        self.assertEqual(list(self.values), list(data))
