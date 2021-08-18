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

from unittest import mock

from osc_lib import exceptions
from osc_lib import utils as oscutils

from manilaclient.common import cliutils
from manilaclient.osc import utils
from manilaclient.osc.v2 import share_instances as osc_share_instances

from manilaclient import api_versions
from manilaclient.tests.unit.osc import osc_utils
from manilaclient.tests.unit.osc.v2 import fakes as manila_fakes


class TestShareInstance(manila_fakes.TestShare):

    def setUp(self):
        super(TestShareInstance, self).setUp()

        self.shares_mock = self.app.client_manager.share.shares
        self.shares_mock.reset_mock()

        self.instances_mock = self.app.client_manager.share.share_instances
        self.instances_mock.reset_mock()

        self.share_instance_export_locations_mock = (
            self.app.client_manager.share.share_instance_export_locations)
        self.share_instance_export_locations_mock.reset_mock()

        self.app.client_manager.share.api_version = api_versions.APIVersion(
            api_versions.MAX_VERSION)


class TestShareInstanceList(TestShareInstance):
    columns = [
        'id',
        'share_id',
        'host',
        'status',
        'availability_zone',
        'share_network_id',
        'share_server_id',
        'share_type_id',
    ]
    column_headers = utils.format_column_headers(columns)

    def setUp(self):
        super(TestShareInstanceList, self).setUp()

        self.instances_list = (
            manila_fakes.FakeShareInstance.create_share_instances(count=2))
        self.instances_mock.list.return_value = self.instances_list

        self.share = manila_fakes.FakeShare.create_one_share()
        self.shares_mock.get.return_value = self.share

        self.shares_mock.list_instances.return_value = self.instances_list
        self.shares_mock.list_instances.return_value = self.instances_list

        self.instance_values = (oscutils.get_dict_properties(
            instance._info, self.columns) for instance in self.instances_list)

        self.cmd = osc_share_instances.ShareInstanceList(self.app, None)

    def test_share_instance_list(self):
        argslist = []
        verifylist = []

        parsed_args = self.check_parser(self.cmd, argslist, verifylist)

        columns, data = self.cmd.take_action(parsed_args)

        self.assertIs(True, self.instances_mock.list.called)

        self.assertEqual(self.column_headers, columns)
        self.assertEqual(list(self.instance_values), list(data))

    def test_share_instance_list_by_share(self):
        argslist = [
            '--share', self.share['id']
        ]
        verifylist = [
            ('share', self.share.id)
        ]

        parsed_args = self.check_parser(self.cmd, argslist, verifylist)

        columns, data = self.cmd.take_action(parsed_args)

        self.shares_mock.list_instances.assert_called_with(self.share)

        self.assertEqual(self.column_headers, columns)
        self.assertEqual(list(self.instance_values), list(data))

    def test_share_instance_list_by_export_location(self):
        fake_export_location = '10.1.1.0:/fake_share_el'
        argslist = [
            '--export-location', fake_export_location
        ]
        verifylist = [
            ('export_location', fake_export_location)
        ]

        parsed_args = self.check_parser(self.cmd, argslist, verifylist)

        columns, data = self.cmd.take_action(parsed_args)

        self.instances_mock.list.assert_called_with(
            export_location=fake_export_location)

        self.assertEqual(self.column_headers, columns)
        self.assertEqual(list(self.instance_values), list(data))

    def test_share_instance_list_by_export_location_invalid_version(self):
        fake_export_location = '10.1.1.0:/fake_share_el'
        argslist = [
            '--export-location', fake_export_location
        ]
        verifylist = [
            ('export_location', fake_export_location)
        ]
        self.app.client_manager.share.api_version = api_versions.APIVersion(
            '2.34')

        parsed_args = self.check_parser(self.cmd, argslist, verifylist)

        self.assertRaises(
            exceptions.CommandError,
            self.cmd.take_action,
            parsed_args)


class TestShareInstanceDelete(TestShareInstance):

    def setUp(self):
        super(TestShareInstanceDelete, self).setUp()
        self.share_instance = (
            manila_fakes.FakeShareInstance.create_one_share_instance())
        self.instances_mock.get.return_value = self.share_instance

        self.cmd = osc_share_instances.ShareInstanceDelete(self.app, None)

    def test_share_instance_delete_missing_args(self):
        arglist = []
        verifylist = []

        self.assertRaises(osc_utils.ParserException,
                          self.check_parser, self.cmd, arglist, verifylist)

    def test_share_instance_delete(self):
        arglist = [
            self.share_instance.id
        ]
        verifylist = [
            ('instance', [self.share_instance.id])
        ]

        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        result = self.cmd.take_action(parsed_args)

        self.instances_mock.force_delete.assert_called_with(
            self.share_instance)
        self.assertIsNone(result)

    def test_share_instance_delete_multiple(self):
        share_instances = (
            manila_fakes.FakeShareInstance.create_share_instances(count=2))
        instance_ids = [instance.id for instance in share_instances]
        arglist = instance_ids
        verifylist = [('instance', instance_ids)]
        self.instances_mock.get.side_effect = share_instances

        delete_calls = [
            mock.call(instance) for instance in share_instances]

        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        result = self.cmd.take_action(parsed_args)

        self.instances_mock.force_delete.assert_has_calls(delete_calls)
        self.assertEqual(self.instances_mock.force_delete.call_count,
                         len(share_instances))
        self.assertIsNone(result)

    def test_share_instance_delete_exception(self):
        arglist = [
            self.share_instance.id
        ]
        verifylist = [
            ('instance', [self.share_instance.id])
        ]

        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        self.instances_mock.force_delete.side_effect = (
            exceptions.CommandError())
        self.assertRaises(exceptions.CommandError,
                          self.cmd.take_action,
                          parsed_args)

    def test_share_instance_delete_wait(self):
        arglist = [
            self.share_instance.id,
            '--wait'
        ]
        verifylist = [
            ('instance', [self.share_instance.id]),
            ('wait', True)
        ]

        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        with mock.patch('osc_lib.utils.wait_for_delete', return_value=True):
            result = self.cmd.take_action(parsed_args)

            self.instances_mock.force_delete.assert_called_with(
                self.share_instance)
            self.instances_mock.get.assert_called_with(self.share_instance.id)
            self.assertIsNone(result)

    def test_share_instance_delete_wait_exception(self):
        arglist = [
            self.share_instance.id,
            '--wait'
        ]
        verifylist = [
            ('instance', [self.share_instance.id]),
            ('wait', True)
        ]

        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        with mock.patch('osc_lib.utils.wait_for_delete', return_value=False):
            self.assertRaises(
                exceptions.CommandError,
                self.cmd.take_action,
                parsed_args
            )


class TestShareInstanceShow(TestShareInstance):

    def setUp(self):
        super(TestShareInstanceShow, self).setUp()

        self.share_instance = (
            manila_fakes.FakeShareInstance.create_one_share_instance()
        )
        self.instances_mock.get.return_value = self.share_instance

        self.export_locations = (
            [manila_fakes.FakeShareExportLocation.create_one_export_location()
             for i in range(2)])

        self.share_instance_export_locations_mock.list.return_value = (
            self.export_locations)

        self.cmd = osc_share_instances.ShareInstanceShow(self.app, None)

        self.data = tuple(self.share_instance._info.values())
        self.columns = tuple(self.share_instance._info.keys())

    def test_share_instance_show_missing_args(self):
        arglist = []
        verifylist = []

        self.assertRaises(
            osc_utils.ParserException,
            self.check_parser, self.cmd, arglist, verifylist)

    def test_share_instance_show(self):
        expected_columns = tuple(self.share_instance._info.keys())

        expected_data_dic = tuple()

        for column in expected_columns:
            expected_data_dic += (self.share_instance._info[column],)

        expected_columns += ('export_locations',)
        expected_data_dic += (dict(self.export_locations[0]),)

        cliutils.convert_dict_list_to_string = mock.Mock()
        cliutils.convert_dict_list_to_string.return_value = dict(
            self.export_locations[0])

        arglist = [
            self.share_instance.id
        ]
        verifylist = [
            ('instance', self.share_instance.id)
        ]

        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        columns, data = self.cmd.take_action(parsed_args)

        self.instances_mock.get.assert_called_with(
            self.share_instance.id
        )

        self.assertCountEqual(expected_columns, columns)
        self.assertCountEqual(expected_data_dic, data)


class TestShareInstanceSet(TestShareInstance):

    def setUp(self):
        super(TestShareInstanceSet, self).setUp()

        self.share_instance = (
            manila_fakes.FakeShareInstance.create_one_share_instance())

        self.instances_mock.get.return_value = self.share_instance

        self.cmd = osc_share_instances.ShareInstanceSet(self.app, None)

    def test_share_instance_set_status(self):
        new_status = 'available'
        arglist = [
            self.share_instance.id,
            '--status', new_status
        ]
        verifylist = [
            ('instance', self.share_instance.id),
            ('status', new_status)
        ]
        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        result = self.cmd.take_action(parsed_args)

        self.instances_mock.reset_state.assert_called_with(
            self.share_instance,
            new_status)
        self.assertIsNone(result)

    def test_share_instance_set_status_exception(self):
        new_status = 'available'
        arglist = [
            self.share_instance.id,
            '--status', new_status
        ]
        verifylist = [
            ('instance', self.share_instance.id),
            ('status', new_status)
        ]
        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        self.instances_mock.reset_state.side_effect = Exception()

        self.assertRaises(
            exceptions.CommandError,
            self.cmd.take_action,
            parsed_args)

    def test_share_instance_set_nothing_defined(self):
        arglist = [
            self.share_instance.id,
        ]
        verifylist = [
            ('instance', self.share_instance.id),
        ]
        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        self.assertRaises(
            exceptions.CommandError,
            self.cmd.take_action,
            parsed_args)
