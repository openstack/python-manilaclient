#  Copyright (c) 2025 Cloudification GmbH.
#
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

from unittest import mock

from osc_lib import exceptions
from osc_lib import utils as oscutils

from manilaclient import api_versions
from manilaclient.common.apiclient.exceptions import BadRequest
from manilaclient.common.apiclient.exceptions import NotFound
from manilaclient.osc import utils
from manilaclient.osc.v2 import qos_types as osc_qos_types
from manilaclient.tests.unit.osc import osc_utils
from manilaclient.tests.unit.osc.v2 import fakes as manila_fakes

COLUMNS = [
    'id',
    'name',
    'description',
    'specs',
    'created_at',
    'updated_at',
]


class TestQosType(manila_fakes.TestShare):
    def setUp(self):
        super().setUp()

        self.qos_types_mock = self.app.client_manager.share.qos_types
        self.qos_types_mock.reset_mock()
        self.app.client_manager.share.api_version = api_versions.APIVersion(
            api_versions.MAX_VERSION
        )


class TestQosTypeCreate(TestQosType):
    def setUp(self):
        super().setUp()

        self.new_qos_type = manila_fakes.FakeQosType.create_one_qostype()
        self.qos_types_mock.create.return_value = self.new_qos_type

        # Get the command object to test
        self.cmd = osc_qos_types.CreateQosType(self.app, None)

        self.data = [
            self.new_qos_type.id,
            self.new_qos_type.name,
            self.new_qos_type.description,
            ('expected_iops : 2000\npeak_iops : 5000'),
            self.new_qos_type.created_at,
            self.new_qos_type.updated_at,
        ]

        self.raw_data = [
            self.new_qos_type.id,
            self.new_qos_type.name,
            self.new_qos_type.description,
            {
                'expected_iops': '2000',
                'peak_iops': '5000',
            },
            self.new_qos_type.created_at,
            self.new_qos_type.updated_at,
        ]

    def test_qos_type_create_required_args(self):
        """Verifies required arguments."""

        arglist = [self.new_qos_type.name]
        verifylist = [
            ('name', self.new_qos_type.name),
        ]

        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        columns, data = self.cmd.take_action(parsed_args)

        self.qos_types_mock.create.assert_called_with(
            name=self.new_qos_type.name,
        )

        self.assertCountEqual(COLUMNS, columns)
        self.assertCountEqual(self.data, data)

    def test_qos_type_create_json_format(self):
        """Verifies --format json."""

        arglist = [self.new_qos_type.name, '-f', 'json']
        verifylist = [
            ('name', self.new_qos_type.name),
        ]

        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        columns, data = self.cmd.take_action(parsed_args)

        self.qos_types_mock.create.assert_called_with(
            name=self.new_qos_type.name,
        )

        self.assertCountEqual(COLUMNS, columns)
        self.assertCountEqual(self.raw_data, data)

    def test_qos_type_create_missing_required_arg(self):
        """Verifies missing required arguments."""

        arglist = []
        verifylist = []

        self.assertRaises(
            osc_utils.ParserException,
            self.check_parser,
            self.cmd,
            arglist,
            verifylist,
        )

    def test_qos_type_create_specs(self):
        arglist = [
            self.new_qos_type.name,
            '--spec',
            'peak_iops=100',
            '--spec',
            'expected_iops=20',
        ]
        verifylist = [
            ('name', self.new_qos_type.name),
            ('spec', ['peak_iops=100', 'expected_iops=20']),
        ]

        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        columns, data = self.cmd.take_action(parsed_args)

        self.qos_types_mock.create.assert_called_with(
            name=self.new_qos_type.name,
            specs={'peak_iops': '100', 'expected_iops': '20'},
        )

        self.assertCountEqual(COLUMNS, columns)
        self.assertCountEqual(self.data, data)


class TestQosTypeDelete(TestQosType):
    qos_types = manila_fakes.FakeQosType.create_qos_types(count=2)

    def setUp(self):
        super().setUp()

        self.qos_types_mock.get = manila_fakes.FakeQosType.get_qos_types(
            self.qos_types
        )
        self.qos_types_mock.delete.return_value = None

        # Get the command object to test
        self.cmd = osc_qos_types.DeleteQosType(self.app, None)

    def test_qos_type_delete_one(self):
        arglist = [self.qos_types[0].id]

        verifylist = [('qos_types', [self.qos_types[0].id])]

        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        result = self.cmd.take_action(parsed_args)
        self.qos_types_mock.delete.assert_called_with(self.qos_types[0])
        self.assertIsNone(result)

    def test_qos_type_delete_multiple(self):
        arglist = []
        for t in self.qos_types:
            arglist.append(t.id)
        verifylist = [
            ('qos_types', arglist),
        ]

        parsed_args = self.check_parser(self.cmd, arglist, verifylist)
        result = self.cmd.take_action(parsed_args)

        calls = []
        for t in self.qos_types:
            calls.append(mock.call(t))
        self.qos_types_mock.delete.assert_has_calls(calls)
        self.assertIsNone(result)

    def test_delete_qos_type_with_exception(self):
        arglist = [
            'non_existing_type',
        ]
        verifylist = [
            ('qos_types', arglist),
        ]

        parsed_args = self.check_parser(self.cmd, arglist, verifylist)
        self.qos_types_mock.delete.side_effect = exceptions.CommandError()
        self.assertRaises(
            exceptions.CommandError, self.cmd.take_action, parsed_args
        )


class TestQosTypeSet(TestQosType):
    def setUp(self):
        super().setUp()

        self.qos_type = manila_fakes.FakeQosType.create_one_qostype(
            methods={'set_keys': None, 'update': None}
        )
        self.qos_types_mock.get.return_value = self.qos_type

        # Get the command object to test
        self.cmd = osc_qos_types.SetQosType(self.app, None)

    def test_qos_type_set_specs(self):
        arglist = [
            self.qos_type.id,
            '--spec',
            'peak_iops=100',
        ]
        verifylist = [
            ('qos_type', self.qos_type.id),
            ('spec', ['peak_iops=100']),
        ]
        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        result = self.cmd.take_action(parsed_args)
        self.qos_type.set_keys.assert_called_with({'peak_iops': '100'})
        self.assertIsNone(result)

    def test_qos_type_set_description(self):
        arglist = [self.qos_type.id, '--description', 'new description']
        verifylist = [
            ('qos_type', self.qos_type.id),
            ('description', 'new description'),
        ]
        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        result = self.cmd.take_action(parsed_args)
        self.qos_type.update.assert_called_with(description='new description')
        self.assertIsNone(result)

    def test_qos_type_set_specs_exception(self):
        arglist = [
            self.qos_type.id,
            '--spec',
            'peak_iops=100',
        ]
        verifylist = [
            ('qos_type', self.qos_type.id),
            ('spec', ['peak_iops=100']),
        ]
        parsed_args = self.check_parser(self.cmd, arglist, verifylist)
        self.qos_type.set_keys.side_effect = BadRequest()
        self.assertRaises(
            exceptions.CommandError, self.cmd.take_action, parsed_args
        )


class TestQosTypeUnset(TestQosType):
    def setUp(self):
        super().setUp()

        self.qos_type = manila_fakes.FakeQosType.create_one_qostype(
            methods={'unset_keys': None, 'update': None}
        )

        self.qos_types_mock.get.return_value = self.qos_type

        # Get the command object to test
        self.cmd = osc_qos_types.UnsetQosType(self.app, None)

    def test_qos_type_unset_description(self):
        arglist = [self.qos_type.id, '--description']
        verifylist = [
            ('qos_type', self.qos_type.id),
            ('description', True),
        ]
        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        result = self.cmd.take_action(parsed_args)
        self.qos_type.update.assert_called_with(description=None)
        self.assertIsNone(result)

    def test_qos_type_unset_specs(self):
        arglist = [self.qos_type.id, '--spec', 'peak_iops']
        verifylist = [
            ('qos_type', self.qos_type.id),
            ('spec', ['peak_iops']),
        ]
        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        result = self.cmd.take_action(parsed_args)
        self.qos_type.unset_keys.assert_called_with(['peak_iops'])
        self.assertIsNone(result)

    def test_qos_type_unset_exception(self):
        arglist = [self.qos_type.id, '--spec', 'peak_iops']
        verifylist = [
            ('qos_type', self.qos_type.id),
            ('spec', ['peak_iops']),
        ]
        parsed_args = self.check_parser(self.cmd, arglist, verifylist)
        self.qos_type.unset_keys.side_effect = NotFound()
        self.assertRaises(
            exceptions.CommandError, self.cmd.take_action, parsed_args
        )


class TestQosTypeList(TestQosType):
    qos_types = manila_fakes.FakeQosType.create_qos_types()
    columns = utils.format_column_headers(COLUMNS)

    def setUp(self):
        super().setUp()

        self.qos_types_mock.list.return_value = self.qos_types

        # Get the command object to test
        self.cmd = osc_qos_types.ListQosType(self.app, None)

        self.values = (
            oscutils.get_dict_properties(s._info, COLUMNS)
            for s in self.qos_types
        )

    def test_qos_type_list(self):
        arglist = []
        verifylist = []

        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        columns, data = self.cmd.take_action(parsed_args)
        self.qos_types_mock.list.assert_called_once_with(
            search_opts={
                'offset': None,
                'limit': None,
                'name': None,
                'description': None,
                'name~': None,
                'description~': None,
            },
            sort_key=None,
            sort_dir=None,
        )
        self.assertEqual(self.columns, columns)
        self.assertEqual(list(self.values), list(data))

    def test_qos_type_list_by_name(self):
        arglist = ['--name', 'fake_name']
        verifylist = [('name', 'fake_name')]

        parsed_args = self.check_parser(self.cmd, arglist, verifylist)
        columns, data = self.cmd.take_action(parsed_args)
        self.qos_types_mock.list.assert_called_with(
            search_opts={
                'offset': None,
                'limit': None,
                'name': 'fake_name',
                'description': None,
                'name~': None,
                'description~': None,
            },
            sort_key=None,
            sort_dir=None,
        )
        self.assertEqual(self.columns, columns)
        self.assertEqual(list(self.values), list(data))


class TestQosTypeShow(TestQosType):
    def setUp(self):
        super().setUp()

        self.qos_type = manila_fakes.FakeQosType.create_one_qostype()

        self.qos_types_mock.get.return_value = self.qos_type

        # Get the command object to test
        self.cmd = osc_qos_types.ShowQosType(self.app, None)

        self.data = [
            self.qos_type.id,
            self.qos_type.name,
            self.qos_type.description,
            ('expected_iops : 2000\npeak_iops : 5000'),
            self.qos_type.created_at,
            self.qos_type.updated_at,
        ]

        self.raw_data = [
            self.qos_type.id,
            self.qos_type.name,
            self.qos_type.description,
            {
                'expected_iops': '2000',
                'peak_iops': '5000',
            },
            self.qos_type.created_at,
            self.qos_type.updated_at,
        ]

    def test_qos_type_show(self):
        arglist = [self.qos_type.id]
        verifylist = [("qos_type", self.qos_type.id)]
        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        columns, data = self.cmd.take_action(parsed_args)
        self.qos_types_mock.get.assert_called_with(self.qos_type.id)

        self.assertCountEqual(COLUMNS, columns)
        self.assertCountEqual(self.data, data)

    def test_qos_type_show_json_format(self):
        arglist = [
            self.qos_type.id,
            '-f',
            'json',
        ]
        verifylist = [("qos_type", self.qos_type.id)]
        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        columns, data = self.cmd.take_action(parsed_args)
        self.qos_types_mock.get.assert_called_with(self.qos_type.id)

        self.assertCountEqual(COLUMNS, columns)
        self.assertCountEqual(self.raw_data, data)
